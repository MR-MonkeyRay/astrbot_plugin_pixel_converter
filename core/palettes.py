"""
Palette definitions for pixel art conversion.
Contains 18 classic color palettes with utility functions.
"""

import random
from typing import Final

import numpy as np
from numpy.typing import NDArray


# Raw palette data: name -> list of RGB tuples
PALETTES: Final[dict[str, list[tuple[int, int, int]]]] = {
    # 1. sora (12 colors) - Original dark blue to warm yellow style
    "sora": [
        (26, 28, 44),
        (93, 39, 93),
        (177, 62, 83),
        (239, 125, 87),
        (255, 205, 117),
        (167, 240, 112),
        (56, 183, 100),
        (37, 113, 121),
        (41, 54, 111),
        (59, 93, 201),
        (65, 166, 246),
        (115, 239, 247),
    ],
    # 2. gameboy (4 colors) - Classic Game Boy green
    "gameboy": [
        (15, 56, 15),
        (48, 98, 48),
        (139, 172, 15),
        (155, 188, 15),
    ],
    # 3. nes (16 colors) - 8-bit Nintendo
    "nes": [
        (0, 0, 0),
        (252, 252, 252),
        (248, 56, 0),
        (0, 168, 0),
        (0, 88, 248),
        (104, 68, 252),
        (168, 0, 32),
        (248, 184, 0),
        (0, 120, 248),
        (252, 116, 96),
        (88, 216, 84),
        (88, 248, 152),
        (0, 0, 168),
        (248, 120, 248),
        (252, 160, 68),
        (184, 184, 184),
    ],
    # 4. cga (4 colors) - Early PC CGA
    "cga": [
        (0, 0, 0),
        (85, 255, 255),
        (255, 85, 255),
        (255, 255, 255),
    ],
    # 5. c64 (16 colors) - Commodore 64
    "c64": [
        (0, 0, 0),
        (255, 255, 255),
        (136, 0, 0),
        (170, 255, 238),
        (204, 68, 204),
        (0, 204, 85),
        (0, 0, 170),
        (238, 238, 119),
        (221, 136, 85),
        (102, 68, 0),
        (255, 119, 119),
        (51, 51, 51),
        (119, 119, 119),
        (170, 255, 102),
        (0, 136, 255),
        (187, 187, 187),
    ],
    # 6. pico8 (16 colors) - PICO-8 fantasy console
    "pico8": [
        (0, 0, 0),
        (29, 43, 83),
        (126, 37, 83),
        (0, 135, 81),
        (171, 82, 54),
        (95, 87, 79),
        (194, 195, 199),
        (255, 241, 232),
        (255, 0, 77),
        (255, 163, 0),
        (255, 236, 39),
        (0, 228, 54),
        (41, 173, 255),
        (131, 118, 156),
        (255, 119, 168),
        (255, 204, 170),
    ],
    # 7. sweetie16 (16 colors) - Modern pixel art
    "sweetie16": [
        (26, 28, 44),
        (44, 232, 245),
        (48, 96, 130),
        (50, 60, 57),
        (55, 148, 110),
        (91, 110, 225),
        (99, 199, 77),
        (118, 66, 138),
        (139, 155, 180),
        (172, 50, 50),
        (215, 123, 186),
        (226, 204, 76),
        (246, 214, 189),
        (255, 0, 68),
        (255, 137, 81),
        (255, 255, 255),
    ],
    # 8. pastel (12 colors) - Soft pastel tones
    "pastel": [
        (255, 179, 186),
        (255, 223, 186),
        (255, 255, 186),
        (186, 255, 201),
        (186, 225, 255),
        (219, 186, 255),
        (255, 186, 243),
        (255, 209, 220),
        (200, 255, 228),
        (186, 255, 255),
        (255, 239, 213),
        (230, 230, 250),
    ],
    # 9. mono (9 colors) - Black and white grayscale
    "mono": [
        (0, 0, 0),
        (32, 32, 32),
        (64, 64, 64),
        (96, 96, 96),
        (128, 128, 128),
        (160, 160, 160),
        (192, 192, 192),
        (224, 224, 224),
        (255, 255, 255),
    ],
    # 10. sepia (9 colors) - Vintage sepia tones
    "sepia": [
        (44, 28, 17),
        (75, 49, 32),
        (107, 73, 50),
        (140, 100, 71),
        (173, 129, 96),
        (200, 160, 125),
        (222, 190, 157),
        (240, 215, 190),
        (255, 237, 219),
    ],
    # 11. sunset (10 colors) - Sunset gradient
    "sunset": [
        (20, 10, 30),
        (60, 20, 60),
        (120, 30, 60),
        (180, 50, 50),
        (220, 90, 40),
        (245, 140, 50),
        (255, 190, 80),
        (255, 220, 130),
        (255, 240, 180),
        (255, 250, 220),
    ],
    # 12. ocean (10 colors) - Ocean blue
    "ocean": [
        (0, 10, 30),
        (0, 30, 60),
        (0, 60, 100),
        (0, 100, 140),
        (0, 140, 170),
        (30, 170, 200),
        (80, 200, 220),
        (140, 220, 235),
        (200, 240, 248),
        (230, 248, 255),
    ],
    # 13. earth (10 colors) - Earth tones
    "earth": [
        (34, 24, 15),
        (70, 50, 30),
        (110, 80, 45),
        (150, 110, 60),
        (180, 140, 80),
        (190, 170, 110),
        (160, 140, 100),
        (120, 100, 70),
        (80, 70, 50),
        (50, 40, 25),
    ],
    # 14. sakura (12 colors) - Cherry blossom pink
    "sakura": [
        (45, 20, 30),
        (90, 35, 50),
        (140, 55, 70),
        (190, 80, 100),
        (220, 120, 140),
        (240, 160, 175),
        (250, 195, 205),
        (255, 220, 225),
        (255, 240, 240),
        (200, 100, 120),
        (170, 60, 85),
        (255, 210, 215),
    ],
    # 15. cyber (12 colors) - Cyberpunk neon
    "cyber": [
        (10, 0, 20),
        (20, 0, 50),
        (40, 0, 80),
        (80, 0, 120),
        (140, 0, 180),
        (200, 0, 255),
        (0, 255, 200),
        (0, 200, 150),
        (255, 0, 100),
        (255, 100, 0),
        (255, 255, 0),
        (255, 255, 255),
    ],
    # 16. horror (12 colors) - Horror dark red
    "horror": [
        (10, 0, 0),
        (30, 5, 5),
        (60, 10, 10),
        (90, 15, 5),
        (120, 20, 10),
        (150, 25, 15),
        (100, 0, 0),
        (80, 0, 0),
        (50, 50, 50),
        (30, 30, 30),
        (200, 0, 0),
        (255, 50, 50),
    ],
    # 17. riso (3 colors) - Risograph print style
    "riso": [
        (0, 120, 191),
        (255, 72, 0),
        (0, 169, 92),
    ],
    # 18. cmyk (4 colors) - Four-color print
    "cmyk": [
        (0, 174, 239),
        (236, 0, 140),
        (255, 242, 0),
        (0, 0, 0),
    ],
}

