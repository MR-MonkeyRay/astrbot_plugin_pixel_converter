"""Rendering pipeline for pixel converter plugin."""

import asyncio
import io
import os
import urllib.request
from uuid import uuid4

from PIL import Image

from astrbot.api import logger

from .types import PixelOptions, RenderConfig, RenderResult
from .pixelate import pixelate
from .fx import apply_fx
from .gif import save_gif


# --- 并发控制 ---
_render_semaphore: asyncio.Semaphore | None = None
_render_semaphore_size: int = 0


def _get_render_semaphore(max_concurrent: int) -> asyncio.Semaphore:
    """获取渲染信号量，按配置的并发数延迟初始化。"""
    global _render_semaphore, _render_semaphore_size
    if _render_semaphore is None or _render_semaphore_size != max_concurrent:
        _render_semaphore = asyncio.Semaphore(max_concurrent)
        _render_semaphore_size = max_concurrent
    return _render_semaphore


async def download_image(url: str) -> Image.Image | None:
    """
    Download image from URL.

    Args:
        url: Image URL to download

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


def render_sync(
    image: Image.Image,
    size: int,
    palette: str,
    fx_list: list[str],
    config: RenderConfig,
) -> RenderResult:
    """
    Synchronous rendering function, runs in thread pool.

    Args:
        image: PIL Image to process
        size: Pixel size (2-5)
        palette: Palette name
        fx_list: List of FX effect names
        config: Render configuration

    Returns:
        RenderResult with output path and animation flag
    """
    # Pixelate
    pixelated = pixelate(image, size, palette, dither=False)

    logger.debug(f"FX list: {fx_list}, palette: {palette}, size: {size}")

    # Apply FX effects
    is_animated, frames = apply_fx(
        pixelated,
        fx_list,
        palette_name=palette,
        pixel_size=size,
        cycle_frames=config.gif_frames,
        ghost_frames=config.gif_frames,
        gif_duration=config.gif_duration,
    )

    # Generate output filename
    ext = ".gif" if is_animated else ".png"
    filename = f"pixel_{uuid4().hex[:8]}{ext}"
    output_path = os.path.join(config.temp_dir, filename)

    # Save result
    if is_animated:
        save_gif(frames, output_path, duration=config.gif_duration)
    else:
        frames[0].save(output_path, "PNG")

    logger.info(f"Saved {'GIF' if is_animated else 'PNG'} to {output_path}")

    return RenderResult(output_path=output_path, is_animated=is_animated)


async def process_image(
    image_url: str,
    options: PixelOptions,
    config: RenderConfig,
) -> RenderResult:
    """
    Full rendering pipeline: download -> validate -> pixelate -> fx -> save.

    Args:
        image_url: URL of image to process
        options: Parsed pixel options
        config: Render configuration

    Returns:
        RenderResult with output path and animation flag

    Raises:
        ValueError: If image cannot be downloaded
    """
    # Download image
    image = await download_image(image_url)
    if image is None:
        raise ValueError("无法下载图片")

    # Validate and resize if needed
    width, height = image.size
    max_dim = max(width, height)
    if max_dim > config.max_image_size:
        scale = config.max_image_size / max_dim
        new_width = int(width * scale)
        new_height = int(height * scale)
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        logger.info(f"Resized image from {width}x{height} to {new_width}x{new_height}")

    # Render in thread pool with concurrency control
    sem = _get_render_semaphore(config.max_concurrent_renders)
    async with sem:
        result = await asyncio.to_thread(
            render_sync,
            image,
            options.size,
            options.palette,
            options.fx_list,
            config,
        )

    return result


async def cleanup_file(path: str) -> None:
    """
    Clean up temporary file after a delay.

    Args:
        path: Path to file to clean up
    """
    await asyncio.sleep(30)  # Wait a bit before cleanup
    try:
        if os.path.exists(path):
            os.remove(path)
            logger.debug(f"Cleaned up temporary file: {path}")
    except Exception as e:
        logger.warning(f"Failed to cleanup temporary file {path}: {e}")
