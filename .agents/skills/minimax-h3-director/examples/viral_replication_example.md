# 爆款视频复刻实战案例：赛博朋克机甲刺客雨夜斩击 (15秒电影级长镜头)

本案例展示如何从一个 15 秒的短视频爆款（机甲武士雨夜拔刀斩破敌方无人机）逆向解构，并重构为 ComfyUI MiniMax-H3 导演台专属的 3 段提示词组。

---

## 阶段一：爆款原片深度解构 (Reverse-Engineering Analysis)

- **场景与光影**：深夜暴雨中的新东京街道，湿漉漉的沥青路面反射紫色与青蓝色霓虹灯光。强侧逆光勾勒武士机械铠甲轮廓，雨滴在铠甲上飞溅成雾。
- **摄影机运镜**：
  - 0-5s: 低角度仰拍跟踪武士拔刀起跑，快门微动模糊。
  - 5-10s: 极速推进环绕特写，刀锋与无人机接触瞬间产生强光与冲击波。
  - 10-15s: 广角慢动作拉开，无人机在背后爆炸切成两半，武士收刀入鞘，烟雾升腾。
- **动作因果链**：起跑蓄力 $\rightarrow$ 蹬地跃起拔刀 $\rightarrow$ 凌空一字斩击中核心 $\rightarrow$ 穿透落地滑行 $\rightarrow$ 纳刀爆炸。
- **声音设计**：暴雨倾盆声、涡轮引擎轰鸣、高频离子利刃出鞘音、爆炸金属碎裂巨响。

---

## 阶段二：ComfyUI MiniMax-H3 导演台标准化输出

### 🎬 【模式与节点选择】
- **推荐模式 (task_type)**: `fl2v` (首尾帧生视频 / 连续长镜头模式)
- **对应 UNET 模型**: `fl2va`
- **CLIP 文本编码器**: `minimax` (Qwen3-VL)
- **段间引导 (Motion Context)**: `True` (推荐 `22` 帧)
- **总时长 / 分段**: 15 秒 / 3 个 Prompt Groups

---

### 🌐 【公共提示词 (Common Prompt)】
```text
Masterpiece, 8K ultra-detailed cinematic cinematography, shot on ARRI Alexa 35 with 35mm anamorphic lens, shallow depth of field, dramatic cinematic lighting with vibrant teal and magenta cyberpunk neon reflections on wet asphalt, pouring rain with hyper-realistic water droplet physics, dense volumetric fog and atmospheric mist, crisp edge rim lighting illuminating high-tech carbon fiber armor, realistic physical motion blur, professional color grading, dynamic film soundscape with heavy ambient rain, deep thunder rumble, and electronic hum.
```

---

### 🎞️ 【分段提示词组 (Prompt Groups)】

#### 🔹 Group 1 (0.0s - 5.0s) —— [起势爆发：雨夜拔刀突进]
- **时长**: `5.0s` | **帧数**: `120 帧 (24 FPS)`
- **首帧状态**: 继承上传的首帧图像（Cyberpunk samurai crouching on a neon-lit wet street in heavy rain）。
- **Prompt**:
```text
The armored cyberpunk samurai suddenly explodes forward into a high-speed sprint across the flooded asphalt, splashing sheets of illuminated water droplets. Dynamic low-angle tracking camera pushes forward rapidly alongside his movement. His right hand grasps the glowing plasma katana hilt, smoothly unsheathing the blade with a blinding blue energy spark, accelerating directly toward the low-flying hostile combat drone hovering ahead. The sound of rapid heavy footsteps in puddles and the sharp acoustic hum of plasma charging.
```

#### 🔹 Group 2 (5.0s - 10.0s) —— [高潮交锋：凌空绝杀斩击]
- **时长**: `5.0s` | **帧数**: `120 帧 (24 FPS)`
- **动量继承**: 开启段间引导（22 帧），承接 Group 1 冲刺与出鞘动势。
- **Prompt**:
```text
Continuing seamlessly from the high-speed sprint, the samurai leaps explosively into mid-air, spinning his body into a devastating diagonal aerial slash across the armored core of the combat drone. The camera arcs in a rapid 180-degree orbital sweep around the point of impact. Violent electrical sparks, shattering titanium debris, and shockwave air ripples burst outward as the blade cleanly slices through the machine. Powerful metallic clashing impact sound and high-voltage electrical crackling.
```

#### 🔹 Group 3 (10.0s - 15.0s) —— [终极收尾：落地纳刀与背景爆炸]
- **时长**: `5.0s` | **帧数**: 120 帧 (24 FPS)
- **动量继承**: 开启段间引导（22 帧），承接 Group 2 空中斩击与下落动势。
- **Prompt**:
```text
Continuing the downward trajectory from the aerial slash, the samurai sticks a low crouched three-point landing on the wet street, sliding backward several meters while carving sparks into the ground. Behind him in the background, the cleaved drone erupts into a fiery cinematic explosion of orange flames and rolling black smoke. With steady calm motion, the samurai smoothly clicks the plasma blade back into its scabbard with a crisp metallic latch. Camera slowly pulls back into a majestic wide shot. Resonant deep bass explosion boom fading into steady rain ambience.
```

---

### 🚫 【专属负向提示词 (Negative Prompt)】
```text
blurry, low resolution, poorly rendered anatomy, extra arms, deformed hands, missing fingers, cartoonish, 3D video game engine look, CGI plasticky textures, static motionless character, unnatural abrupt teleportation, floating detached limbs, oversaturated anime bloom, bad lighting, watermark, text, timestamp.
```

---

### ⚙️ 【ComfyUI 节点参数推荐表】
| 节点/参数项 | 推荐设定值 | 设定依据与作用 |
| :--- | :--- | :--- |
| **task_type** | `fl2v` | 首尾帧长视频模式，最强连续性 |
| **UNET Model** | `fl2va` | 适配 fl2v/i2v 基础扩散架构 |
| **CLIP Loader** | `minimax` | Qwen3-VL 多模态中英文深度解析 |
| **Motion Context (段间引导)** | `True` | Group 2 / 3 必须勾选，消除跳帧与动作脱节 |
| **Context Frames** | `22` | 平衡动作连贯性与显存开销的最优值 |
| **FPS** | `24` | 电影工业标准帧率 |
| **Group Count** | `3` | 每组 5 秒，总共 15 秒超连贯动作大片 |
| **Audio Output** | `True` | 开启 MiniMax-H3 内置高保真音频合成 |
| **Refine 节点** | `MiniMax H3 Director Refine` (可选) | 对 15s 视频进行同分辨率超清画质精修 |
