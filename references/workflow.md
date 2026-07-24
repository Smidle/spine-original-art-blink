# Spine 原立绘眨眼完整流程

## 目录

1. 目标与适用边界
2. 工具与用途
3. 输入审计
4. 眼部状态制作
5. Spine 工程生成与检查
6. 原生逐帧验收
7. 故障判断
8. 文件保留与交付

## 1. 目标与适用边界

把单张透明原立绘制作成只包含眼睛与眉毛联动的 Spine 第一阶段工程。
最终画面只允许双眼和两条眉毛在批准区域内变化；身体、手脚、头发、
衣服、胸部和挂件逐像素固定。

此流程用于先验收眼睛，不用于完整 Live2D 分层。只有用户确认眨眼
后，才能另立阶段讨论身体切片、骨骼、网格、呼吸和次级运动。

默认眨眼节奏为 30 FPS、3.2 秒：

| 帧 | 状态 |
|---|---|
| 0–34 | 睁眼 |
| 35–36 | 半闭 |
| 37–38 | 全闭 |
| 39–40 | 半闭 |
| 41–96 | 睁眼 |

Spine 的附件关键帧放在 0、34、35、37、39、41、96。附件状态会保持
到下一个关键帧，所以 35–36、37–38、39–40 分别自然形成两帧。

## 2. 工具与用途

### 图像检查

- 使用本地图片查看工具在原始分辨率检查原图、眼睛特写、接触表和
  Spine 导出帧。
- 使用 SHA-256 记录原图和开眼输出，防止误换原画。
- 使用 Pillow 进行 RGBA 裁切、颜色匹配、羽化合成、逐像素差异、
  接触表和 WebP 预览生成。

### 图像生成

- 当没有可靠的闭眼源时，使用 Codex 内置 imagegen 的精确对象编辑
  模式生成闭眼参考。
- 先阅读 imagegen Skill；仅把生成图当眼睑参考。
- 使用类似提示词：

  > 仅将角色的两只眼睛改为自然闭合。保持原始姿势、脸型、肤色、
  > 高光、头发、首饰、服装、手脚、透明背景、画布尺寸、比例和所有
  > 非眼部像素不变。闭眼线必须位于原眼睛中心，线条粗细与原画一致。
  > 禁止重绘、裁切、缩放、旋转、位移、换色、增加矩形皮肤贴片、
  > 妆容、文字或水印。

- 检查生成图全身是否漂移。即使全身发生变化，只要眼部局部可用，
  也只能裁取眼部并通过遮罩合回原图；不能采用生成后的身体。
- 制作 v1 眉毛联动时，分别对已批准的半闭眼图与闭眼图生成参考。
  提示词只允许眉毛随眼皮轻微下压或放松，禁止修改眼睛、肤色、刘海、
  脸型、身体或画布。即使生成图整体重绘，也只能把眉毛批准框内的
  局部像素作为参考。

### Spine

- 优先使用 Spine 原生 CLI 完成导入、工程信息读取和帧导出，降低
  UI 操作误差。
- 使用 Spine Professional 4.3 或与目标项目一致的版本。
- 使用 Computer Use 控制已打开的 Spine UI，检查动画列表、时间轴、
  附件状态和播放效果。
- 如果 Computer Use 无法枚举 Spine，使用 `open -a` 打开工程并依靠
  CLI 做确定性导入、导出和信息检查。
- 在 macOS 上把 JSON、图片目录、Spine 工程和导出目录放在普通工作
  目录。不要从 `/tmp` 或 `/private/tmp` 运行图片导出；实测 Spine
  可能生成 97 个文件名正确但内容为 0 字节的 PNG。

### 文件和命令

- 使用 `rg`/`find` 做只读文件审计。
- 使用 `apply_patch` 修改文本脚本和配置。
- 清理旧文件前列出精确目标；默认移入唯一命名的废纸篓目录。
- 如果系统 Python 缺少 Pillow，加载工作区依赖并使用其中的 Python。

## 3. 输入审计

1. 找到未经切片、未经变形的透明原立绘。
2. 查看整张图，确认头、双手、双腿和脚完整连接，没有旧贴图重影。
3. 记录：
   - 绝对路径；
   - 像素尺寸；
   - 色彩模式；
   - 是否包含 Alpha；
   - SHA-256。
4. 创建独立的 `images-blink-only` 目录，不覆盖原图。
5. 把之前工程和预览列出来。此时只审计，不立即删除。

