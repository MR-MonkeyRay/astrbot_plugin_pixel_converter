# Pixel Converter

AstrBot 插件 - 将图片转换为像素风格

## 功能特性

- 18 种像素调色板（Game Boy、NES、PICO-8 等）
- 5 种视觉特效（故障风、CRT、抖动、动画）
- 支持消息图片、@用户头像、自己头像
- 可配置默认参数

## 安装

```bash
git clone https://github.com/MR-MonkeyRay/astrbot_plugin_pixel_converter.git
```

将项目目录放入 AstrBot 的 `addons/plugins/` 下，重启 AstrBot。

## 使用方法

**命令**：`像素画` / `pixel` / `px`

**格式**：`像素画 [SIZE] [调色板] [FX,FX,...] [@用户]`

所有参数可选，顺序无关。SIZE 和调色板不填则使用配置默认值或随机；FX 不填则不加特效。

**FX 写法**：逗号分隔 `glitch,crt` 或空格分开 `glitch crt` 均可

**图片来源优先级**：
1. 消息中的图片（含引用/回复图片）
2. @用户的头像
3. 发送者自己的头像
4. 以上都没有 → 等待模式（60秒内发送图片继续处理）

**SIZE**：2-5，数字越大像素块越粗

## 调色板

| 调色板 | 色数 | 风格 | 别名 |
|--------|------|------|------|
| sora | 12 | 深蓝到暖黄 | - |
| gameboy | 4 | 经典 Game Boy 绿 | gb |
| nes | 16 | 8-bit 任天堂 | nintendo |
| cga | 4 | 早期 PC CGA | - |
| c64 | 16 | Commodore 64 | - |
| pico8 | 16 | PICO-8 幻想主机 | pico |
| sweetie16 | 16 | 现代像素画 | sweetie |
| pastel | 12 | 柔和粉彩 | - |
| mono | 9 | 黑白灰阶 | bw, monochrome |
| sepia | 9 | 复古棕褐 | - |
| sunset | 10 | 日落渐变 | - |
| ocean | 10 | 海洋蓝 | - |
| earth | 10 | 大地色 | - |
| sakura | 12 | 樱花粉 | - |
| cyber | 12 | 赛博霓虹 | - |
| horror | 12 | 恐怖暗红 | - |
| riso | 3 | 孔版印刷 | - |
| cmyk | 4 | 四色印刷 | - |

## FX 特效

**静态（PNG）**：
- `crt` - CRT 扫描线

**动画（GIF）**：
- `glitch` - 故障风动画
- `dither` - 动态抖动纹理动画
- `cycle` - 调色板轮转动画
- `ghost` - 残影动画

多个特效用逗号分隔，如 `crt`。多个动画 FX 同时指定时，仅第一个生效。

## 配置项

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| default_size | int | 3 | 默认像素大小(2-5)，留空随机 |
| default_palette | string | "" | 默认调色板，留空随机 |
| default_fx | string | "" | 默认FX，留空则不加特效，多个用逗号分隔 |
| max_image_size | int | 2048 | 最大图片边长(px) |
| gif_frames | int | 8 | 动画GIF帧数 |
| gif_duration | int | 100 | GIF每帧时长(ms) |

## 示例

```
像素画                     # 自己头像，随机调色板
像素画 gameboy             # 自己头像，Game Boy 调色板
像素画 3 nes crt           # SIZE=3, NES 调色板, CRT特效
像素画 cyber glitch @某人  # 某人头像，赛博调色板，故障GIF
像素画 pico8 dither        # PICO-8调色板，抖动GIF
像素画 mono cycle          # 黑白调色板，轮转GIF
px sakura                  # 樱花调色板
```

配合图片使用：
```
[图片] 像素画 pico8 glitch  # 输出故障风GIF动画
像素画 nes @某人
```
