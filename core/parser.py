"""Command parsing logic for pixel converter plugin."""

import random

from .types import PixelOptions
from .palettes import (
    list_palettes,
    is_valid_palette,
    normalize_palette_name,
)
from .fx import normalize_fx_names, ALL_FX


def parse_options(
    message_str: str,
    at_qq_list: list[str] | None,
    default_size: int,
    default_palette: str,
    default_fx: str,
) -> PixelOptions:
    """
    Parse command options from message string.

    Args:
        message_str: The raw message string
        at_qq_list: List of @mentioned QQ numbers (first one used)
        default_size: Default pixel size from config
        default_palette: Default palette name from config
        default_fx: Default FX string from config

    Returns:
        PixelOptions with parsed values
    """
    tokens = message_str.strip().split()[1:]  # Skip command itself

    size = None
    palette = None
    fx_list = None
    help_requested = False

    for token in tokens:
        token = token.strip()
        if not token:
            continue
        # Check for help keyword
        if token.lower() in ("help", "帮助"):
            help_requested = True
            break
        # Check for size (2-5)
        if token.isdigit() and 2 <= int(token) <= 5:
            size = int(token)
            continue
        # Check for palette name
        if is_valid_palette(token):
            palette = normalize_palette_name(token)
            continue
        # Check for FX names (can be comma-separated or individual tokens)
        potential_fx = []
        for fx_token in token.split(","):
            fx_token = fx_token.strip().lower()
            if fx_token in ALL_FX:
                potential_fx.append(fx_token)
        if potential_fx:
            if fx_list is None:
                fx_list = []
            fx_list.extend(potential_fx)

    # Early return for help request
    if help_requested:
        return PixelOptions(size=0, palette="", fx_list=[], at_qq=None, help=True)

    # Extract @user (first one)
    at_qq = at_qq_list[0] if at_qq_list else None

    # Apply defaults from config if not specified
    if size is None:
        size = (
            default_size
            if 2 <= default_size <= 5
            else random.randint(2, 5)
        )

    if palette is None:
        if default_palette and is_valid_palette(default_palette):
            palette = normalize_palette_name(default_palette)
        else:
            palette = random.choice(list_palettes())

    if fx_list is None or len(fx_list) == 0:
        if default_fx:
            fx_list = normalize_fx_names(default_fx.split(","))
        else:
            fx_list = []

    return PixelOptions(
        size=size,
        palette=palette,
        fx_list=fx_list,
        at_qq=at_qq,
        help=False,
    )