## 4. 眼部状态制作

### 4.1 定义坐标

1. 以原图像素坐标定义左右眼的 `target_box`：
   `[x1, y1, x2, y2]`。
2. 框应覆盖眼睑、睫毛和眼球开口，并留少量皮肤用于颜色匹配。
3. 不要把眉毛、鼻梁、刘海或脸缘纳入框内。
4. 为每只眼定义局部 `mask_polygon`。坐标相对于眼框左上角。
5. 遮罩只覆盖需要替换的眼睑/眼球开口，羽化半径通常
   `0.5–1.0 px`。

### 4.2 准备半闭眼

1. 优先采用用户已经确认正确的半闭眼帧或画师绘制的半闭眼。
2. 从正确帧按目标框原尺寸裁取。
3. 保持画布缩放和眼睛位置不变。
4. 禁止为了“看起来合适”而缩放眼睛。
5. 分别保存左右眼半闭源；文件应只包含目标框大小，或在配置中提供
   对应 `half_source_box`。

### 4.3 准备闭眼参考

1. 优先使用画师绘制的闭眼。
2. 没有闭眼源时调用 imagegen，要求只改变双眼。
3. 查看生成参考，重点检查：
   - 闭眼线中心是否对应原瞳孔中心；
   - 两眼大小是否与原画透视关系一致；
   - 睫毛颜色、线宽和方向；
   - 眼皮肤色是否与半闭状态一致；
   - 是否出现矩形皮肤块或背景棋盘被烘焙。
4. 在配置中填写 `closed_source_box`。该框输出尺寸必须与
   `target_box` 完全相同。

### 4.4 配置并生成

1. 复制 `blink-config.example.json` 到项目目录。
2. 修改每只眼的框、源文件和遮罩。
3. 让配置中的相对路径以配置文件目录为基准。
4. 运行：

```bash
python3 scripts/build_eye_states.py \
  --original /path/original.png \
  --closed-reference /path/closed-reference.png \
  --config /path/blink-config.json \
  --output-dir /path/images-blink-only
```

脚本执行以下确定性动作：

1. 逐字节复制原图为 `character_open.png`。
2. 在原图副本上原坐标贴入半闭眼。
3. 从闭眼参考裁取同尺寸闭眼。
4. 用半闭眼边缘的皮肤样本进行 RGB 中位数色差匹配。
5. 只在眼部多边形内以小半径羽化闭眼。
6. 输出 `character_half.png` 和 `character_closed.png`。
7. 验证开眼哈希与原图一致。
8. 验证半闭、闭眼的所有差异都位于两个眼框内。
9. 输出 `eye-state-qa.json`。

### 4.5 人工检查

分别查看全身和 200%–800% 眼部特写：

- 三张图画布尺寸、人物位置、Alpha 完全一致；
- 半闭和闭眼没有脸部整体位移；
- 眼睛没有变大、变小或左右漂移；
- 没有肤色方块、色边、黑边和棋盘纹；
- 头发没有被眼部贴图覆盖；
- 非眼部像素没有任何改变。

### 4.6 生成 v1 眉毛参考

只在眼睛三状态已经通过验收后开始眉毛：

1. 以已批准的 `character_half.png` 生成半闭眼眉毛参考。
2. 以已批准的 `character_closed.png` 生成闭眼眉毛参考。
3. 使用 imagegen 精确对象编辑模式，要求：
   - 半闭：眉毛轻微下压；
   - 全闭：眉毛继续轻微下压并放松；
   - 眉毛粗细、颜色和角色神态保持原画风格；
   - 眼睛状态、肤色、刘海、脸型、饰品、身体、Alpha 和画布不变。
4. 把生成结果保存为完整画布参考，但禁止直接替换正式贴图。
5. 在原分辨率确认两张参考里的眉毛位置可用。生成图其他区域即使看似
   正确，也一律不采用。

### 4.7 配置并生成 v1 审核候选

复制 `references/brow-config-v1.example.json`，为每条眉毛设置：

- `box`：完整画布坐标；
- `polygon`：相对于框左上角的羽化多边形；
- `feather_radius`：默认约 1 px；
- `review_crop`：审核接触表与循环预览的脸部范围。

运行：

