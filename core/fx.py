"""
FX effects for pixel art post-processing.

Provides 5 effects:
- Static: crt (scanline overlay)
- Animated: glitch (RGB shift animation), dither (shimmering texture),
           cycle (palette rotation), ghost (trail effect)

Note: The 'dither' animation applies subtle brightness perturbation per frame
before Floyd-Steinberg dithering, creating a shimmering texture effect.
"""

import random
from typing import Final

import numpy as np
from numpy.typing import NDArray
from PIL import Image

from .palettes import get_palette
from .pixelate import map_to_palette


# FX categories
STATIC_FX: Final[set[str]] = {"crt"}
ANIMATED_FX: Final[set[str]] = {"glitch", "dither", "cycle", "ghost"}
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


def apply_glitch(image: Image.Image, shift: int = 6, band_count: int = 8) -> Image.Image:
    """
    Glitch effect: RGB channel offset + random band displacement.

    Args:
        image: Input PIL image (RGB or RGBA mode)
        shift: Channel shift amount in pixels
        band_count: Number of random bands to displace

    Returns:
        Glitched PIL image (same mode as input)
    """
    # Preserve alpha if present
    has_alpha = image.mode == "RGBA"
    if has_alpha:
        rgb_image = image.convert("RGB")
        alpha_channel = image.split()[3]
    else:
        rgb_image = image

    arr = np.array(rgb_image)
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

    glitched_rgb = Image.fromarray(result, mode="RGB")

    if has_alpha:
        glitched_rgb.putalpha(alpha_channel)
        return glitched_rgb
    else:
        return glitched_rgb


def apply_glitch_frames(
    image: Image.Image,
    frames: int = 8,
    max_shift: int = 6,
    base_band_count: int = 8,
) -> list[Image.Image]:
    """
    Generate glitch animation frames with varying shift and band displacement.

    Args:
        image: Input PIL image
        frames: Number of frames to generate (minimum 2 for GIF)
        max_shift: Maximum RGB channel shift
        base_band_count: Base number of displacement bands

    Returns:
        List of glitched frames
    """
    result_frames = []

    frame_count = max(frames, 2)  # Ensure at least 2 frames
    for i in range(frame_count):
        # Vary shift and band_count per frame for animation effect
        phase = i / frame_count
        shift = max(1, int(round(1 + (max_shift - 1) * abs(np.sin(phase * np.pi)))))
        band_count = max(2, base_band_count + (i % 3) - 1)

        # Generate single glitch frame
        frame = apply_glitch(image, shift=shift, band_count=band_count)
        result_frames.append(frame)

    return result_frames


