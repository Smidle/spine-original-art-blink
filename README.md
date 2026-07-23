<p align="right">
  简体中文 | <a href="./README.en.md">English</a>
</p>

# Spine 原立绘眨眼

从一张完整角色立绘制作高保真、只改变双眼的 Spine 眨眼动画，并用 Spine 原生导出帧证明身体、头发、服装、四肢、饰品和背景保持逐像素固定。

<p align="center">
  <img src="./assets/blink-example.gif" alt="Spine blink-only example" width="384" />
</p>

## 适用场景

- 从单张角色立绘开始制作 Spine 或 Live2D 风格动画；
- 先单独完成并验收眨眼，再进入呼吸、头发和身体动画；
- 修复闭眼位置偏移、肤色矩形、色边、重影或全身漂移；
- 需要可复现的 Spine 工程、原生 PNG 帧和像素级 QA 报告。

## 核心原则

- 原立绘始终是唯一事实来源；
- `character_open.png` 必须与工作源图逐字节一致；
- 睁眼、半闭和闭眼状态使用相同尺寸、位置和完整画布；
- 只允许批准的左右眼框发生像素变化；
- 生成式图像只能作为局部眼睑参考，不能替换角色身体；
- Spine 工程只包含 1 根骨骼、1 个插槽、3 个附件和 1 条附件时间轴；
- 通过眨眼验收后立即停止，不自动开始呼吸或身体动画。

## 安装

从独立仓库安装：

```bash
npx skills add Smidle/spine-original-art-blink
```

在交互式列表中选择需要安装到的智能体。

也可以克隆仓库后，把本目录直接复制到 Codex 的个人技能目录：

```bash
git clone https://github.com/Smidle/spine-original-art-blink.git
cp -R spine-original-art-blink ~/.codex/skills/
```

## 使用

在 Codex 中提供一张角色原立绘，然后调用：

```text
使用 $spine-original-art-blink 从这张原立绘制作只改变眼睛的 Spine 眨眼动画，并完成原生逐帧验收。
```

技能会先完整读取 [`references/workflow.md`](./references/workflow.md)，再执行：

1. 审计原图尺寸、模式、Alpha 与 SHA-256；
2. 定义左右眼框和局部羽化多边形；
3. 准备半闭眼与闭眼局部参考；
4. 生成三张完整画布状态图；
5. 构建最小 `blink_only` Spine 工程；
6. 以 30 FPS 导出 0–96 帧原生 PNG；
7. 验证所有非眼部像素固定、状态重复一致、首尾循环无跳变；
8. 交付 Spine 工程、源链、接触表、动画预览和 QA 报告。

## 默认帧表

| 帧 | 状态 |
|---|---|
| 0–34 | 睁眼 |
| 35–36 | 半闭 |
| 37–38 | 全闭 |
| 39–40 | 半闭 |
| 41–96 | 睁眼 |

默认参数为 30 FPS、3.2 秒，附件关键帧位于 0、34、35、37、39、41、96。

## 依赖

- Spine Professional 4.3，或与目标工程一致的版本；
- Python 3；
- Pillow；
- macOS 上的 Spine CLI 默认路径：

```text
/Applications/Spine.app/Contents/MacOS/Spine
```

如果系统 Python 没有 Pillow，技能会优先使用 Codex 工作区提供的 Python 运行时。

## 目录

```text
spine-original-art-blink/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── assets/
│   └── blink-example.gif
├── references/
│   ├── blink-config.example.json
│   └── workflow.md
└── scripts/
    ├── build_eye_states.py
    ├── build_spine_blink_json.py
    └── validate_blink_export.py
```

## 验收条件

最终结果必须同时满足：

- 开眼输出哈希等于原图哈希；
- 三个状态尺寸、Alpha、比例与位置一致；
- 所有差异框位于批准的眼部区域；
- Spine 原生导出的每一帧在眼框外逐像素一致；
- 帧序为睁眼 → 半闭 → 全闭 → 半闭 → 睁眼；
- 循环首尾一致；
- root 没有 transform 时间轴；
- 目检没有矩形贴片、色边、重复边缘、眼睑偏移、脸部漂移或抗锯齿光晕。

示例 GIF 使用一名完全原创的日系幻想角色制作，仅用于展示该眨眼工作流的最终效果。
