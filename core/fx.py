"""
FX effects for pixel art post-processing.

Provides 5 effects:
- Static: glitch, crt, dither (re-applies palette with Floyd-Steinberg)
- Animated: cycle (palette rotation), ghost (trail effect)

Note: The 'dither' effect re-applies palette mapping with Floyd-Steinberg dithering
as a post-processing step on an already pixelated image.
"""

import random
from typing import Final

import numpy as np
from numpy.typing import NDArray
from PIL import Image

from .palettes import get_palette
from .pixelate import map_to_palette


# FX categories
STATIC_FX: Final[set[str]] = {"glitch", "crt", "dither"}
ANIMATED_FX: Final[set[str]] = {"cycle", "ghost"}
ALL_FX: Final[set[str]] = STATIC_FX | ANIMATED_FX


def normalize_fx_names(fx_list: list[str]) -> list[str]:
    """
    Normalize and validate FX names.

    - Convert to lowercase
    - Strip whitespace
    - Remove invalid/unknown names

    Args:
        fx_list: Raw FX name list

    Returns:
        List of valid, normalized FX names
    """
    normalized = []
    for fx in fx_list:
        name = fx.lower().strip()
        if name in ALL_FX:
            normalized.append(name)
    return normalized


def is_animated_fx(fx_list: list[str]) -> bool:
    """
    Check if any FX in list produces animation.

    Args:
        fx_list: List of FX names

    Returns:
        True if any animated FX is present
    """
    for fx in fx_list:
        if fx.lower().strip() in ANIMATED_FX:
            return True
    return False


def random_fx() -> list[str]:
    """
    Pick one random FX effect.

    Returns:
        List containing single random FX name
    """
    return [random.choice(list(ALL_FX))]


def apply_glitch(image: Image.Image, shift: int = 6, band_count: int = 8) -> Image.Image:
    """
    Glitch effect: RGB channel offset + random band displacement.

    Args:
        image: Input PIL image (RGB mode)
        shift: Channel shift amount in pixels
        band_count: Number of random bands to displace

    Returns:
        Glitched PIL image
    """
    arr = np.array(image)
    height, width = arr.shape[:2]

    # Split and shift channels
    r = arr[:, :, 0]
    g = arr[:, :, 1]
    b = arr[:, :, 2]

    # Shift R left, B right
    r_shifted = np.roll(r, shift=-shift, axis=1)
    b_shifted = np.roll(b, shift=shift, axis=1)

    # Merge channels back
    result = np.stack([r_shifted, g, b_shifted], axis=2).copy()

    # Random band displacement with safe bounds for small images
    for _ in range(band_count):
        # Limit band_height to available image height
        max_band_height = min(6, height)
        if max_band_height < 2:
            break  # Image too small for band displacement
        band_height = random.randint(2, max_band_height)
        y_start = random.randint(0, max(0, height - band_height))
        x_offset = random.randint(-10, 10)

        # Shift the band horizontally
        band = result[y_start : y_start + band_height, :, :].copy()
        result[y_start : y_start + band_height, :, :] = np.roll(band, shift=x_offset, axis=1)

    return Image.fromarray(result, mode="RGB")


def apply_crt(image: Image.Image, scanline_alpha: int = 48) -> Image.Image:
    """
    CRT scanline effect: overlay semi-transparent black lines.

    Args:
        image: Input PIL image (RGB mode)
        scanline_alpha: Alpha value (0-255) for scanline darkness

    Returns:
        PIL image with CRT scanline effect
    """
    # Convert to RGBA for alpha compositing
    rgba = image.convert("RGBA")
    arr = np.array(rgba)

    # Create scanline overlay
    overlay = np.zeros_like(arr)
    overlay[1::2, :, :] = [0, 0, 0, scanline_alpha]

    # Alpha composite: result = overlay * alpha + base * (1 - alpha)
    base_alpha = arr[:, :, 3:4] / 255.0
    overlay_alpha = overlay[:, :, 3:4] / 255.0

    # Composite RGB channels
    result_rgb = (
        overlay[:, :, :3] * overlay_alpha + arr[:, :, :3] * (1 - overlay_alpha)
    ).astype(np.uint8)

    # Keep original alpha channel
    result = np.concatenate([result_rgb, arr[:, :, 3:4]], axis=2)

    return Image.fromarray(result, mode="RGBA").convert("RGB")


