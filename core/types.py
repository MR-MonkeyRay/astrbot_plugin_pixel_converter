"""Shared data types for pixel converter plugin."""

from dataclasses import dataclass


@dataclass
class PixelOptions:
    """Parsed pixel conversion options."""

    size: int
    palette: str
    fx_list: list[str]
    at_qq: str | None
    help: bool = False


@dataclass
class RenderConfig:
    """Configuration for rendering."""

    max_image_size: int
    gif_frames: int
    gif_duration: int
    temp_dir: str
    max_concurrent_renders: int = 8


@dataclass
class RenderResult:
    """Result of rendering operation."""

    output_path: str
    is_animated: bool
