<p align="right">
  简体中文 | <a href="./README.en.md">English</a>
</p>

# Spine 原立绘眼眉眨眼

从一张完整角色立绘制作高保真的眼睛与眉毛联动 Spine 眨眼动画，并用候选审核和 Spine 原生导出帧证明所有未批准区域保持逐像素固定。

<p align="center">
  <img src="./assets/v1-eye-eyebrow-blink.webp" alt="Spine v1 eye-and-eyebrow blink example" width="384" />
</p>

## 本次版本更新：v1 眼眉联动

- 眨眼由“仅眼睛变化”升级为眼睑与左右眉毛自然联动；
- 正式写入前新增候选审核门：先交付开眼、半闭、闭眼、接触表和循环预览，得到明确批准后才能更新 `.spine`；
- 新增 `build_eyebrow_states_v1.py` 和 `brow-config-v1.example.json`，可复现 v1 的局部眉毛处理；
- 原生导出校验支持重复使用 `--allowed-box`，可分别批准眼睛与眉毛区域，同时保留旧的 `--allowed-eye-box` 参数；
- 新示例经过 97 帧、30 FPS、3.2 秒原生 QA：身体、四肢、头发和服装没有切换或移动。

## 适用场景

- 从单张角色立绘开始制作 Spine 或 Live2D 风格动画；
- 先单独完成并验收眼睛与眉毛联动，再进入呼吸、头发和身体动画；
- 修复闭眼位置偏移、眉毛断裂、肤色矩形、色边、重影或全身漂移；
- 需要可复现的 Spine 工程、原生 PNG 帧和像素级 QA 报告。

## 核心原则

- 原立绘始终是唯一事实来源；
- `character_open.png` 必须与工作源图逐字节一致；
- 睁眼、半闭和闭眼状态使用相同尺寸、位置和完整画布；
- 只允许批准的左右眼与左右眉毛区域发生像素变化；
- 生成式图像只能作为局部眼睑或眉毛参考，不能替换角色身体；
- 眉毛候选必须先审核，未经明确批准不得覆盖正式贴图或 Spine 工程；
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
使用 $spine-original-art-blink 从这张原立绘制作眼睛与眉毛联动的 Spine 眨眼动画，先完成候选审核，再更新正式工程并完成原生逐帧验收。
```

技能会先完整读取 [`references/workflow.md`](./references/workflow.md)，再执行：

1. 审计原图尺寸、模式、Alpha 与 SHA-256；
2. 定义左右眼框、眉毛框和局部羽化多边形；
3. 准备半闭眼、闭眼和眉毛联动的局部参考；
4. 生成三张完整画布候选状态图；
5. 交付接触表、循环预览和局部像素 QA，等待明确批准；
6. 批准后才把候选晋升为正式贴图并构建最小 `blink_only` Spine 工程；
7. 以 30 FPS 导出 0–96 帧原生 PNG；
8. 验证所有未批准像素固定、状态重复一致、首尾循环无跳变；
9. 交付 Spine 工程、源链、接触表、动画预览和 QA 报告。

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
│   └── v1-eye-eyebrow-blink.webp
├── references/
│   ├── blink-config.example.json
│   ├── brow-config-v1.example.json
│   └── workflow.md
└── scripts/
    ├── build_eye_states.py
    ├── build_eyebrow_states_v1.py
    ├── build_spine_blink_json.py
    └── validate_blink_export.py
```

## 验收条件

最终结果必须同时满足：

- 开眼输出哈希等于原图哈希；
- 三个状态尺寸、Alpha、比例与位置一致；
- 所有差异框位于批准的眼睛或眉毛区域；
- Spine 原生导出的每一帧在批准区域外逐像素一致；
- 帧序为睁眼 → 半闭 → 全闭 → 半闭 → 睁眼；
- 循环首尾一致；
- root 没有 transform 时间轴；
- 目检没有矩形贴片、色边、重复边缘、眉毛断裂、原眉位置白块、眼睑偏移、脸部漂移或抗锯齿光晕。

示例 WebP 展示本次 v1 眼眉联动流程的审核结果，仅用于说明该 Skill 的最终效果。