```bash
python3 scripts/build_eyebrow_states_v1.py \
  --open /path/eye-only/character_open.png \
  --half /path/eye-only/character_half.png \
  --closed /path/eye-only/character_closed.png \
  --half-reference /path/generated-half-brow-reference.png \
  --closed-reference /path/generated-closed-brow-reference.png \
  --config /path/brow-config-v1.json \
  --output-dir /path/review-eyebrow-v1
```

脚本按 v1 流程执行：

1. 完整保留已批准的开眼、半闭和闭眼基底。
2. 在每个眉毛框外环采样基底与生成参考的 RGB 中位数色差。
3. 对生成参考的眉毛局部做颜色平移。
4. 只在批准的眉毛羽化多边形内合成。
5. 开眼候选逐字节复制原开眼图。
6. 输出半闭、闭眼候选、34–41 帧接触表、无损 WebP 循环和
   `eyebrow-blink-review-qa.json`。
7. 报告必须保持：
   - `formal_project_modified: false`
   - `skill_modified: false`
   - 两个状态的 `changed_outside_brow_regions: false`

### 4.8 v1 人工审核门

在修改正式工程之前向用户展示：

1. 34–41 帧接触表；
2. 循环动态预览；
3. 半闭与闭眼相对眼部基底的差异框；
4. 明确声明正式 `.spine`、正式贴图和 Skill 尚未修改。

重点检查眉毛幅度、左右透视、眉毛与刘海交界、旧眉位置、肤色闪变和
生成参考带来的局部色差。用户未明确批准时，只能继续修改独立审核
目录；不得写入正式工程或 Skill。

### 4.9 批准后写入正式工程

获得明确批准后：

1. 把眼部基底复制到独立 `source-eye-states` 目录，避免以后对已合成
   的眉毛重复应用 v1 脚本。
2. 保持正式 `character_open.png` 字节不变。
3. 用批准的 `candidate_half_brow.png` 和
   `candidate_closed_brow.png` 更新正式半闭/闭眼贴图。
4. 重新生成 Spine JSON 并重新导入 `.spine`，不能只依赖旧工程缓存。
5. 重新导出全部 97 帧，再执行眼睛+眉毛联合区域的原生验收。

## 5. Spine 工程生成与检查

### 5.1 生成导入 JSON

运行：

```bash
python3 scripts/build_spine_blink_json.py \
  --images-dir /path/images-blink-only \
  --output /path/character-blink-only.json \
  --skeleton-name character-blink-only \
  --fps 30 --duration 3.2 \
  --open-start 34 --half-in 35 --closed-in 37 \
  --half-out 39 --open-out 41
```

生成结构必须是：

- 1 根 `root`；
- 1 个 `character` 插槽；
- 3 个完整画布附件：`character_open`、`character_half`、
  `character_closed`；
- 1 个 `blink_only` 附件时间轴；
- root 无位移、旋转、缩放、剪切或变形时间轴。

### 5.2 导入工程

```bash
"/Applications/Spine.app/Contents/MacOS/Spine" \
  -i /path/character-blink-only.json \
  -o /path/character-blink-only.spine -r
```

如果输出工程已存在，先把旧工程移入废纸篓或使用新的明确文件名，避免
误导入到错误骨架。

### 5.3 CLI 信息检查

```bash
"/Applications/Spine.app/Contents/MacOS/Spine" \
  -i /path/character-blink-only.spine
```

确认输出为 1 bone、1 slot、1 animation，并核对画布尺寸。

### 5.4 UI 检查

1. 打开工程。
2. 切换到 Animate/动画模式。
3. 在动画列表选择 `blink_only`。
4. 确保动画名称左侧的小圆点处于启用状态。
5. 定位 34–41 帧并逐帧查看。
6. 按播放检查完整循环。
7. 展开 root，确认没有 transform 时间轴。
8. 展开 character 插槽，确认只有附件切换关键帧。

## 6. 原生逐帧验收

### 6.1 导出

使用 Spine PNG 动画导出设置：

- animation: `blink_only`
- FPS: 30
- last frame: true
- transparent background
- render images: true
- render bones/others: false
- smoothing: 8
- scale: 100，或记录使用的固定比例

```bash
mkdir -p /path/native-frames

"/Applications/Spine.app/Contents/MacOS/Spine" \
  -i /path/character-blink-only.spine \
  -o /path/native-frames \
  -e /path/export-png.json
```

### 6.2 坐标换算

