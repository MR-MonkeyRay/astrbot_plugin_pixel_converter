"""
Palette definitions for pixel art conversion.
Contains 18 classic color palettes with utility functions.
"""

from typing import Final

import numpy as np
from numpy.typing import NDArray


# Raw palette data: name -> list of RGB tuples
PALETTES: Final[dict[str, list[tuple[int, int, int]]]] = {
    # 1. sora (12 colors)
    "sora": [
        (0, 0, 0),
        (8, 14, 32),
        (22, 32, 60),
        (36, 54, 92),
        (52, 76, 120),
        (72, 104, 152),
        (100, 140, 184),
        (168, 148, 40),
        (220, 200, 90),
        (248, 236, 160),
        (255, 252, 228),
        (224, 160, 128),
    ],
    # 2. gameboy (4 colors)
    "gameboy": [
        (15, 56, 15),
        (48, 98, 48),
        (139, 172, 15),
        (155, 188, 15),
    ],
    # 3. nes (16 colors)
    "nes": [
        (0, 0, 0),
        (252, 252, 252),
        (188, 188, 188),
        (124, 124, 124),
        (228, 0, 8),
        (248, 56, 0),
        (248, 184, 0),
        (172, 124, 0),
        (0, 184, 0),
        (88, 216, 84),
        (0, 168, 68),
        (0, 232, 216),
        (0, 120, 248),
        (104, 68, 252),
        (216, 0, 204),
        (248, 120, 88),
    ],
    # 4. cga (4 colors)
    "cga": [
        (0, 0, 0),
        (85, 255, 255),
        (255, 85, 255),
        (255, 255, 255),
    ],
    # 5. c64 (16 colors)
    "c64": [
        (0, 0, 0),
        (255, 255, 255),
        (136, 0, 0),
        (170, 255, 238),
        (204, 68, 204),
        (0, 204, 85),
        (0, 0, 170),
        (238, 238, 119),
        (136, 68, 0),
        (102, 68, 0),
        (255, 119, 119),
        (51, 51, 51),
        (119, 119, 119),
        (170, 255, 102),
        (0, 136, 255),
        (187, 187, 187),
    ],
    # 6. pico8 (16 colors)
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
    # 7. sweetie16 (16 colors)
    "sweetie16": [
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
        (244, 244, 244),
        (148, 176, 194),
        (86, 108, 134),
        (51, 60, 87),
    ],
    # 8. pastel (12 colors)
    "pastel": [
        (255, 179, 186),
        (255, 223, 186),
        (255, 255, 186),
        (186, 255, 201),
        (186, 225, 255),
        (218, 186, 255),
        (255, 186, 243),
        (255, 255, 255),
        (200, 200, 200),
        (120, 120, 120),
        (60, 60, 60),
        (0, 0, 0),
    ],
    # 9. mono (9 colors)
    "mono": [
        (0, 0, 0),
        (34, 34, 34),
        (68, 68, 68),
        (102, 102, 102),
        (136, 136, 136),
        (170, 170, 170),
        (204, 204, 204),
        (238, 238, 238),
        (255, 255, 255),
    ],
    # 10. sepia (9 colors)
    "sepia": [
        (44, 28, 6),
        (72, 52, 18),
        (102, 78, 36),
        (138, 110, 60),
        (170, 142, 88),
        (198, 176, 122),
        (222, 204, 160),
        (242, 230, 200),
        (255, 245, 230),
    ],
    # 11. sunset (10 colors)
    "sunset": [
        (13, 2, 33),
        (44, 6, 69),
        (87, 10, 82),
        (140, 15, 75),
        (191, 36, 51),
        (224, 80, 29),
        (240, 134, 28),
        (248, 190, 53),
        (255, 237, 120),
        (255, 255, 230),
    ],
    # 12. ocean (10 colors)
    "ocean": [
        (0, 20, 40),
        (0, 40, 80),
        (0, 80, 120),
        (0, 120, 160),
        (0, 160, 200),
        (40, 200, 220),
        (80, 220, 240),
        (160, 240, 255),
        (200, 248, 255),
        (255, 255, 255),
    ],
    # 13. earth (10 colors)
    "earth": [
        (34, 32, 28),
        (69, 60, 44),
        (107, 95, 70),
        (140, 128, 96),
        (168, 156, 120),
        (96, 128, 56),
        (64, 96, 48),
        (140, 96, 64),
        (192, 160, 112),
        (220, 200, 168),
    ],
    # 14. sakura (12 colors)
    "sakura": [
        (43, 30, 26),
        (80, 56, 44),
        (52, 80, 48),
        (120, 164, 84),
        (156, 48, 72),
        (200, 80, 108),
        (232, 140, 164),
        (248, 196, 208),
        (255, 232, 238),
        (255, 255, 255),
        (176, 164, 200),
        (140, 180, 220),
    ],
    # 15. cyber (12 colors)
    "cyber": [
        (8, 4, 16),
        (20, 8, 40),
        (48, 12, 64),
        (100, 20, 100),
        (180, 20, 100),
        (255, 40, 120),
        (255, 140, 200),
        (10, 40, 80),
        (0, 160, 200),
        (80, 240, 255),
        (200, 160, 255),
        (255, 255, 255),
    ],
    # 16. horror (12 colors)
    "horror": [
        (0, 0, 0),
        (24, 4, 4),
        (60, 8, 8),
        (120, 16, 16),
        (180, 20, 20),
        (220, 60, 40),
        (40, 44, 16),
        (72, 80, 32),
        (48, 24, 48),
        (80, 72, 68),
        (200, 180, 140),
        (240, 220, 190),
    ],
    # 17. riso (3 colors)
    "riso": [
        (0, 50, 255),
        (232, 0, 28),
        (245, 240, 232),
    ],
    # 18. cmyk (4 colors)
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