# Alias mapping: alias -> canonical name
PALETTE_ALIASES: Final[dict[str, str]] = {
    "gb": "gameboy",
    "nintendo": "nes",
    "pico": "pico8",
    "sweetie": "sweetie16",
    "bw": "mono",
    "monochrome": "mono",
}

# Cached numpy arrays for each palette (built at module load)
_PALETTE_ARRAYS: dict[str, NDArray[np.uint8]] = {}


def _build_cache() -> None:
    """Build numpy array cache for all palettes at module load."""
    for name, colors in PALETTES.items():
        _PALETTE_ARRAYS[name] = np.array(colors, dtype=np.uint8)


# Build cache on module import
_build_cache()


def normalize_palette_name(name: str) -> str:
    """
    Normalize a palette name to its canonical form.

    - Converts to lowercase
    - Expands aliases to canonical names

    Args:
        name: Raw palette name (case-insensitive, may be alias)

    Returns:
        Canonical palette name

    Raises:
        ValueError: If the name is not a valid palette or alias
    """
    normalized = name.lower().strip()

    # Check if it's an alias
    if normalized in PALETTE_ALIASES:
        return PALETTE_ALIASES[normalized]

    # Check if it's a valid canonical name
    if normalized in PALETTES:
        return normalized

    raise ValueError(f"Unknown palette: '{name}'. Valid palettes: {list_palettes()}")


def get_palette(name: str) -> NDArray[np.uint8]:
    """
    Get palette colors as a numpy array.

    Args:
        name: Palette name (case-insensitive, supports aliases)

    Returns:
        Numpy array of shape (N, 3) with dtype uint8,
        where N is the number of colors in the palette
    """
    canonical = normalize_palette_name(name)
    return _PALETTE_ARRAYS[canonical].copy()


def list_palettes() -> list[str]:
    """
    Get list of all available palette names.

    Returns:
        List of 18 canonical palette names
    """
    return list(PALETTES.keys())


def is_valid_palette(name: str) -> bool:
    """
    Check if a name is a valid palette (canonical or alias).

    Args:
        name: Palette name to check

    Returns:
        True if the name is a valid palette or alias
    """
    normalized = name.lower().strip()
    return normalized in PALETTES or normalized in PALETTE_ALIASES


def random_palette() -> tuple[str, NDArray[np.uint8]]:
    """
    Select a random palette.

    Returns:
        Tuple of (palette_name, color_array)
        where color_array has shape (N, 3) dtype uint8
    """
    name = random.choice(list(PALETTES.keys()))
    return name, _PALETTE_ARRAYS[name].copy()
