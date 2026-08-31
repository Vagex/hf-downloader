import express from 'express';
import cors from 'cors';
import fs from 'fs';
import path from 'path';
import multer from 'multer';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;

// Data directory
const DATA_DIR = path.join(__dirname, 'data');
const UPLOADS_DIR = path.join(DATA_DIR, 'uploads');
const DB_FILE = path.join(DATA_DIR, 'prompts.json');

if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });
if (!fs.existsSync(UPLOADS_DIR)) fs.mkdirSync(UPLOADS_DIR, { recursive: true });

// Setup Multer for media uploads (images and videos up to 200MB)
const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, UPLOADS_DIR),
  filename: (req, file, cb) => {
    const ext = path.extname(file.originalname).toLowerCase();
    const prefix = ['.mp4', '.webm', '.mov', '.mkv'].includes(ext) ? 'video-' : 'img-';
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1e9);
    cb(null, prefix + uniqueSuffix + ext);
  }
});
const upload = multer({ 
  storage, 
  limits: { fileSize: 200 * 1024 * 1024 } // 200MB limit for AI videos
});

app.use(cors());
app.use(express.json({ limit: '50mb' }));
app.use('/uploads', express.static(UPLOADS_DIR));

// Load or initialize DB
function getPrompts() {
  if (fs.existsSync(DB_FILE)) {
    try {
      const content = fs.readFileSync(DB_FILE, 'utf-8');
      const parsed = JSON.parse(content);
      if (Array.isArray(parsed) && parsed.length > 0) {
        return parsed;
      }
    } catch (e) {
      console.error('Error reading DB:', e);
    }
  }

  // Auto seed initial prompts if DB is empty
  const defaultData = [
    {
      id: "prompt-airplane-window-shot",
      title: "飞机舷窗一镜到底长镜头（首尾帧穿梭）",
      category: "video",
      subcategory: "LTX 2.5 / Minimax h3 / 可灵 Kling",
      aspectRatio: "9:16",
      duration: "8-10s",
      rating: 5,
      isPinned: true,
      tags: ["一镜到底", "长镜头", "首尾帧", "穿梭运镜", "黄昏金光", "写实摄影"],
      variables: [
        { key: "flight_no", label: "航班号", defaultValue: "CX 831" },
        { key: "departure", label: "出发地", defaultValue: "HKG" },
        { key: "destination", label: "目的地", defaultValue: "SFO" },
        { key: "gate", label: "登机口", defaultValue: "15" },
        { key: "seat", label: "座位号", defaultValue: "12A" },
        { key: "ground_material", label: "地面材质", defaultValue: "浅色石材地砖" }
      ],
      prompt: `一条连续长镜头，不许切镜，写实摄影，竖屏 9:16，大约 8 到 10 秒。\n\n从首帧开始：坐在飞机座位上向外看椭圆形舷窗，窗框在前景，窗外是机翼、发光云海，云缝里能看见下方的滨海城市和港口，金色夕光。\n\n镜头缓慢前推，穿过双层舷窗玻璃，顺着机翼飞出去，离开飞机后贴着云顶滑行，再从云缝俯冲向下，飞向刚才窗外看到的同一座滨海城市和港口。保持黄昏金光。\n\n镜头继续下降，掠过水岸和航站楼屋顶，穿过玻璃幕墙进入安静的候机厅，降到坐着时的第一人称视角，低头看向自己的腿上。\n\n准确落在尾帧：双手拿着一张米色登机牌，上面写着 FLIGHT {{flight_no}} | {{departure}} → {{destination}} | GATE {{gate}} | SEAT {{seat}}，下方是牛仔裤和白色运动鞋，地面是{{ground_material}}。`,
      negativePrompt: "镜头运动要有惯性。不要跳切，不要文字变形，不要额外字幕，不要突然出现别人的大脸。",
      images: [
        "/uploads/airplane-shot-ref.png"
      ],
      notes: "首尾帧运镜神作，适用于 LTX 2.5、Minimax h3 或可灵 1.5/2.0 首尾帧模式。建议配合首帧图（舷窗机翼）和尾帧图（第一人称手持登机牌）生成。",
      createdAt: new Date().toISOString()
    },
    {
      id: "prompt-ltx-rainy-cyberpunk-drive",
      title: "LTX 2.5 极致物理惯性·雨夜飞车追逐长镜头",
      category: "video",
      subcategory: "LTX 2.5",
      aspectRatio: "16:9",
      duration: "6-10s",
      rating: 5,
      isPinned: true,
      tags: ["LTX 2.5", "物理惯性", "长镜头", "雨夜反光", "电影质感", "高速运镜"],
      variables: [
        { key: "vehicle_type", label: "载具类型", defaultValue: "哑光黑色复古跑车" },
        { key: "city_scene", label: "城市街道", defaultValue: "雨水浸湿的东京高架桥与霓虹隧道" },
        { key: "camera_move", label: "运镜轨迹", defaultValue: "镜头从车尾低角度紧贴地面快速贴地前移，平滑升起并穿过挡风玻璃进入驾驶室" }
      ],
      prompt: "【LTX 2.5 专用电影级动态】\n电影级连续高速运镜，不切镜，真实物理惯性。\n画面中一辆{{vehicle_type}}在{{city_scene}}上飞速疾驰，轮胎带起细腻真实的水雾飞溅与沥青地面积水反光。\n{{camera_move}}。车窗外霓虹灯光随着车速形成柔和自然的流光拖影，车内仪表盘发出幽微蓝光。全片保持严谨的物理光照反射与空气悬浮微粒感，35mm 变形宽银幕电影摄影，Kodak 5219 色彩风格，超高画质。",
      negativePrompt: "画面卡顿，帧率过低，塑料感，模型穿模，突兀剪辑，无物理惯性，低分辨率",
      images: [
        "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?q=80&w=800&auto=format&fit=crop"
      ],
      notes: "LTX 2.5 在处理真实物理速度感、水花飞溅与复杂光影连续过渡上表现极佳，建议加入明确的运镜惯性与相机速度描述。",
      createdAt: new Date().toISOString()
    },
    {
      id: "prompt-minimax-h3-cinematic-character",
      title: "Minimax h3 海螺·电影级情绪微表情推镜",
      category: "video",
      subcategory: "Minimax h3",
      aspectRatio: "16:9",
      duration: "6-8s",
      rating: 5,
      isPinned: true,
      tags: ["Minimax h3", "海螺视频", "微表情", "情绪特写", "自然呼吸", "电影光影"],
      variables: [
        { key: "character", label: "人物主角", defaultValue: "一位眼神深邃的30岁建筑设计师，微卷发丝在微风中轻动" },
        { key: "action", label: "细微动作", defaultValue: "缓缓转头看向窗外的斜阳，嘴角泛起一抹释怀的微笑，轻轻呼出一口气" },
        { key: "environment", label: "环境空间", defaultValue: "布满图纸和咖啡杯的落地窗工作室，夕阳洒在脸庞" }
      ],
      prompt: "【Minimax h3 海螺电影叙事模式】\n电影级自然慢推镜头，极高真实感人物动态。\n画面聚焦在{{character}}，位于{{environment}}。\n{{action}}。人物具有极度逼真的皮肤肌理细节、微表情变化与自然的胸膛起伏呼吸节奏。侧逆光勾勒出发丝与睫毛的金色轮廓，镜头运用阿莱（ARRI Alexa 65）大画幅电影机浅景深虚化背景，情绪饱满，胶片质感细腻，大师级光影构图。",
      negativePrompt: "面部僵硬，假笑，皮肤过度磨皮，塑料质感，多余手指畸变，画质模糊，动作不自然",
      images: [
        "https://images.unsplash.com/photo-1534528741775-53994a69daeb?q=80&w=800&auto=format&fit=crop"
      ],
      notes: "Minimax h3 (海螺) 对人脸微表情、自然眼神转动与肢体连贯性极强，提示词重点强调情绪流转与环境光影融合。",
      createdAt: new Date().toISOString()
    },
    {
      id: "prompt-flux-cinematic-portrait",
      title: "FLUX.1 电影感自然光胶片人像",
      category: "image",
      subcategory: "FLUX.1 / Midjourney",
      aspectRatio: "3:4",
      duration: "",
      rating: 5,
      isPinned: true,
      tags: ["胶片质感", "电影光影", "人像摄影", "35mm镜头", "柯达色彩"],
      variables: [
        { key: "subject", label: "人物主体", defaultValue: "24岁的东亚年轻女性，微卷短发，眼神清澈而坚定" },
        { key: "clothing", label: "服装搭配", defaultValue: "复古深绿色的羊毛开衫与高领打底衫" },
        { key: "location", label: "场景环境", defaultValue: "午后阳光斜照的木质复古咖啡馆靠窗座位" },
        { key: "lighting", label: "光影氛围", defaultValue: "柔和温暖的侧逆光，窗帘投下的斑驳光影" }
      ],
      prompt: `Cinematic 35mm photograph of {{subject}}, wearing {{clothing}}, seated at {{location}}. {{lighting}}, subtle film grain, Kodak Portra 400 aesthetic, candid emotional expression, shallow depth of field, f/1.4 aperture, hyperrealistic skin textures, soft warm tones, masterpiece, 8k resolution.`,
      negativePrompt: "cgi, 3d render, plastic skin, oversaturated, deformed hands, extra fingers, cartoon, blurry, watermark",
      images: [
        "https://images.unsplash.com/photo-1534528741775-53994a69daeb?q=80&w=800&auto=format&fit=crop"
      ],
      notes: "专为 FLUX.1 Schnell / Dev 调优的胶片质感人像，光影极其自然，无塑料感。",
      createdAt: new Date().toISOString()
    },
    {
      id: "prompt-kling-macro-liquid-product",
      title: "高端香水/精油微距动态流体广告运镜",
      category: "video",
      subcategory: "可灵 Kling / Runway",
      aspectRatio: "16:9",
      duration: "5-10s",
      rating: 4,
      isPinned: false,
      tags: ["微距运镜", "流体粒子", "商业广告", "4K慢动作", "极简奢华"],
      variables: [
        { key: "brand_color", label: "品牌主色调", defaultValue: "琥珀金与墨黑色" },
        { key: "product_name", label: "产品类型", defaultValue: "奢华玻璃方瓶香水" },
        { key: "ingredient", label: "核心成分元素", defaultValue: "金色蜜糖与柑橘水滴" }
      ],
      prompt: `极致商业广告特写，超慢动作升格摄影。镜头围绕{{product_name}}进行 360 度平滑微距旋转运镜。四周环绕着晶莹剔透的{{ingredient}}和丝滑流淌的悬浮液体，反射出耀眼的{{brand_color}}光芒。背景为极简高级哑光暗色调，纯净通透，工作室环形柔光照明，光影流转，电影级色彩渲染。`,
      negativePrompt: "画面卡顿，液体飞溅失控，文字畸变，模糊，暗角严重，杂质",
      images: [
        "https://images.unsplash.com/photo-1592945403244-b3fbafd7f539?q=80&w=800&auto=format&fit=crop"
      ],
      notes: "适合可灵高画质模式或 Luma Dream Machine，建议开启专业运镜模式。",
      createdAt: new Date().toISOString()
    },
    {
      id: "prompt-mj-cyberpunk-architecture",
      title: "新中式赛博朋克立体建筑与空中步道",
      category: "image",
      subcategory: "Midjourney v6.1",
      aspectRatio: "16:9",
      duration: "",
      rating: 4,
      isPinned: false,
      tags: ["赛博朋克", "新中式", "未来建筑", "霓虹夜景", "虚幻引擎5"],
      variables: [
        { key: "city_feature", label: "城市地标特征", defaultValue: "悬浮在万丈深渊之上的重檐飞檐空中阁楼与霓虹天桥" },
        { key: "weather", label: "天气效果", defaultValue: "细雨蒙蒙，湿漉漉的地面反射出璀璨霓虹倒影" }
      ],
      prompt: `Futuristic Neo-Chinoiserie megastructure city, {{city_feature}}, holographic dragons floating between soaring skyscrapers, {{weather}}, misty cyberpunk atmosphere, volumetric orange and cyan neon lighting, hyper-detailed architectural details, Unreal Engine 5 render, Octane render, 8k --ar 16:9 --v 6.1 --style raw`,
      negativePrompt: "--no blurry, low resolution, messy perspective",
      images: [
        "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?q=80&w=800&auto=format&fit=crop"
      ],
      notes: "Midjourney 经典出图词，可根据变量随时替换不同的中国风古建筑元素与雨夜效果。",
      createdAt: new Date().toISOString()
    },
    {
      id: "prompt-llm-senior-prompt-engineer",
      title: "大模型顶级 Prompt 架构师元提示词 (System Role)",
      category: "text",
      subcategory: "Claude 3.7 / GPT-4o / DeepSeek",
      aspectRatio: "",
      duration: "",
      rating: 5,
      isPinned: true,
      tags: ["系统提示词", "角色扮演", "结构化输出", "元提示词", "深度思考"],
      variables: [
        { key: "target_domain", label: "目标任务领域", defaultValue: "短视频爆款文案生成 / 跨境电商详情页 / 架构代码重构" }
      ],
      prompt: `你是一位世界顶级的 Prompt 架构专家与思维链设计大师。\n你的任务是为我定制用于【{{target_domain}}】的极高水准结构化 Prompt。\n\n请按照以下五层标准框架进行设计输出：\n1. 【Role & Context】：清晰定义 AI 的专家人设、背景能力与认知深度。\n2. 【Task & Workflow】：分步骤拆解任务执行逻辑，避免一步到位的浅层思考。\n3. 【Constraints & Rules】：明确负向约束与必须遵守的边界红线。\n4. 【Dynamic Variables】：用 {{变量名}} 形式标注可随时替换的业务参数。\n5. 【Few-Shot Examples】：提供 1-2 个高质量输入与期望输出的黄金对照样本。\n\n请先询问我的具体业务诉求与痛点细节，然后再为我输出完整 Prompt 模版。`,
      negativePrompt: "",
      images: [],
      notes: "通用的元提示词模版，用来让大模型帮你写出更精准、专业的下级提示词。",
      createdAt: new Date().toISOString()
    }
  ];
  savePrompts(defaultData);
  return defaultData;
}