def apply_crt(image: Image.Image, scanline_alpha: int = 48) -> Image.Image:
    """
    CRT scanline effect: overlay semi-transparent black lines.

    Args:
        image: Input PIL image (RGB or RGBA mode)
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

    return Image.fromarray(result, mode="RGBA")


def apply_dither_frames(
    image: Image.Image,
    palette_name: str,
    *,
    pixel_size: int = 1,
    frames: int = 8,
    noise_strength: float = 2.0,
) -> list[Image.Image]:
    """
    Generate dither animation frames with subtle noise variation.

    When pixel_size > 1, downscale before dithering and upscale after
    for much better performance on large images.

    Each frame applies slight brightness perturbation before dithering,
    creating a subtle shimmer effect in the dithered texture.

    Args:
        image: Input PIL image
        palette_name: Name of palette to use for dithering
        pixel_size: Size of pixel blocks (downscale before dither for performance)
        frames: Number of frames to generate (minimum 2 for GIF)
        noise_strength: Strength of per-frame noise (0-10, default 2.0)

    Returns:
        List of dithered frames
    """
    # Defensive: ensure pixel_size is at least 1
    pixel_size = max(pixel_size, 1)

    frame_count = max(frames, 2)

    # Move get_palette outside loop (was called every frame)
    palette = get_palette(palette_name)

    # Save original size for final upscaling
    original_size = image.size

    # If pixel_size > 1, downscale to pixel grid size first
    if pixel_size > 1:
        grid_w = max(1, image.size[0] // pixel_size)
        grid_h = max(1, image.size[1] // pixel_size)
        work_image = image.resize((grid_w, grid_h), Image.Resampling.BILINEAR)
    else:
        work_image = image

    # Convert to array once, outside loop (avoid repeated np.array calls)
    base_arr = np.array(work_image)
    is_rgba = work_image.mode == "RGBA"

    # --- 两阶段策略：先按唯一 offset 计算，再按帧序列复用 ---

    # 阶段 1：计算每帧的 noise_offset，找出唯一值
    offsets = []
    for i in range(frame_count):
        phase = i / frame_count
        noise_offset = int(noise_strength * np.sin(phase * 2 * np.pi))
        offsets.append(noise_offset)

    unique_offsets = set(offsets)

    # 阶段 2：每个唯一 offset 只计算一次 dither
    offset_to_frame: dict[int, Image.Image] = {}
    for offset in unique_offsets:
        if is_rgba:
            rgb = base_arr[:, :, :3].astype(np.int16)
            alpha = base_arr[:, :, 3:]
            rgb = np.clip(rgb + offset, 0, 255).astype(np.uint8)
            perturbed_arr = np.concatenate([rgb, alpha], axis=2)
            perturbed = Image.fromarray(perturbed_arr, mode="RGBA")
        else:
            arr = base_arr.astype(np.int16)
            arr = np.clip(arr + offset, 0, 255).astype(np.uint8)
            perturbed = Image.fromarray(arr, mode=work_image.mode)

        frame = map_to_palette(perturbed, palette, dither=True)

        if pixel_size > 1:
            frame = frame.resize(original_size, Image.Resampling.NEAREST)

        offset_to_frame[offset] = frame

    # 阶段 3：按原始帧顺序组装（复用已计算的帧）
    result_frames = [offset_to_frame[o].copy() for o in offsets]

    return result_frames


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

    # Flatten to (H*W, 3) - only take RGB channels for RGBA support
    height, width = arr.shape[:2]
    pixels = arr[:, :, :3].reshape(-1, 3)

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
        image: Input PIL image (RGB or RGBA mode, pixelated and palette-mapped)
        palette_name: Name of the palette used
        frames: Number of animation frames

    Returns:
        List of frames for animation
    """
    palette = get_palette(palette_name)

    # Preserve alpha if present
    has_alpha = image.mode == "RGBA"
    if has_alpha:
        img_array = np.array(image)
        rgb_array = img_array[:, :, :3]
        alpha_array = img_array[:, :, 3]
        opaque_mask = alpha_array >= 30
        rgb_image = Image.fromarray(rgb_array, mode="RGB")
    else:
        rgb_image = image
        opaque_mask = None

    # Build index map: which palette index each pixel uses
    index_map = _build_palette_index_map(rgb_image, palette)
    height, width = index_map.shape

    result_frames = []

    for i in range(frames):
        # Create shifted palette
        shifted_palette = np.roll(palette, shift=i, axis=0)

        # Remap using shifted palette
        frame_rgb = shifted_palette[index_map]

        if has_alpha:
            # Restore original RGB for transparent pixels (alpha < 30)
            frame_rgb[~opaque_mask] = rgb_array[~opaque_mask]
            # Recombine with alpha
            frame_arr = np.dstack([frame_rgb, alpha_array])
            frame = Image.fromarray(frame_arr, mode="RGBA")
        else:
            frame = Image.fromarray(frame_rgb, mode="RGB")

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
        image: Input PIL image (RGB or RGBA mode)
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
        frame = Image.fromarray(final_arr, mode="RGBA")
        result_frames.append(frame)

    return result_frames


def apply_fx(
    image: Image.Image,
    fx_list: list[str],
    *,
    palette_name: str | None = None,
    pixel_size: int = 1,
    cycle_frames: int = 8,
    ghost_frames: int = 6,
    gif_duration: int = 100,
) -> tuple[bool, list[Image.Image]]:
    """
    Apply FX effects to a pixelated image.

    Strategy:
    1. Separate fx_list into static and animated
    2. Apply all static FX first (only crt)
    3. If animated FX exist, generate frames from appropriate source
       - glitch: uses static-FX-processed image, generates varying RGB shifts
       - dither: uses static-FX-processed image, generates shimmering dither texture
       - cycle: uses pre-static-FX image to avoid color drift
       - ghost: uses static-FX-processed image
    4. If multiple animated FX, only use first one found

    Note: All animated FX use gif_frames config (passed as cycle_frames/ghost_frames).

    Args:
        image: Input PIL image (RGB or RGBA mode, pixelated)
        fx_list: List of FX names to apply
        palette_name: Required for dither and cycle effects
        pixel_size: Pixel block size (passed to dither for downscaling optimization)
        cycle_frames: Number of frames for animated FX (glitch, dither, cycle, ghost)
        ghost_frames: Number of frames for ghost animation (unused, for API consistency)
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

    # Apply static FX (only crt)
    current_image = image.copy()

    for fx_name in static_fx:
        if fx_name == "crt":
            current_image = apply_crt(current_image)

    # Handle animated FX (only first one if multiple)
    if animated_fx:
        animated_name = animated_fx[0]

        if animated_name == "glitch":
            # Glitch animation uses gif_frames config (same as other animated FX)
            frames = apply_glitch_frames(current_image, frames=cycle_frames)
            return True, frames

        if animated_name == "dither":
            if palette_name is None:
                # Cannot dither without palette, return static result
                return False, [current_image]
            # Dither animation uses gif_frames config (same as other animated FX)
            frames = apply_dither_frames(
                current_image, palette_name,
                pixel_size=pixel_size,
                frames=cycle_frames,
            )
            return True, frames

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
