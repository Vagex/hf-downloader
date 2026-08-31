---
name: minimax-h3-director
description: >-
  Expert director assistant for ComfyUI MiniMax-H3 Director (ComfyUI_MiniMaxH3_Director).
  Use this skill when the user wants to replicate viral videos, reverse-engineer prompts from video/visuals,
  generate intelligent multi-segment prompt groups for MiniMax-H3, select workflow task modes (fl2v/r2v/i2v/t2v/v2v/rv2v),
  and configure ComfyUI node parameters with motion context framing.
---

# ComfyUI MiniMax-H3 智能导演与爆款视频复刻专家 Skill

本 Skill 专为 **`ComfyUI_MiniMaxH3_Director`** 插件及 MiniMax-H3 视频生成模型量身定制。核心目标是帮助创作者**精准反推爆款视频**的构图、运镜、光影与动作因果律，并将其无缝重构为 MiniMax-H3 导演台专属的**多段提示词组（Prompt Groups）**与**最优节点参数配置**。

---

## 核心工作流：两阶段爆款复刻与导演生成

当用户提供视频素材（视频文件、帧截图、分镜描述或爆款剧情构想）时，执行以下标准化流程：

```
[用户输入视频/素材/需求]
         │
         ▼
 ┌────────────────────────────────────────────────────────┐
 │ 阶段一：爆款视频深度解构与反推 (Reverse-Engineering)    │
 │ 1. 镜头语言与画质解构 (Cinematography)                 │
 │ 2. 光影、色彩与粒子氛围反推 (Lighting & Atmosphere)      │
 │ 3. 动作动力学与因果律反推 (Action & Physics)             │
 │ 4. 音效与节奏拆解 (Sound & Pacing)                     │
 │ 5. 5秒周期分镜切片 (5s Shot Slicing)                   │
 └────────────────────────────────────────────────────────┘
         │
         ▼
 ┌────────────────────────────────────────────────────────┐
 │ 阶段二：MiniMax-H3 智能导演重构 (Prompt Structuring)    │
 │ 1. 智能匹配 task_type 与 UNET (fl2v/r2v/i2v/t2v/v2v)   │
 │ 2. 生成【公共提示词 (Common Prompt)】                    │
 │ 3. 生成【分段提示词组 (Group 1 ~ N Prompts)】           │
 │ 4. 生成【专属负向提示词 (Negative Prompt)】              │
 │ 5. 输出【ComfyUI 节点参数配置表】                        │
 └────────────────────────────────────────────────────────┘
```

---

## 阶段一：爆款视频深度解构与反推规范

反推视频时，严格按照以下 5 个维度进行多模态/视觉逆向分析：

### 1. 镜头语言与摄影画质 (Cinematography)
- **景别变换**：极特写 (Extreme Close-up) $\rightarrow$ 中景 (Medium Shot) $\rightarrow$ 广角环境 (Wide Landscape)。
- **摄影机运镜**：运镜轨迹（如 `rapid push-in`, `dynamic low-angle tracking`, `360-degree orbital pan`, `FPV drone rush`）。
- **光学质感与画质**：电影级摄影机型号（如 `ARRI Alexa 35`, `RED V-Raptor`, `35mm Anamorphic Lens`）、浅景深 (shallow depth of field)、电影级镜头光晕 (cinematic lens flare)、微颗粒感 (subtle film grain)。

### 2. 光影、色彩与环境粒子 (Lighting & Atmosphere)
- **主光源与光比**：强侧逆光 (strong rim lighting)、体积光/丁达尔效应 (volumetric Tyndall rays)、戏剧性明暗对比 (chiaroscuro)。
- **色调与调色**：赛博霓虹 (Cyberpunk neon)、青橙电影调色 (Teal and Orange grade)、暗黑哥特 (Dark Gothic tones)。
- **环境动态粒子**：空气尘埃 (dust motes in air)、飞溅雨滴/水花 (splashing water droplets)、火星碎屑 (glowing embers)、漫卷烟雾 (rolling smoke)。

### 3. 动作动力学与因果律 (Action & Dynamic Causality)
- **拒绝动作真空**：严格拆解动作链条 —— **起势蓄力 (Wind-up) $\rightarrow$ 爆发触点 (Impact Peak) $\rightarrow$ 物理形变/反作用力 (Reaction & Deformation) $\rightarrow$ 动势延伸 (Follow-through)**。
- 每一个动作必须有明确的物理反馈（如地面碎裂、衣物飘动、气浪冲击、肌肉紧绷）。

### 4. 音效与拟音设计 (Sound FX & Foley)
- 提取关键动作的撞击音 (`heavy mechanical thud`, `metallic clashing`)、气流呼啸音 (`wind whoosh`)、环境背景底噪 (`ambient thunder`, `neon buzzing`)。

### 5. 5秒周期分镜切片 (5-Second Slicing)
- MiniMax-H3 的单段黄金生成时长为 **5 秒**（24/25 FPS 对应 120/125 帧）。
- 将视频按 5 秒一段切分（Group 1: 0~5s, Group 2: 5~10s, Group 3: 10~15s...），并确保段与段之间具有清晰的**动量继承点**。