把原图的两个眼框和两个眉毛框分别换算到 Spine 导出尺寸。例如导出
比例为 75%，则所有坐标乘以 0.75，并为抗锯齿增加约 2–4 px 边界。
不要为了方便把允许框扩大到脸部或头发。

### 6.3 自动验证

```bash
python3 scripts/validate_blink_export.py \
  --frames-dir /path/native-frames \
  --report /path/qa-report.json \
  --contact /path/native-contact.png \
  --preview /path/blink.webp \
  --fps 30 --duration 3.2 \
  --open-start 34 --half-in 35 --closed-in 37 \
  --half-out 39 --open-out 41 \
  --allowed-box EYE_LEFT_X1 EYE_LEFT_Y1 EYE_LEFT_X2 EYE_LEFT_Y2 \
  --allowed-box EYE_RIGHT_X1 EYE_RIGHT_Y1 EYE_RIGHT_X2 EYE_RIGHT_Y2 \
  --allowed-box BROW_LEFT_X1 BROW_LEFT_Y1 BROW_LEFT_X2 BROW_LEFT_Y2 \
  --allowed-box BROW_RIGHT_X1 BROW_RIGHT_Y1 BROW_RIGHT_X2 BROW_RIGHT_Y2
```

验证器检查：

- 帧数量为 `duration × fps + 1`；
- 所有帧尺寸一致；
- 0、34、41、末帧开眼一致；
- 35=36、37=38、39=40；
- 所有帧在批准的眼睛与眉毛框外与第 0 帧逐像素一致；
- 状态转换差异框位于批准框内；
- 输出 34–41 帧接触表；
- 输出无损 WebP 循环预览；
- 验证导出 PNG 可由 Pillow 正常解码，不能只统计文件数量；
- 任一布尔条件失败即返回非零退出码。

### 6.4 人工原生检查

查看接触表和完整闭眼帧：

- 34–36 延续已确认状态；
- 37–38 不偏移、不变色；
- 39–41 平滑返回；
- 双手、双脚完整；
- 腿宽不变化；
- 手臂、头发和衣服没有重影；
- 循环首尾不跳动。

## 7. 故障判断

| 现象 | 常见原因 | 处理 |
|---|---|---|
| 闭眼出现矩形肤色块 | 使用了整块矩形贴图 | 缩小遮罩，只在眼睑多边形内合成 |
| 37–38 帧位置偏移 | 眼框、源框或附件中心不一致 | 校正源框；禁止用 Spine 整体位移补偿 |
| 闭眼颜色不同 | AI 参考肤色漂移 | 用半闭源外环做颜色中位数匹配 |
| 眉毛附近肤色或刘海闪变 | 把生成参考整块合回 | 回到眼部基底，只在眉毛羽化多边形内重新生成 v1 候选 |
| 眉毛候选重复叠加 | 正式贴图被当成眼部基底再次运行 | 使用保留的 `source-eye-states` 重建候选 |
| 眼睛忽大忽小 | 对眼睛做了缩放 | 恢复原尺寸裁取，重新绘制状态 |
| 手脚或腿变化 | 误用了生成整图或身体附件 | 以原图重建三状态并做眼框外像素检查 |
| 播放无反应 | 动画未选择或左侧圆点未启用 | 选择 `blink_only` 并启用小圆点 |
| 接触表正确、Spine 不正确 | 导入了旧工程或图片路径错误 | 用新文件名重新导入并检查 images 路径 |
| Pillow `getbbox` 漏报 RGBA 差异 | 只检查 Alpha 或单通道 | 合并 RGBA 四通道差异后取 bbox |

## 8. 文件保留与交付

保留：

- 原立绘；
- 两张半闭眼源；
- 闭眼生成/绘制参考；
- v1 半闭与闭眼眉毛生成参考；
- 眼框配置；
- 眉毛配置；
- 眼部基底三状态；
- 批准后的眼睛+眉毛三状态；
- 眼部与眉毛状态生成脚本、候选审核 QA；
- Spine 导入 JSON、工程和导出设置；
- 原生帧、接触表、WebP 和 QA 报告。

清理：

- 旧身体切片、遮罩、错误附件；
- 旧骨骼工程和备份；
- 旧 idle 导出帧；
- 诊断用但不再支撑最终结果的中间图。

清理前精确列出目标；默认移动到唯一命名的废纸篓目录并报告恢复
位置。最终向用户报告动画名、帧表、自动验收结果，以及“尚未开始
身体动画”。
