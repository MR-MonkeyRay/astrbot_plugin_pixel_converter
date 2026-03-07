"""
AstrBot Pixel Converter Plugin
Convert images to pixel art style with classic palettes and FX effects.
"""

import asyncio
import io
import os
import random
import shutil
import tempfile
import urllib.request
from uuid import uuid4

from PIL import Image

from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import astrbot.api.message_components as Comp
from astrbot.core.utils.session_waiter import session_waiter, SessionController

from core.palettes import (
    list_palettes,
    is_valid_palette,
    normalize_palette_name,
)
from core.pixelate import pixelate
from core.fx import (
    apply_fx,
    normalize_fx_names,
    ALL_FX,
)
from core.gif import save_gif


# QQ Avatar URL template
AVATAR_URL_TEMPLATE = "https://q1.qlogo.cn/g?b=qq&nk={qq}&s=640"


@register("astrbot_plugin_pixel_converter", "monkeyray", "将图片转换为像素风格", "0.1.0")
class PixelConverterPlugin(Star):
    """AstrBot plugin for converting images to pixel art style."""

    def __init__(self, context: Context) -> None:
        super().__init__(context)
        # Config defaults
        self.default_size: int = 3
        self.default_palette: str = ""
        self.default_fx: str = ""
        self.max_image_size: int = 2048
        self.gif_frames: int = 8
        self.gif_duration: int = 100
        # Temporary directory for output files
        self._temp_dir: str = ""

    async def initialize(self) -> None:
        """Load plugin configuration."""
        config = self.context.get_config()
        self.default_size = config.get("default_size", 3)
        self.default_palette = config.get("default_palette", "")
        self.default_fx = config.get("default_fx", "")
        self.max_image_size = config.get("max_image_size", 2048)
        self.gif_frames = config.get("gif_frames", 8)
        self.gif_duration = config.get("gif_duration", 100)
        # Create temp directory
        self._temp_dir = tempfile.mkdtemp(prefix="pixel_converter_")
        logger.info(f"Pixel Converter plugin initialized. Temp dir: {self._temp_dir}")

    async def terminate(self) -> None:
        """Plugin termination handler."""
        if self._temp_dir and os.path.exists(self._temp_dir):
            try:
                shutil.rmtree(self._temp_dir)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp directory: {e}")
            self._temp_dir = ""
        logger.info("Pixel Converter plugin terminated.")

    @filter.command("像素画", alias=["pixel", "px"])
    async def pixel_command(self, event: AstrMessageEvent):
        """Convert image to pixel art style."""
        try:
            # Parse command options
            options = self._parse_options(event)
            # Try to extract image source
            image_url = self._extract_image_url(event, options.get("at_qq"))
            if image_url:
                # Direct processing
                yield event.plain_result("🎨 正在像素化处理中...")
                result_path, is_animated, palette_name, fx_list, size = await self._process(
                    image_url, options
                )
                yield event.image_result(result_path)
                fx_str = "+".join(fx_list) if fx_list else "无"
                yield event.plain_result(
                    f"✨ 像素化完成！SIZE={size} | 调色板={palette_name} | FX={fx_str}"
                )
                # Schedule cleanup
                asyncio.create_task(self._cleanup(result_path))
            else:
                # No image found, enter wait mode
                yield event.plain_result("📸 请发送一张图片，我来像素化~ (60秒超时)")

                @session_waiter(timeout=60, record_history_chains=False)
                async def wait_for_image(controller: SessionController, ev: AstrMessageEvent):
                    """Wait for user to send an image."""
                    # Check for image in message
                    url = self._extract_image_url_from_chain(ev)
                    if url:
                        # Found image
                        await ev.send(ev.plain_result("🎨 正在像素化处理中..."))
                        result_path, is_animated, palette_name, fx_list, size = await self._process(
                            url, options
                        )
                        await ev.send(ev.image_result(result_path))
                        fx_str = "+".join(fx_list) if fx_list else "无"
                        await ev.send(
                            ev.plain_result(
                                f"✨ 像素化完成！SIZE={size} | 调色板={palette_name} | FX={fx_str}"
                            )
                        )
                        # Schedule cleanup
                        asyncio.create_task(self._cleanup(result_path))
                        controller.stop()
                    else:
                        # Check for cancel command
                        if ev.message_str.strip() in ("取消", "退出", "cancel"):
                            await ev.send(ev.plain_result("已取消像素化~"))
                            controller.stop()
                        else:
                            await ev.send(ev.plain_result("⚠️ 未检测到图片，请发送一张图片~"))
                            controller.keep(timeout=60, reset_timeout=True)

                try:
                    await wait_for_image(event)
                except TimeoutError:
                    yield event.plain_result("⏰ 等待超时，已取消~")
                finally:
                    event.stop_event()

        except ValueError as e:
            logger.warning(f"Parameter error: {e}")
            yield event.plain_result(f"❌ 参数错误: {e}")
        except Exception as e:
            logger.error(f"Pixel command error: {e}", exc_info=True)
            yield event.plain_result(f"❌ 处理失败: {str(e)}")

    def _parse_options(self, event: AstrMessageEvent) -> dict:
        """
        Parse command options from message string.

        Returns:
            dict with keys: size, palette, fx_list, at_qq
        """
        message_str = event.message_str.strip()
        tokens = message_str.split()[1:]  # Skip command itself

        size = None
        palette = None
        fx_list = None
        at_qq = None

        for token in tokens:
            token = token.strip()
            if not token:
                continue
            # Check for size (2-5)
            if token.isdigit() and 2 <= int(token) <= 5:
                size = int(token)
                continue
            # Check for palette name
            if is_valid_palette(token):
                palette = normalize_palette_name(token)
                continue
            # Check for FX names (can be comma-separated or individual tokens)
            potential_fx = []
            for fx_token in token.split(","):
                fx_token = fx_token.strip().lower()
                if fx_token in ALL_FX:
                    potential_fx.append(fx_token)
            if potential_fx:
                if fx_list is None:
                    fx_list = []
                fx_list.extend(potential_fx)

        # Extract @user from message chain
        message_chain = event.get_messages()
        for comp in message_chain:
            if isinstance(comp, Comp.At):
                at_qq = comp.qq
                break

        # Apply defaults from config if not specified
        if size is None:
            size = (
                self.default_size
                if 2 <= self.default_size <= 5
                else random.randint(2, 5)
            )

        if palette is None:
            if self.default_palette and is_valid_palette(self.default_palette):
                palette = normalize_palette_name(self.default_palette)
            else:
                # Random palette
                palette = random.choice(list_palettes())

        if fx_list is None or len(fx_list) == 0:
            if self.default_fx:
                fx_list = normalize_fx_names(self.default_fx.split(","))
            else:
                fx_list = []  # Empty means no FX

        return {
            "size": size,
            "palette": palette,
            "fx_list": fx_list,
            "at_qq": at_qq,
        }

    def _extract_image_url(
        self, event: AstrMessageEvent, at_qq: str | None
    ) -> str | None:
        """
        Extract image URL from event, following priority order.

        Priority:
        1. Image component in message chain (includes reply/quote images)
        2. @user's avatar URL
        3. Sender's avatar URL (fallback)

        Returns:
            Image URL or None
        """
        message_chain = event.get_messages()

        # Priority 1: Check for image in message chain
        for comp in message_chain:
            if isinstance(comp, Comp.Image):
                return comp.url

        # Priority 2: @user avatar
        if at_qq:
            return AVATAR_URL_TEMPLATE.format(qq=at_qq)

        # Priority 3: Sender's avatar (fallback)
        sender_id = event.get_sender_id()
        if sender_id:
            return AVATAR_URL_TEMPLATE.format(qq=sender_id)

        return None

    def _extract_image_url_from_chain(self, event: AstrMessageEvent) -> str | None:
        """Extract only Image URL from message chain (for wait mode)."""
        message_chain = event.get_messages()
        for comp in message_chain:
            if isinstance(comp, Comp.Image):
                return comp.url
        return None

    async def _process(
        self, image_url: str, options: dict
    ) -> tuple[str, bool, str, list[str], int]:
        """
        Full rendering pipeline: download -> validate -> pixelate -> fx -> save.

        Returns:
            (output_path, is_animated, palette_name, fx_list, size)
        """
        size = options["size"]
        palette_name = options["palette"]
        fx_list = options["fx_list"]

        # Download image
        image = await self._download_image(image_url)
        # Validate image
        if image is None:
            raise ValueError("无法下载图片")

        # Validate and resize if needed
        width, height = image.size
        max_dim = max(width, height)
        if max_dim > self.max_image_size:
            scale = self.max_image_size / max_dim
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            logger.info(f"Resized image from {width}x{height} to {new_width}x{new_height}")

        # Render in thread pool
        output_path, is_animated = await asyncio.to_thread(
            self._render_sync, image, size, palette_name, fx_list
        )

        return output_path, is_animated, palette_name, fx_list, size

    def _render_sync(
        self,
        image: Image.Image,
        size: int,
        palette_name: str,
        fx_list: list[str],
    ) -> tuple[str, bool]:
        """
        Synchronous rendering function, runs in thread pool.

        Returns:
            (output_path, is_animated)
        """
        # Pixelate
        pixelated = pixelate(image, size, palette_name, dither=False)

        # Apply FX effects
        is_animated, frames = apply_fx(
            pixelated,
            fx_list,
            palette_name=palette_name,
            cycle_frames=self.gif_frames,
            ghost_frames=self.gif_frames,
            gif_duration=self.gif_duration,
        )

        # Generate output filename
        ext = ".gif" if is_animated else ".png"
        filename = f"pixel_{uuid4().hex[:8]}{ext}"
        output_path = os.path.join(self._temp_dir, filename)

        # Save result
        if is_animated:
            save_gif(frames, output_path, duration=self.gif_duration)
        else:
            frames[0].save(output_path, "PNG")

        logger.info(f"Saved {'GIF' if is_animated else 'PNG'} to {output_path}")

        return output_path, is_animated

    async def _download_image(self, url: str) -> Image.Image | None:
        """
        Download image from URL.

        Returns:
            PIL Image or None if failed
        """

        def _download():
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read()
            return Image.open(io.BytesIO(data)).convert("RGB")

        try:
            return await asyncio.to_thread(_download)
        except Exception as e:
            logger.error(f"Failed to download image from {url}: {e}")
            return None

    async def _cleanup(self, path: str) -> None:
        """Clean up temporary file after a delay."""
        await asyncio.sleep(30)  # Wait a bit before cleanup
        try:
            if os.path.exists(path):
                os.remove(path)
                logger.debug(f"Cleaned up temporary file: {path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temporary file {path}: {e}")