def apply_dither(image: Image.Image, palette_name: str) -> Image.Image:
    """
    Dither effect: Re-apply palette mapping with Floyd-Steinberg dithering.

    This is a post-processing effect that re-maps an already pixelated image
    to the palette using Floyd-Steinberg dithering for a grainier, retro look.

    Args:
        image: Input PIL image (RGB mode, should be pixelated)
        palette_name: Name of palette to use for dithering

    Returns:
        Dithered PIL image
    """
    palette = get_palette(palette_name)
    return map_to_palette(image, palette, dither=True)


def _build_palette_index_map(
    image: Image.Image,
    palette: NDArray[np.uint8],
) -> NDArray[np.uint8]:
    """
    Build index map: each pixel -> index in palette.

    Args:
        image: PIL image (RGB)
        palette: Shape (N, 3) palette array

    Returns:
        2D array of palette indices
    """
    arr = np.array(image)

    # Flatten to (H*W, 3)
    height, width = arr.shape[:2]
    pixels = arr.reshape(-1, 3)

    # Convert to int32 for distance calculation
    pixels_int = pixels.astype(np.int32)
    palette_int = palette.astype(np.int32)

    # Compute distances: (H*W, N)
    distances = np.sum((pixels_int[:, np.newaxis, :] - palette_int[np.newaxis, :, :]) ** 2, axis=2)

    # Get nearest index for each pixel
    indices = np.argmin(distances, axis=1).astype(np.uint8)

    return indices.reshape(height, width)


def apply_cycle(
    image: Image.Image,
    palette_name: str,
    frames: int = 8,
) -> list[Image.Image]:
    """
    Palette cycle animation: rotate palette colors and remap.

    Args:
        image: Input PIL image (RGB mode, pixelated and palette-mapped)
        palette_name: Name of the palette used
        frames: Number of animation frames

    Returns:
        List of frames for animation
    """
    palette = get_palette(palette_name)

    # Build index map: which palette index each pixel uses
    index_map = _build_palette_index_map(image, palette)
    height, width = index_map.shape

    result_frames = []

    for i in range(frames):
        # Create shifted palette
        shifted_palette = np.roll(palette, shift=i, axis=0)

        # Remap using shifted palette
        frame_arr = shifted_palette[index_map]
        frame = Image.fromarray(frame_arr, mode="RGB")
        result_frames.append(frame)

    return result_frames


