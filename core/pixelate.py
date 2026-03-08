"""
Core pixelation engine for converting images to pixel art style.

Provides the main pixelate() function and supporting utilities
for downscaling, palette mapping, and upscaling.
"""

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


def _build_palette_image(palette: np.ndarray) -> Image.Image:
    """Construct a Pillow P-mode reference image for quantize.

    Unused palette entries are filled with the last palette color
    to prevent Pillow from mapping pixels to spurious black (0,0,0).
    """
    palette_image = Image.new("P", (1, 1))
    flat = palette.flatten().tolist()
    # Fill remaining entries with the last color to avoid introducing
    # spurious black when the palette has fewer than 256 colors
    last_color = flat[-3:]  # Last RGB triplet
    while len(flat) < 768:
        flat.extend(last_color)
    palette_image.putpalette(flat)
    return palette_image


def apply_floyd_steinberg_dither(
    rgb_array: np.ndarray,
    palette: np.ndarray,
    *,
    alpha_mask: np.ndarray | None = None,
) -> np.ndarray:
    """
    Floyd-Steinberg dithering using Pillow's built-in C implementation.

    Delegates to Pillow's quantize() with FLOYDSTEINBERG dither mode,
    which runs the same algorithm (left-to-right, top-to-bottom error
    diffusion with 7/16, 3/16, 5/16, 1/16 weights) in native C code.

    For images with transparent regions (alpha_mask), transparent pixels
    are pre-filled with their nearest palette color before quantization.
    This minimizes error diffusion leakage from transparent areas into
    adjacent opaque pixels.

    Args:
        rgb_array: Shape (H, W, 3), dtype uint8
        palette: Shape (K, 3), dtype uint8
        alpha_mask: Optional shape (H, W) bool array.
                    True = opaque (process normally),
                    False = transparent (skip, no color mapping or error diffusion).

    Returns:
        Quantized array with only palette colors, dtype uint8
    """
    palette_img = _build_palette_image(palette)

    work = rgb_array.copy()

    # Pre-fill transparent pixels with nearest palette color to minimize
    # error diffusion leakage into adjacent opaque regions
    if alpha_mask is not None and not alpha_mask.all():
        transparent_pixels = work[~alpha_mask]
        if len(transparent_pixels) > 0:
            work[~alpha_mask] = map_array_to_palette_rgb(transparent_pixels, palette)

    rgb_image = Image.fromarray(work, mode="RGB")

    quantized = rgb_image.quantize(
        palette=palette_img,
        dither=Image.Dither.FLOYDSTEINBERG,
    )

    result = np.array(quantized.convert("RGB"), dtype=np.uint8)

    # Restore original RGB for transparent pixels
    if alpha_mask is not None:
        result[~alpha_mask] = rgb_array[~alpha_mask]

    return result


def map_to_palette(
    image: Image.Image,
    palette: np.ndarray,
    *,
    dither: bool = False,
) -> Image.Image:
    """
    Map all pixels to nearest color in palette.

    Supports both RGB and RGBA images. For RGBA images, pixels with
    alpha < 30 are skipped (not mapped to palette).

    Args:
        image: Input PIL image (RGB or RGBA mode)
        palette: Numpy array of shape (N, 3) with dtype uint8
        dither: If True, use Floyd-Steinberg dithering;
                if False, use vectorized RGB Euclidean distance

    Returns:
        PIL.Image with palette-mapped colors (same mode as input)
    """
    # Validate palette is not empty
    if len(palette) == 0:
        raise ValueError("Palette must not be empty")

    img_array = np.array(image)
    has_alpha = image.mode == "RGBA" and img_array.shape[2] == 4

    if has_alpha:
        rgb_array = img_array[:, :, :3]
        alpha_array = img_array[:, :, 3]
        opaque_mask = alpha_array >= 30
    else:
        rgb_array = img_array

    if dither:
        result_rgb = apply_floyd_steinberg_dither(
            rgb_array, palette,
            alpha_mask=opaque_mask if has_alpha else None,
        )
    else:
        result_rgb = map_array_to_palette_rgb(rgb_array, palette)

    if has_alpha:
        # Restore original RGB for transparent pixels
        result_rgb[~opaque_mask] = rgb_array[~opaque_mask]
        result_array = np.dstack([result_rgb, alpha_array])
        return Image.fromarray(result_array, mode="RGBA")
    else:
        return Image.fromarray(result_rgb, mode="RGB")


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
        image: Input PIL image (any mode, will be converted to RGBA)
        size: Pixel block size (2-5), used to calculate downscale factor
        palette: Palette name string or numpy array of shape (N, 3)
        dither: Enable Floyd-Steinberg dithering during palette mapping

    Returns:
        Pixelated PIL.Image in RGBA mode
    """
    # Validate parameters
    if not (2 <= size <= 5):
        raise ValueError(f"Pixel size must be between 2 and 5, got {size}")

    # Convert to RGBA to preserve alpha channel
    image = image.convert("RGBA")

    # Store original size for final upscaling
    original_size = image.size

    # Resolve palette if string
    if isinstance(palette, str):
        palette_array = get_palette(palette)
    else:
        palette_array = palette

    # Step 1: Resize down (RGBA)
    small = resize_for_pixelation(image, size)

    # Step 2: Split into RGB and Alpha
    small_array = np.array(small)
    rgb_array = small_array[:, :, :3]
    alpha_array = small_array[:, :, 3]

    # Step 3: Map to palette, skipping transparent pixels (alpha < 30)
    opaque_mask = alpha_array >= 30

    if dither:
        mapped_rgb = apply_floyd_steinberg_dither(rgb_array, palette_array, alpha_mask=opaque_mask)
    else:
        mapped_rgb = map_array_to_palette_rgb(rgb_array, palette_array)

    # Restore original RGB for transparent pixels (alpha < 30)
    mapped_rgb[~opaque_mask] = rgb_array[~opaque_mask]

    # Step 4: Recombine RGBA
    result_array = np.dstack([mapped_rgb, alpha_array])
    small_mapped = Image.fromarray(result_array, mode="RGBA")

    # Step 5: Upscale back to original size
    result = upscale_nearest(small_mapped, original_size)

    return result
