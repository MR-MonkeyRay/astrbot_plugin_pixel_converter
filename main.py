"""
AstrBot Pixel Converter Plugin
Convert images to pixel art style with classic palettes and FX effects.
"""

import asyncio
import os
import shutil
import tempfile

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import astrbot.api.message_components as Comp
from astrbot.core.utils.session_waiter import session_waiter, SessionController

from .core.types import RenderConfig
from .core.parser import parse_options
from .core.helptext import build_help_text
from .core.sources import (
    extract_image_url,
    extract_image_url_from_chain,
)
from .core.renderer import process_image, cleanup_file


@register("astrbot_plugin_pixel_converter", "monkeyray", "将图片转换为像素风格", "0.1.1")
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

    def _get_render_config(self) -> RenderConfig:
        """Create RenderConfig from current settings."""
        return RenderConfig(
            max_image_size=self.max_image_size,
            gif_frames=self.gif_frames,
            gif_duration=self.gif_duration,
            temp_dir=self._temp_dir,
        )

    def _extract_at_qq_list(self, event: AstrMessageEvent) -> list[str]:
        """Extract list of @mentioned QQ numbers from message chain."""
        at_list = []
        for comp in event.get_messages():
            if isinstance(comp, Comp.At):
                at_list.append(comp.qq)
        return at_list

    @filter.command("像素画", alias=["pixel", "px"])
    async def pixel_command(self, event: AstrMessageEvent):
        """Convert image to pixel art style."""
        try:
            # Extract @mentions for parser
            at_qq_list = self._extract_at_qq_list(event)

            # Parse command options
            options = parse_options(
                message_str=event.message_str,
                at_qq_list=at_qq_list,
                default_size=self.default_size,
                default_palette=self.default_palette,
                default_fx=self.default_fx,
            )

            # Check for help request
            if options.help:
                help_text = build_help_text()
                yield event.plain_result(help_text)
                return

            # Get render config
            render_config = self._get_render_config()

            # Try to extract image source
            image_url = extract_image_url(
                message_chain=event.get_messages(),
                at_qq=options.at_qq,
                sender_id=event.get_sender_id(),
                Comp_module=Comp,
            )

            if image_url:
                # Direct processing
                result = await process_image(image_url, options, render_config)
                yield event.image_result(result.output_path)
                # Schedule cleanup
                asyncio.create_task(cleanup_file(result.output_path))
            else:
                # No image found, enter wait mode
                yield event.plain_result("📸 请发送一张图片，我来像素化~ (60秒超时)")

                @session_waiter(timeout=60, record_history_chains=False)
                async def wait_for_image(controller: SessionController, ev: AstrMessageEvent):
                    """Wait for user to send an image."""
                    # Check for image in message
                    url = extract_image_url_from_chain(ev.get_messages(), Comp)
                    if url:
                        # Found image
                        result = await process_image(url, options, render_config)
                        await ev.send(ev.image_result(result.output_path))
                        # Schedule cleanup
                        asyncio.create_task(cleanup_file(result.output_path))
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
