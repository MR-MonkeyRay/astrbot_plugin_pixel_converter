"""
GIF encoding utilities for animated pixel art.

Provides functions to save multiple frames as animated GIF files.
"""

from pathlib import Path

from PIL import Image


def normalize_gif_frames(frames: list[Image.Image]) -> list[Image.Image]:
    """
    Ensure all frames have same size and mode.

    - Convert to RGB if needed
    - Resize to first frame's size if inconsistent

    Args:
        frames: List of PIL images (may have different sizes/modes)

    Returns:
        List of normalized PIL images (all RGB, same size)
    """
    if not frames:
        return []

    # Get target size from first frame
    target_size = frames[0].size
    normalized = []

    for frame in frames:
        # Convert to RGB
        if frame.mode != "RGB":
            frame = frame.convert("RGB")

        # Resize if needed
        if frame.size != target_size:
            frame = frame.resize(target_size, Image.Resampling.NEAREST)

        normalized.append(frame)

    return normalized


def save_gif(
    frames: list[Image.Image],
    output_path: str | Path,
    duration: int = 100,
    *,
    loop: int = 0,
) -> Path:
    """
    Save frames as animated GIF.

    Args:
        frames: List of PIL.Image (must be >= 2 frames, same size recommended)
        output_path: File path to save
        duration: Per-frame duration in ms
        loop: Number of loops (0 = infinite)

    Algorithm:
    1. Normalize frames (ensure same size and mode)
    2. Convert all frames to 'P' mode (palette mode) for efficient GIF
    3. Use consistent palette across all frames for smooth animation
    4. Save using PIL save with save_all=True

    Returns:
        Path to saved GIF file
    """
    if len(frames) < 2:
        raise ValueError("GIF requires at least 2 frames")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Normalize frames
    frames = normalize_gif_frames(frames)

    # Build a global palette from the first frame
    # Quantize first frame to get consistent palette
    first_frame = frames[0]

    # Use ADAPTIVE quantization for better color matching
    # MEDIANCUT gives good results for pixel art
    first_palette = first_frame.quantize(colors=256, method=Image.Quantize.MEDIANCUT)

    # Convert all frames to P mode using the same palette
    p_frames = []
    for frame in frames:
        # Convert to P mode with the same palette
        p_frame = frame.quantize(palette=first_palette)
        p_frames.append(p_frame)

    # Save as animated GIF
    first_p = p_frames[0]
    rest_frames = p_frames[1:]

    first_p.save(
        output_path,
        format="GIF",
        save_all=True,
        append_images=rest_frames,
        loop=loop,
        duration=duration,
        disposal=2,  # Restore to background after each frame
    )

    return output_path
