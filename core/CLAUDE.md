# Core 模块

[根目录](../CLAUDE.md) > **core**

像素化核心引擎，与 AstrBot 框架解耦（仅 `renderer.py` 使用 `astrbot.api.logger`）。

## 公共 API

| 函数 | 位置 | 说明 |
| --- | --- | --- |
| `process_image(url, options, config)` | `renderer.py` | 完整渲染管道，返回 `RenderResult` |
| `cleanup_file(path)` | `renderer.py` | 延迟清理临时文件 |
| `parse_options(...)` | `parser.py` | 解析命令参数为 `PixelOptions` |
| `extract_image_url(...)` | `sources.py` | 提取图片 URL（消息图片 > @头像 > 发送者头像） |
| `build_help_text()` | `helptext.py` | 生成帮助文本 |

## FX 特效

| 特效 | 类型 | 说明 |
| --- | --- | --- |
| `crt` | 静态 | CRT 扫描线 |
| `glitch` | 动画 | RGB 通道偏移 + 随机带位移 |
| `dither` | 动画 | 亮度扰动 + Floyd-Steinberg 抖动 |
| `cycle` | 动画 | 调色板索引旋转 |
| `ghost` | 动画 | 透明度衰减偏移叠加 |

多个动画 FX 只取第一个生效（避免帧合并复杂度）。

## 设计决策

- **cycle 使用原始图像**：cycle 基于调色板索引映射旋转颜色，静态 FX（如 CRT）会引入调色板外颜色导致索引不准
- **dither 两阶段策略**：先算每帧亮度偏移的唯一值集合，每个唯一偏移只做一次抖动计算，按帧序复用结果
- **并发控制**：`renderer.py` 通过 `asyncio.Semaphore` 限制同时渲染数（默认 8）
