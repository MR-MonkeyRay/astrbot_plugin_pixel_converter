"""Image source extraction logic for pixel converter plugin."""

from typing import Any

# QQ Avatar URL template
AVATAR_URL_TEMPLATE = "https://q1.qlogo.cn/g?b=qq&nk={qq}&s=640"


def find_image_in_chain(message_chain: list[Any], Comp_module) -> str | None:
    """
    Recursively find first image URL in message chain.

    Args:
        message_chain: List of message components
        Comp_module: astrbot.api.message_components module

    Supports:
        - Direct image in current message
        - Image inside reply/quote message chain

    Returns:
        Image URL or None
    """
    if not message_chain:
        return None

    for comp in message_chain:
        if isinstance(comp, Comp_module.Image):
            if comp.url:
                return comp.url
            if comp.file and str(comp.file).startswith(
                ("http://", "https://", "file:///")
            ):
                return comp.file

        if isinstance(comp, Comp_module.Reply):
            nested_chain = getattr(comp, "chain", None)
            nested_url = find_image_in_chain(nested_chain, Comp_module)
            if nested_url:
                return nested_url

    return None


def extract_image_url(
    message_chain: list[Any],
    at_qq: str | None,
    sender_id: str | None,
    Comp_module,
) -> str | None:
    """
    Extract image URL from message chain, following priority order.

    Args:
        message_chain: List of message components
        at_qq: @mentioned user's QQ number
        sender_id: Message sender's ID
        Comp_module: astrbot.api.message_components module

    Priority:
        1. Image in current message or replied message
        2. @user's avatar URL
        3. Sender's avatar URL (fallback)

    Returns:
        Image URL or None
    """
    # Priority 1: Image in current message or replied message
    image_url = find_image_in_chain(message_chain, Comp_module)
    if image_url:
        return image_url

    # Priority 2: @user avatar
    if at_qq:
        return AVATAR_URL_TEMPLATE.format(qq=at_qq)

    # Priority 3: Sender's avatar (fallback)
    if sender_id:
        return AVATAR_URL_TEMPLATE.format(qq=sender_id)

    return None


def extract_image_url_from_chain(
    message_chain: list[Any], Comp_module
) -> str | None:
    """
    Extract image URL from message chain, including reply images.

    Args:
        message_chain: List of message components
        Comp_module: astrbot.api.message_components module

    Returns:
        Image URL or None
    """
    return find_image_in_chain(message_chain, Comp_module)