---

## 阶段二：MiniMax-H3 导演台标准化输出结构

输出时必须提供完整、规范、可直接复制到 ComfyUI 节点的格式：

```markdown
### 🎬 【模式与节点选择】
- **推荐模式 (task_type)**: `fl2v` / `r2v` / `i2v` / `t2v` / `v2v`
- **对应 UNET 模型**: `fl2va` (针对 fl2v/i2v/t2v) 或 `ref2va` (针对 r2v/v2v/rv2v)
- **CLIP 文本编码器**: `minimax` (基于 Qwen3-VL)
- **段间引导 (Motion Context)**: True (建议 `22` 帧)

---

### 🌐 【公共提示词 (Common Prompt)】
(定义全局画质、摄影机光圈/镜头、环境光影、粒子系统与全局声音氛围)
[8K masterpiece, cinematic lighting, shot on ARRI Alexa 35, 35mm anamorphic lens, shallow depth of field, ...]

---

### 🎞️ 【分段提示词组 (Prompt Groups)】

#### 🔹 Group 1 (0.0s - 5.0s) —— [分段主题/起势高潮]
- **时长**: 5.0s | **帧数**: 120/125 帧
- **首帧状态**: (描述起始画面状态，或继承上传的首帧图像)
- **动作与运镜**: (详述 0~5 秒内的连续动作演进、摄影机机位移动与物理互动)
- **音效提示**: (动作音效、气流、碰撞声)

#### 🔹 Group 2 (5.0s - 10.0s) —— [转折推进/动势承接]
- **时长**: 5.0s | **帧数**: 120/125 帧
- **动量继承**: (承接上一段结尾动势，开启段间引导 22 帧)
- **动作与运镜**: (剧情推进、速度切换、爆发碰撞)
- **音效提示**: (呼应动作的声效)

#### 🔹 Group 3 (10.0s - 15.0s) —— [终极爆发/高潮收尾]
- **时长**: 5.0s | **帧数**: 120/125 帧
- **动量继承**: (承接上一段动势)
- **动作与运镜**: (终结一击、镜头定格拉开或电影张力收尾)
- **音效提示**: (高潮打击声与环境余韵)

---

### 🚫 【专属负向提示词 (Negative Prompt)】
[blurry, low quality, distorted anatomy, extra limbs, static pose, slow-motion stall, cartoon, watermark, glitch, sudden cut, ...]

---

### ⚙️ 【ComfyUI 节点参数推荐表】
| 参数项 | 设置值 | 核心说明 |
| :--- | :--- | :--- |
| **task_type** | `fl2v` / `r2v` | 依据素材选择 |
| **UNET Model** | `fl2va` / `ref2va` | 严防混淆 |
| **Motion Context** | `True` (帧数 `22`) | 多段连贯核心开关 |
| **FPS** | `24` 或 `25` | 电影级标准流畅度 |
| **Audio Generation** | `True` | 开启原生音画同步 |
| **Refine 二次精修** | 可选 (建议同分辨率 Refine) | 提升皮肤与金属细节 |
```

---

## 模式选择黄金准则速查

| 创作场景 | 首选 task_type | UNET | 关键素材准备 | 提示词特殊语法 |
| :--- | :--- | :--- | :--- | :--- |
| **连续长剧情/高燃打斗** | **`fl2v`** | `fl2va` | 1张首帧关键图（或首尾帧） | 自然语言动作流 + 段间引导继承 |
| **多角色/指定道具爆款** | **`r2v`** | `ref2va` | 角色图、道具图、音频素材 | `<Picture 1>`, `<Picture 2>`, `<Audio 1>` |
| **实拍动作/舞蹈爆款复刻** | **`v2v` / `rv2v`** | `ref2va` | 源爆款视频 (`<Video 1>`) | `<Video 1>` 动作迁移 + 新画风描述 |
| **概念单图动态化** | **`i2v`** | `fl2va` | 1张原画/设计图 | 聚焦镜头运动与局部微动态 |
| **无参考图纯文本生成** | **`t2v`** | `fl2va` | 无需素材 | 公共提示词需强定义角色与环境外貌 |

---

## 质量控制与防翻车准则

1. **绝对禁止“慢动作摆拍”**：爆款视频的核心在于张力，必须明确动词（如 `lunges forward`, `pivots sharply`, `unleashes an explosive strike`），避免模糊的 `standing coolly`。
2. **段间动量无缝锚定**：Group 2 及以后的提示词第一句必须写明继承上段末尾的姿态与运动矢量（例如：*“Continuing the forward momentum from the previous strike, the protagonist smoothly spins...”*）。
3. **音效精准锚定**：如开启音频生成，提示词中必须包含环境声（Ambience）与拟音（Foley），避免生成静音或杂音。
4. **占位符规范**：在 `r2v`/`rv2v` 中引用图片必须严格遵循 `<Picture 1>`、视频 `<Video 1>`，禁止随意发明 `<ImageA>` 等非标准标签。
