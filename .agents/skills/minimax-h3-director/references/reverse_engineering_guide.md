# 爆款视频深度解构与反推提示词指南 (Reverse-Engineering Guide)

在复刻爆款短视频（如高燃打斗、赛博科幻、电影感广告、国风特效、跑车竞速等）时，需要将一段复杂的视觉体验，精确解构成 AI 视频生成模型（MiniMax-H3）能理解的 5 大维度参数。

---

## 维度一：镜头语言与摄影构图 (Camera & Framing)

| 镜头类型 / 运镜术语 | 英文提示词 (Prompt Keywords) | 视觉效果与适用场景 |
| :--- | :--- | :--- |
| **极速推进/冲刺变焦** | `rapid cinematic push-in`, `crash zoom onto subject` | 强调爆发瞬间、面部震撼表情或武器触点 |
| **低角度仰拍追踪** | `dynamic low-angle tracking shot`, `ground-level perspective` | 增强角色压迫感、速度感与庞大体量 |
| **环绕运镜** | `360-degree orbital arc shot around subject`, `spiral panning` | 展示角色全方位动作、气场爆发或子弹时间 |
| **第一人称/近身追焦** | `first-person FPV rush`, `tight shoulder-cam tracking` | 沉浸式格斗、极速跑酷、主观驾驶视点 |
| **俯瞰大广角** | `birds-eye top-down wide view`, `epic aerial crane shot` | 场景全貌、阵法法阵展开、群体对抗 |
| **荷兰角/倾斜构图** | `dramatic Dutch angle`, `canted framing` | 紧张局势、危机感、心理失衡 |
| **电影光学质感** | `shot on 35mm anamorphic lens, beautiful oval bokeh, subtle chromatic aberration, ARRI Alexa 35 color grade` | 好莱坞电影大片质感，去除塑料感 |

---

## 维度二：光影氛围与环境粒子系统 (Lighting & Particle FX)

| 光影与粒子类型 | 英文提示词 (Prompt Keywords) | 画面作用 |
| :--- | :--- | :--- |
| **强侧逆光 / 轮廓光** | `strong volumetric rim lighting, crisp edge highlights outlining the silhouette` | 分离角色与背景，雕刻肌肉与金属边缘 |
| **丁达尔体积光** | `volumetric light beams cutting through haze, misty god rays` | 营造神圣、神秘或破晓清晨氛围 |
| **暗调明暗对比** | `high contrast chiaroscuro lighting, deep cinematic shadows` | 黑色电影质感、悬疑、力量感 |
| **流体与物理飞溅** | `splattering water droplets frozen in air, exploding mud particles` | 强化物理打击感与环境交互 |
| **能量余烬与火星** | `swirling glowing ember particles, drifting sparks and heat distortion` | 爆炸余波、烈火刀锋、魔幻能量释放 |
| **烟雾与尘埃** | `dense rolling smoke billowing across ground, suspended atmospheric dust motes` | 增加场景纵深与厚重感 |

---

## 维度三：动作链条与因果律分解法 (Action Chain & Causality)

爆款视频之所以吸引人，在于每一个动作都有明确的**物理起因、形变与反作用力**。提示词必须遵循**四段式动作因果律**：

```
[1. 起势蓄力 (Wind-Up)]
  └── 肌肉紧绷、重心下沉、刀刃反手后撤、空气气流内聚
        │
[2. 爆发冲击 (Impact Peak)]
  └── 瞬间极速位移、刀刃斩击触点火星四溅、骨骼碰撞冲击波
        │
[3. 受力反馈 (Physical Reaction)]
  └── 受击者身体剧烈后仰/被击飞、衣物剧烈甩动、地面受力龟裂
        │
[4. 动势收拢与余韵 (Follow-Through / Momentum)]
  └── 落地滑行带起碎石、气浪扩散、摄影机晃动后重新聚焦
```

---

## 维度四：音画对齐设计 (Sound FX & Audio Sync)

MiniMax-H3 支持生成原生音画同步的视频。在提示词中必须嵌入清晰的声音描述词：

1. **环境音 (Atmospheric Ambience)**:
   - `heavy distant thunder rumbling`, `rain pouring loudly on asphalt`, `low mechanical hum of neon transformers`
2. **拟音打击 (Foley & Impacts)**:
   - `sharp metallic blade clash with resonant ringing`, `heavy bone-crunching punch impact`, `screeching rubber tires on wet tarmac`
3. **气流与能量 (Whooshes & Energy)**:
   - `violent sonic boom whoosh`, `crackling electrical arcs`, `fiery combustion roar`

---

## 维度五：5秒节奏分段与段间引导锚定 (5s Slicing & Motion Anchoring)

MiniMax-H3 的段间引导（Motion Context）会抓取上一段末尾 22 帧的动量。
为了让 AI 完美衔接，**Group 2 及之后的段落提示词必须遵循以下语法**：

- **语法模板**：
  > `[继承上段动势] Continuing immediately from the previous [motion/action], [Subject] smoothly [next continuous action]...`
- **示例**：
  > *Group 1 结尾*：Protagonist leaps into the air with his blade raised.
  > *Group 2 开头*：Continuing the airborne descent from the jump, the protagonist plunges his blade violently into the asphalt, sending concrete debris erupting upward.
