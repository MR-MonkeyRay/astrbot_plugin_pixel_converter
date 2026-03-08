"""Help text generation for pixel converter plugin."""

from .palettes import PALETTES, PALETTE_ALIASES
from .fx import STATIC_FX, ANIMATED_FX


# FX descriptions mapping
FX_DESCRIPTIONS: dict[str, str] = {
    "glitch": "故障风动画 (GIF)",
    "crt": "CRT 显示器扫描线效果",
    "dither": "动态抖动纹理动画 (GIF)",
    "cycle": "调色板颜色循环动画 (GIF)",
    "ghost": "残影/拖尾效果 (GIF)",
}


def build_help_text() -> str:
    """Build help text with usage info, palettes, and FX effects."""
    lines = []

    # Basic usage
    lines.append("🎮 像素画插件使用帮助")
    lines.append("")
    lines.append("📝 基本用法")
    lines.append("  命令格式: 像素画 [SIZE] [PALETTE] [FX,FX,...] [@user]")
    lines.append("  别名: pixel, px")
    lines.append("  所有参数均可选，顺序不限")
    lines.append("  - SIZE: 像素大小 (2-5)，数字越大像素越粗")
    lines.append("  - PALETTE: 调色板名称")
    lines.append("  - FX: 特效名称，多个可用逗号或空格分隔")
    lines.append("  - @user: 使用该用户的头像")
    lines.append("")
    lines.append("📌 示例")
    lines.append("  像素画 3 gameboy")
    lines.append("  像素画 4 pico8 glitch @某人")
    lines.append("  像素画 2 nes dither")
    lines.append("")

    # Palette list (dynamic count)
    palette_count = len(PALETTES)
    lines.append(f"🎨 调色板列表 ({palette_count}个)")
    # Build reverse mapping: canonical name -> list of aliases
    alias_map: dict[str, list[str]] = {}
    for alias, canonical in PALETTE_ALIASES.items():
        if canonical not in alias_map:
            alias_map[canonical] = []
        alias_map[canonical].append(alias)

    palette_names = sorted(PALETTES.keys())
    for name in palette_names:
        aliases = alias_map.get(name, [])
        if aliases:
            alias_str = ", ".join(sorted(aliases))
            lines.append(f"  {name} ({alias_str})")
        else:
            lines.append(f"  {name}")
    lines.append("")

    # FX effects list (dynamic count and content)
    fx_count = len(STATIC_FX) + len(ANIMATED_FX)
    lines.append(f"✨ FX 特效列表 ({fx_count}个)")
    lines.append("  静态特效:")
    for fx in sorted(STATIC_FX):
        desc = FX_DESCRIPTIONS.get(fx, "特效")
        lines.append(f"    {fx} - {desc}")
    lines.append("  动画特效:")
    for fx in sorted(ANIMATED_FX):
        desc = FX_DESCRIPTIONS.get(fx, "特效")
        lines.append(f"    {fx} - {desc}")

    return "\n".join(lines)
