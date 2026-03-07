"""
Core pixelation engine for converting images to pixel art style.

Provides the main pixelate() function and supporting utilities
for downscaling, palette mapping, and upscaling.
"""

from typing import cast

import numpy as np
from numpy.typing import NDArray
from PIL import Image

from .palettes import get_palette


def resize_for_pixelation(image: Image.Image, pixel_size: int) -> Image.Image:
    """
    Resize image down by pixel_size factor using BILINEAR interpolation.

    New width = original_width // pixel_size
    New height = original_height // pixel_size
    Minimum dimension is 1.

    Args:
        image: Input PIL image
        pixel_size: Downscale factor (block size)

    Returns:
        Resized PIL image
    """
    orig_width, orig_height = image.size
    new_width = max(1, orig_width // pixel_size)
    new_height = max(1, orig_height // pixel_size)
    return image.resize((new_width, new_height), Image.Resampling.BILINEAR)


def map_array_to_palette_rgb(
    rgb_array: np.ndarray,
    palette: np.ndarray,
) -> np.ndarray:
    """
    Vectorized nearest-color mapping using NumPy broadcasting.

    Args:
        rgb_array: Shape (H, W, 3) or (N, 3), dtype uint8
        palette: Shape (K, 3), dtype uint8

    Returns:
        Array with same shape as rgb_array, with each pixel
        replaced by its nearest palette color.
    """
    # Flatten to (N, 3) if needed
    original_shape = rgb_array.shape
    if rgb_array.ndim == 3:
        pixels = rgb_array.reshape(-1, 3)
    else:
        pixels = rgb_array

    # Convert to int32 to avoid uint8 overflow in distance calculation
    pixels_int = pixels.astype(np.int32)
    palette_int = palette.astype(np.int32)

    # Reshape for broadcasting:
    # pixels: (N, 1, 3)
    # palette: (1, K, 3)
    pixels_expanded = pixels_int[:, np.newaxis, :]  # (N, 1, 3)
    palette_expanded = palette_int[np.newaxis, :, :]  # (1, K, 3)

    # Compute squared Euclidean distance: (N, K)
    diff = pixels_expanded - palette_expanded
    distances = np.sum(diff**2, axis=2)

    # Find nearest palette index for each pixel
    indices = np.argmin(distances, axis=1)

    # Map to palette colors
    result = palette[indices]

    # Restore original shape
    if len(original_shape) == 3:
        result = result.reshape(original_shape)

    return result


def apply_floyd_steinberg_dither(
    rgb_array: np.ndarray,
    palette: np.ndarray,
) -> np.ndarray:
    """
    Floyd-Steinberg dithering on the pixel grid.

    Process pixels left-to-right, top-to-bottom.
    Error diffusion weights:
        right = 7/16
        bottom-left = 3/16
        bottom = 5/16
        bottom-right = 1/16

    Args:
        rgb_array: Shape (H, W, 3), dtype uint8
        palette: Shape (K, 3), dtype uint8

    Returns:
        Quantized array with only palette colors, dtype uint8
    """
    # Work with float64 to avoid precision issues
    work = rgb_array.astype(np.float64)
    height, width = work.shape[:2]
    result = np.zeros_like(work)

    palette_float = palette.astype(np.float64)
    palette_int = palette.astype(np.int32)

    for y in range(height):
        for x in range(width):
            old_pixel = work[y, x].copy()

            # Find nearest palette color
            diff = palette_int.astype(np.int32) - old_pixel.astype(np.int32)
            distances = np.sum(diff**2, axis=1)
            nearest_idx = np.argmin(distances)
            new_pixel = palette_float[nearest_idx]

            result[y, x] = new_pixel

            # Calculate quantization error
            error = old_pixel - new_pixel

            # Diffuse error to neighbors
            # Right: 7/16
            if x + 1 < width:
                work[y, x + 1] += error * (7 / 16)

            # Bottom row neighbors
            if y + 1 < height:
                # Bottom-left: 3/16
                if x - 1 >= 0:
                    work[y + 1, x - 1] += error * (3 / 16)
                # Bottom: 5/16
                work[y + 1, x] += error * (5 / 16)
                # Bottom-right: 1/16
                if x + 1 < width:
                    work[y + 1, x + 1] += error * (1 / 16)

    # Clip and convert back to uint8
    return np.clip(result, 0, 255).astype(np.uint8)


def map_to_palette(
    image: Image.Image,
    palette: np.ndarray,
    *,
    dither: bool = False,
) -> Image.Image:
    """
    Map all pixels to nearest color in palette.

    Args:
        image: Input PIL image (should be RGB mode)
        palette: Numpy array of shape (N, 3) with dtype uint8
        dither: If True, use Floyd-Steinberg dithering;
                if False, use vectorized RGB Euclidean distance

    Returns:
        PIL.Image in RGB mode with palette-mapped colors
    """
    # Validate palette is not empty
    if len(palette) == 0:
        raise ValueError("Palette must not be empty")

    # Convert to numpy array
    rgb_array = np.array(image)

    if dither:
        result_array = apply_floyd_steinberg_dither(rgb_array, palette)
    else:
        result_array = map_array_to_palette_rgb(rgb_array, palette)

    return Image.fromarray(result_array, mode="RGB")


def upscale_nearest(
    image: Image.Image,
    target_size: tuple[int, int],
) -> Image.Image:
    """
    Upscale using NEAREST neighbor interpolation.

    Args:
        image: Input PIL image
        target_size: Target (width, height)

    Returns:
        Upscaled PIL image with pixelated appearance preserved
    """
    return image.resize(target_size, Image.Resampling.NEAREST)


def pixelate(
    image: Image.Image,
    size: int,
    palette: str | np.ndarray,
    *,
    dither: bool = False,
) -> Image.Image:
    """
    Main pixelation pipeline: resize down -> palette map -> resize up.

    Args:
        image: Input PIL image (any mode, will be converted to RGB)
        size: Pixel block size (2-5), used to calculate downscale factor
        palette: Palette name string or numpy array of shape (N, 3)
        dither: Enable Floyd-Steinberg dithering during palette mapping

    Returns:
        Pixelated PIL.Image in RGB mode
    """
    # Validate parameters
    if not (2 <= size <= 5):
        raise ValueError(f"Pixel size must be between 2 and 5, got {size}")

    # Convert to RGB
    image = image.convert("RGB")

    # Store original size for final upscaling
    original_size = image.size

    # Resolve palette if string
    if isinstance(palette, str):
        palette_array = get_palette(palette)
    else:
        palette_array = palette

    # Step 1: Resize down
    small = resize_for_pixelation(image, size)

    # Step 2: Map to palette
    mapped = map_to_palette(small, palette_array, dither=dither)

    # Step 3: Upscale back to original size
    result = upscale_nearest(mapped, original_size)

    return result