function savePrompts(prompts) {
  fs.writeFileSync(DB_FILE, JSON.stringify(prompts, null, 2), 'utf-8');
}

// REST API Endpoints

// 1. Get all prompts
app.get('/api/prompts', (req, res) => {
  const prompts = getPrompts();
  res.json({ success: true, data: prompts });
});

// 2. Add new prompt
app.post('/api/prompts', (req, res) => {
  const prompts = getPrompts();
  const newPrompt = {
    ...req.body,
    id: req.body.id || `prompt-${Date.now()}-${Math.random().toString(36).substr(2, 6)}`,
    createdAt: req.body.createdAt || new Date().toISOString(),
    updatedAt: new Date().toISOString()
  };
  prompts.unshift(newPrompt);
  savePrompts(prompts);
  res.json({ success: true, data: newPrompt });
});

// 3. Update prompt
app.put('/api/prompts/:id', (req, res) => {
  const { id } = req.params;
  let prompts = getPrompts();
  const index = prompts.findIndex(p => p.id === id);
  if (index === -1) {
    return res.status(404).json({ success: false, message: 'Prompt not found' });
  }
  prompts[index] = { ...prompts[index], ...req.body, updatedAt: new Date().toISOString() };
  savePrompts(prompts);
  res.json({ success: true, data: prompts[index] });
});