def apply_ghost(
    image: Image.Image,
    frames: int = 6,
    alpha_decay: float = 0.72,
    offset_step: tuple[int, int] = (2, 2),
) -> list[Image.Image]:
    """
    Ghost trail effect: multiple frames with decaying transparency offset.

    Args:
        image: Input PIL image (RGB mode)
        frames: Number of animation frames
        alpha_decay: Multiplicative decay per ghost layer
        offset_step: (x, y) offset increment per frame

    Returns:
        List of frames for animation
    """
    # Convert to RGBA
    base_rgba = image.convert("RGBA")
    base_arr = np.array(base_rgba).astype(np.float64)
    height, width = base_arr.shape[:2]

    result_frames = []

    for i in range(frames):
        # Create canvas for this frame
        canvas = np.zeros_like(base_arr)

        # Calculate offset for ghost layer
        offset_x = i * offset_step[0]
        offset_y = i * offset_step[1]

        # Create ghost layer with offset
        ghost = np.roll(base_arr, shift=offset_y, axis=0)
        ghost = np.roll(ghost, shift=offset_x, axis=1)

        # Apply alpha decay to ghost
        ghost_alpha_factor = alpha_decay**i
        ghost[:, :, 3] = ghost[:, :, 3] * ghost_alpha_factor

        # Composite: ghost behind base
        # For simplicity, blend ghost onto canvas, then base on top
        # Alpha blending: out = fg * fg_alpha + bg * (1 - fg_alpha)
        ghost_alpha = ghost[:, :, 3:4] / 255.0
        canvas_rgb = ghost[:, :, :3] * ghost_alpha
        canvas_alpha = ghost[:, :, 3:4]

        # Now composite base on top
        base_alpha = base_arr[:, :, 3:4] / 255.0
        # Where base is visible, it overrides
        final_rgb = base_arr[:, :, :3] * base_alpha + canvas_rgb * (1 - base_alpha)
        final_alpha = np.maximum(base_arr[:, :, 3:4], canvas_alpha * (1 - base_alpha))

        # For the base frame (i=0), just use the original
        if i == 0:
            final_rgb = base_arr[:, :, :3]
            final_alpha = base_arr[:, :, 3:4]

        # Convert to uint8 and create image
        final_arr = np.concatenate(
            [final_rgb.astype(np.uint8), final_alpha.astype(np.uint8)],
            axis=2,
        )
        frame = Image.fromarray(final_arr, mode="RGBA").convert("RGB")
        result_frames.append(frame)

    return result_frames


def apply_fx(
    image: Image.Image,
    fx_list: list[str],
    *,
    palette_name: str | None = None,
    cycle_frames: int = 8,
    ghost_frames: int = 6,
    gif_duration: int = 100,
) -> tuple[bool, list[Image.Image]]:
    """
    Apply FX effects to a pixelated image.

    Strategy:
    1. Separate fx_list into static and animated
    2. Apply all static FX first (in order: dither -> glitch -> crt)
    3. If animated FX exist, generate frames from appropriate source
    4. If both cycle and ghost, only use first animated FX found

    Note: cycle animation uses the original pre-static-FX image to avoid
    color drift from glitch/crt effects. ghost uses the static-FX-processed image.

    Args:
        image: Input PIL image (RGB mode, pixelated)
        fx_list: List of FX names to apply
        palette_name: Required for dither and cycle effects
        cycle_frames: Number of frames for cycle animation
        ghost_frames: Number of frames for ghost animation
        gif_duration: Per-frame duration in ms (unused here, for API consistency)

    Returns:
        (is_animated, frames) where frames is [single_image] or [frame1, frame2, ...]
    """
    # Normalize and validate FX names
    valid_fx = normalize_fx_names(fx_list)

    if not valid_fx:
        # No valid FX, return original
        return False, [image.copy()]

    # Separate static and animated FX
    static_fx = [fx for fx in valid_fx if fx in STATIC_FX]
    animated_fx = [fx for fx in valid_fx if fx in ANIMATED_FX]

    # Save pre-static-fx image for cycle (needs clean palette-mapped input)
    pre_static_image = image.copy()

    # Apply static FX in defined order: dither -> glitch -> crt
    static_order = ["dither", "glitch", "crt"]
    current_image = image.copy()

    for fx_name in static_order:
        if fx_name in static_fx:
            if fx_name == "dither":
                if palette_name is None:
                    continue  # Skip dither without palette
                current_image = apply_dither(current_image, palette_name)
            elif fx_name == "glitch":
                current_image = apply_glitch(current_image)
            elif fx_name == "crt":
                current_image = apply_crt(current_image)

    # Handle animated FX (only first one if multiple)
    if animated_fx:
        animated_name = animated_fx[0]

        if animated_name == "cycle":
            if palette_name is None:
                # Cannot cycle without palette, return static result
                return False, [current_image]
            # Use pre-static image for cycle to avoid color drift
            frames = apply_cycle(pre_static_image, palette_name, frames=cycle_frames)
            return True, frames

        elif animated_name == "ghost":
            # Ghost uses the static-fx-processed image
            frames = apply_ghost(current_image, frames=ghost_frames)
            return True, frames

    # No animated FX, return static result
    return False, [current_image]