// 4. Delete prompt
app.delete('/api/prompts/:id', (req, res) => {
  const { id } = req.params;
  let prompts = getPrompts();
  prompts = prompts.filter(p => p.id !== id);
  savePrompts(prompts);
  res.json({ success: true, message: 'Deleted successfully' });
});

// 5. Media upload (images / videos)
app.post('/api/upload', upload.any(), (req, res) => {
  if (!req.files || req.files.length === 0) {
    return res.status(400).json({ success: false, message: 'No files uploaded' });
  }
  const urls = req.files.map(file => `/uploads/${file.filename}`);
  res.json({ success: true, urls });
});

// 6. Bulk Export
app.get('/api/export', (req, res) => {
  const prompts = getPrompts();
  res.setHeader('Content-Type', 'application/json');
  res.setHeader('Content-Disposition', `attachment; filename=prompthub-backup-${new Date().toISOString().slice(0,10)}.json`);
  res.send(JSON.stringify(prompts, null, 2));
});

// 7. Bulk Import
app.post('/api/import', (req, res) => {
  const { prompts: newPrompts, mode } = req.body; // mode: 'replace' | 'merge'
  if (!Array.isArray(newPrompts)) {
    return res.status(400).json({ success: false, message: 'Invalid data format' });
  }

  let finalPrompts = [];
  if (mode === 'replace') {
    finalPrompts = newPrompts;
  } else {
    // Merge: prevent duplicate IDs
    const existing = getPrompts();
    const existingIds = new Set(existing.map(p => p.id));
    const toAdd = newPrompts.filter(p => !existingIds.has(p.id));
    finalPrompts = [...toAdd, ...existing];
  }

  savePrompts(finalPrompts);
  res.json({ success: true, count: finalPrompts.length });
});

// Serve frontend in production
const distPath = path.join(__dirname, 'dist');
if (fs.existsSync(distPath)) {
  app.use(express.static(distPath));
  app.get('*', (req, res) => {
    res.sendFile(path.join(distPath, 'index.html'));
  });
}

app.listen(PORT, '0.0.0.0', () => {
  console.log(`🚀 PromptHub server is running at http://0.0.0.0:${PORT}`);
});
