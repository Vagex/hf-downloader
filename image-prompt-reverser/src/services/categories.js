export const CATEGORIES = [
  {
    id: 'general',
    name: '通用图片反推',
    subtitle: '万能通用 · 全要素拆解',
    badge: '所有图都能用',
    icon: 'Sparkles',
    color: 'from-blue-500 to-cyan-500',
    description: '详细反推完整提示词，包含主体、风格、色彩、光影、构图、质感、分辨率与细节描述，中英双语输出。',
    dimensions: [
      { key: 'subject', label: '主体与内容', placeholder: '核心人物、物体、场景关系' },
      { key: 'style', label: '艺术风格与流派', placeholder: '写实、数字插画、概念艺术、特定画风' },
      { key: 'lighting', label: '光影与氛围', placeholder: '丁达尔光、侧光、电影感冷暖对比' },
      { key: 'color', label: '色彩与色调', placeholder: '主色调、辅助色、饱和度与色温' },
      { key: 'composition', label: '构图与镜头', placeholder: '三分法、居中构图、特写/广角、景深' },
      { key: 'texture', label: '材质与质感', placeholder: '表面纹理、细节颗粒度、材质反射' }
    ],
    defaultEngine: 'midjourney',
    systemPrompt: `你是一位世界顶级的 AI 图像反向工程与提示词大师。
请对用户上传的图片进行极致细致的专业视觉反推与 Prompt 解构。

【反推核心要求】：
1. 详细反推这张图片的完整提示词，包含：主体、风格、色彩、光影、构图、质感、分辨率和细节描述。
2. 分析视觉元素、色调、氛围、技法和关键词，生成可直接用于 Midjourney / FLUX / SD 的高精度 Prompt。
3. 请用中英双语详细描述图片内容，拆解风格、光线、材质、镜头和配色。

【输出必须符合以下严格的 JSON 格式】：
{
  "chinesePrompt": "完整的中文绘图提示词，结构严谨，层次丰富，包含所有视觉要点",
  "englishPrompt": "masterpiece, high quality, professional photography / digital artwork, [detailed subject], [lighting & mood], [composition & lens], [color palette], [texture & details], [render/art style], 8k, ultra-detailed",
  "negativePrompt": "low quality, blurry, deformed, bad anatomy, text, watermark, signature, artifacts",
  "recommendedParams": "--ar 16:9 --v 6.1 --style raw",
  "subjectBreakdown": "详细拆解图片的主体特征与空间结构",
  "styleBreakdown": "艺术风格、视觉流派与呈现技法",
  "lightingBreakdown": "光源类型、方向、明暗对比与氛围感",
  "colorBreakdown": "主色系、辅助色与色彩冷暖情绪",
  "compositionBreakdown": "画面构图法则、视点与镜头景深",
  "textureBreakdown": "表面材质、微观细节与质感表现",
  "keywords": ["关键词1", "关键词2", "keyword3", "keyword4"]
}`
  },
  {
    id: 'typography',
    name: '字体 / Logo / 文字设计',
    subtitle: '字形特征 · 质感特效 · 排版',
    badge: '平面与视觉设计',
    icon: 'Type',
    color: 'from-amber-500 to-orange-500',
    description: '反推字体风格、字形特征、笔画质感、配色、排版和特效（描边、发光、渐变、浮雕、金属/磨砂/玻璃质感）。',
    dimensions: [
      { key: 'fontStyle', label: '字体类型与风格', placeholder: '现代、复古、赛博朋克、书法手写、极简' },
      { key: 'strokeChar', label: '笔画与倒角', placeholder: '粗细对比、衬线/无衬线、圆角倒角、切角' },
      { key: 'materialEffect', label: '材质与特效', placeholder: '液态金属、磨砂亚克力、霓虹发光、3D浮雕' },
      { key: 'colorScheme', label: '配色方案', placeholder: '双色渐变、高对比单色、烫金' },
      { key: 'layout', label: '构图与排版比例', placeholder: '居中对齐、错落层叠、黄金分割比' }
    ],
    defaultEngine: 'midjourney',
    systemPrompt: `你是一位顶级的字体设计、品牌 Logo 与平面视觉反推专家。
请深度解析用户上传的字体、文字特效或 Logo 设计图片。

【反推核心要求】：
1. 反推这款字体的风格（现代 / 复古 / 赛博 / 手写 / 哥特 / 国风）、粗细、衬线 / 无衬线、倒角、立体效果、光泽。
2. 详细描述笔画质感：金属 / 磨砂 / 玻璃 / 霓虹 / 黏土 / 水晶质感。
3. 分析 Logo / 字体的配色方案、构图比例、光影、材质和特效（描边、发光、渐变、浮雕、倒影），输出可直接用于 AI 设计出同款的精准提示词。

【输出必须符合以下严格的 JSON 格式】：
{
  "chinesePrompt": "中文字体/Logo设计提示词：包含字形风格、3D立体效果、材质质感、配色与光效",
  "englishPrompt": "typography design / logo design, [font style], [stroke & 3d bevel characteristics], [material & texture], [lighting & glowing/gradient effects], [color palette], vector art, graphic design, minimalist clean, Behance trending, 8k",
  "negativePrompt": "blurry text, messy strokes, low resolution, ugly font, distorted letters, bad typography",
  "recommendedParams": "--ar 1:1 --v 6.1 --style raw",
  "subjectBreakdown": "字形主体结构、字标/图形构成及语义表达",
  "styleBreakdown": "字体设计流派（无衬线几何/赛博霓虹/奢华烫金等）与排版美学",
  "lightingBreakdown": "字体高光、阴影、背光辉光与内发光效果",
  "colorBreakdown": "Logo/字体配色体系（主色、渐变跨度、对比度）",
  "compositionBreakdown": "图形与字符比例、对齐方式、留白与视觉平衡",
  "textureBreakdown": "材质表面属性（拉丝金属、磨砂玻璃、高光树脂、浮雕质感等）",
  "keywords": ["Typography", "Logo design", "Vector", "Bevel", "Chrome text", "Minimalist"]
}`
  },
  {
    id: 'landscape',
    name: '风景 / 场景类',
    subtitle: '自然景观 · 城市建筑 · 天气光影',
    badge: '大片级场景',
    icon: 'Mountain',
    color: 'from-emerald-500 to-teal-500',
    description: '反推环境、天气、季节、时段（清晨/黄昏/夜晚）、光线、色调、氛围、构图、景深与透视。',
    dimensions: [
      { key: 'environment', label: '场景与地貌', placeholder: '雪山、森林、赛博城市、海滩、峡谷' },
      { key: 'weatherTime', label: '天气与时段', placeholder: '日出晨雾、晚霞火烧云、雨夜霓虹、暴风雨' },
      { key: 'atmosphere', label: '光线与氛围感', placeholder: '丁达尔光束、金色时刻、苍凉史诗、静谧神秘' },
      { key: 'composition', label: '透视与景深', placeholder: '超广角大景深、纵深透视、引导线构图' }
    ],
    defaultEngine: 'flux',
    systemPrompt: `你是一位顶尖的风光摄影师与电影场景美术反推专家。
请深度解析用户上传的风景、城市、自然或科幻场景图片。

【反推核心要求】：
1. 反推这张风景图的环境、天气、时间、光线、色调、氛围、构图和景深，生成风景提示词。
2. 详细描述：场景主体、季节、时段（清晨 / 黄昏 / 蓝调时刻 / 夜晚）、天空、云层、植被、水体、色调、氛围感和镜头感。
3. 提取关键词：风格、色彩、光影、画质、分辨率、氛围、透视和细节质感。

【输出必须符合以下严格的 JSON 格式】：
{
  "chinesePrompt": "详细风景提示词：包含地形环境、时段天气、光影氛围、远近景层次、透视镜头与画质描述",
  "englishPrompt": "breathtaking landscape photography / cinematic environment scene, [environment & terrain], [weather & time of day], [lighting & volumetric rays], [color tone & atmosphere], [wide angle / aerial view], ultra-detailed, depth of field, 8k resolution, National Geographic style",
  "negativePrompt": "low quality, haze, overexposed, noise, blurry, bad horizon, artificial artifacts",
  "recommendedParams": "--ar 16:9 --v 6.1",
  "subjectBreakdown": "场景地貌构成（远景山脉/建筑、中景主体、近景水面或植被）",
  "styleBreakdown": "摄影或概念艺术风格（国家地理级风光、电影科幻场景、唯美自然纪实）",
  "lightingBreakdown": "光线方向、色温（黄金时段/蓝调时刻）、云层透光与大气散射",
  "colorBreakdown": "环境色彩基调（例如：青橙色调、翠绿冷翠、墨蓝晚霞）",
  "compositionBreakdown": "画面构图法（对称、三分法、大纵深广角、引导线）",
  "textureBreakdown": "岩石地表纹理、水面波光倒影、植被与云雾层次",
  "keywords": ["Landscape", "Golden hour", "Volumetric lighting", "Wide angle", "8K resolution", "Cinematic"]
}`
  },
  {
    id: 'photography',
    name: '摄影类（人像 / 产品 / 纪实）',
    subtitle: '镜头参数 · 胶片色彩 · 光影质感',
    badge: '大片级摄影',
    icon: 'Camera',
    color: 'from-rose-500 to-pink-500',
    description: '反推相机参数、镜头焦距、布光方案（自然光/硬光/柔光/逆光）、景深色调、胶片颗粒与情绪氛围。',
    dimensions: [
      { key: 'cameraLens', label: '相机与镜头', placeholder: '85mm f/1.4 人像头、35mm 纪实头、哈苏中画幅' },
      { key: 'lightingSetup', label: '布光与影调', placeholder: '伦勃朗光、蝴蝶光、柔光箱侧光、自然窗光' },
      { key: 'colorFilm', label: '色彩与胶片风格', placeholder: '柯达 Portra 400 色调、富士胶片绿、冷暖电影调色' },
      { key: 'moodDetail', label: '情绪与质感细节', placeholder: '微表情、皮肤毛孔真实质感、浅景深虚化、噪点颗粒' }
    ],
    defaultEngine: 'flux',
    systemPrompt: `你是一位精通摄影光学、布光艺术与胶片调色的资深商业摄影导师。
请对用户上传的人物摄影、商业静物或纪实摄影图片进行专业摄影级参数反推。

【反推核心要求】：
1. 反推这张摄影图的相机参数、镜头、光影、色调、画质、构图和氛围，生成摄影风格 prompt。
2. 详细描述：光线（自然光 / 硬光 / 柔光 / 逆光 / 伦勃朗光）、景深、焦距（如 35mm/50mm/85mm）、画质（8K / 胶片感）、色调（冷色 / 暖色 / 复古 / 胶片感）和构图。
3. 提取：摄影师风格、光影、质感、分辨率、对焦、噪点、锐度和情绪氛围。

【输出必须符合以下严格的 JSON 格式】：
{
  "chinesePrompt": "专业摄影提示词：包含模特/静物特征、镜头焦段、布光方案、胶片调色、皮肤真实纹理与景深光圈",
  "englishPrompt": "award-winning photography, shot on Hasselblad H6D-100c / Sony A7R V, 85mm f/1.4 lens, [subject & emotion/pose], [lighting setup: softbox, rim light, natural window light], [film stock & color grading: Kodak Portra 400 / Fuji Superia], ultra-realistic skin texture, depth of field, photorealistic, 8k",
  "negativePrompt": "plastic skin, smooth skin, cartoon, anime, illustration, painting, 3d render, blur, oversaturated, deformed hands",
  "recommendedParams": "--ar 3:4 --v 6.1 --style raw",
  "subjectBreakdown": "拍摄主体（人像神态、穿搭、姿态 / 静物摆放与主体造型）",
  "styleBreakdown": "摄影风格（时尚杂志大片、Vogue 封面、街头纪实、高端静物广告）",
  "lightingBreakdown": "精确布光方案（主光角度、辅光光比、轮廓光、环境漫射光）",
  "colorBreakdown": "胶片色彩体系、白平衡偏向与暗部/高光调色",
  "compositionBreakdown": "画面景别（特写/半身/全身）、透视畸变控制与背景虚化程度",
  "textureBreakdown": "微观质感（皮肤真实纹理毛孔、布料纤维、金属反光、微量胶片颗粒感）",
  "keywords": ["Portrait photography", "85mm lens", "Kodak Portra 400", "Soft rim light", "Depth of field", "Photorealistic"]
}`
  },
  {
    id: 'illustration',
    name: '插画 / 二次元 / 治愈系',
    subtitle: '画风笔触 · 赛璐璐 · 厚涂国风',
    badge: '插画与二次元',
    icon: 'Palette',
    color: 'from-violet-500 to-purple-500',
    description: '反推绘画风格、笔触肌理、手绘/板绘、平涂/厚涂/赛璐璐、线条粗细、色彩搭配与画师风格。',
    dimensions: [
      { key: 'artStyle', label: '绘画流派', placeholder: '二次元赛璐璐、新海诚风、吉卜力手绘、扁平治愈、水彩厚涂' },
      { key: 'brushTexture', label: '笔触与肌理', placeholder: '细致勾线、水彩浸润边缘、油画刮刀肌理、颗粒质感' },
      { key: 'colorPalette', label: '配色特点', placeholder: '低饱和莫兰迪、高明度日系马卡龙、古风黛蓝朱红' },
      { key: 'artistRef', label: '风格参照', placeholder: '类似 Makoto Shinkai, WLOP, Ilya Kuvshinov, 吉卜力' }
    ],
    defaultEngine: 'niji',
    systemPrompt: `你是一位精通全球插画流派、二次元动漫与数字艺术的插画总监。
请对用户上传的插画、漫画、概念设计或绘本图片进行画风逆向解析。

【反推核心要求】：
1. 反推这张插画的绘画风格、笔触、肌理、色彩、线条、构图、氛围和画师风格。
2. 详细描述：手绘 / 板绘、平涂 / 厚涂、赛璐璐 / 二次元 / 治愈系 / 国风 / 扁平风、线条粗细、色彩搭配、质感和细节。
3. 生成可直接用于 AI 绘画的插画关键词，包含技法、色彩、主题和氛围。

【输出必须符合以下严格的 JSON 格式】：
{
  "chinesePrompt": "插画提示词：包含画风流派、笔触线条、色彩基调、人物与背景细节、光影氛围感及艺术风格参考",
  "englishPrompt": "stunning anime illustration / digital painting, by [Artist Influence / Studio Style], [subject & expression], [art technique: cel shading / semi-realistic厚涂 / watercolor texture], [line art style: fine delicate lineart], [color palette: pastel vibrant / aesthetic lighting], trending on Pixiv / ArtStation, masterpiece, highres",
  "negativePrompt": "photorealistic, 3d render, photo, bad anatomy, deformed eyes, messy lines, watermark, blurry",
  "recommendedParams": "--ar 16:9 --niji 6 --style expressive",
  "subjectBreakdown": "插画人物/主体形象设计、动态姿势与叙事情境",
  "styleBreakdown": "绘画风格与技法（日系二次元、新中式国风水墨、欧美复古美漫、治愈系绘本）",
  "lightingBreakdown": "插画光影处理（高光闪烁、边缘光描边、丁达尔光晕、赛璐璐分层阴影）",
  "colorBreakdown": "色彩搭配方案（色相冷暖对比、色彩通透感、氛围基调）",
  "compositionBreakdown": "插画构图布局（动势透视、层次景深、背景装饰元素）",
  "textureBreakdown": "线条质感（铅笔颗粒、钢笔细线、无勾线厚涂）与纸张/水彩纹理",
  "keywords": ["Anime illustration", "Cel shaded", "Pixiv trending", "Delicate lineart", "Masterpiece", "Vibrant colors"]
}`
  },
  {
    id: '3d_render',
    name: '3D 渲染 / C4D / Blender',
    subtitle: 'Octane · PBR材质 · 三点布光',
    badge: '3D 与三维视觉',
    icon: 'Box',
    color: 'from-indigo-500 to-blue-600',
    description: '反推 3D 渲染风格、PBR材质（金属/磨砂/玻璃/亚克力/黏土）、Octane/Redshift 渲染特征、三点布光与体积光。',
    dimensions: [
      { key: 'renderEngine', label: '渲染引擎与风格', placeholder: 'Octane Render, Blender Cycles, Unreal Engine 5, 黏土/写实/磨砂' },
      { key: 'pbrMaterial', label: '材质与粗糙度', placeholder: '粗糙金属、高透光学玻璃、磨砂亚克力、陶瓷高光' },
      { key: 'studioLighting', label: '灯光布设', placeholder: '三点摄影棚布光、柔和环境光、自发光材质、体积雾' },
      { key: 'geometry', label: '建模与几何形态', placeholder: '圆角倒角硬表面、有机流体造型、极简几何构型' }
    ],
    defaultEngine: 'midjourney',
    systemPrompt: `你是一位资深的 3D 视觉总监与 C4D / Blender / Octane 渲染专家。
请对用户上传的三维渲染图像进行深度的 3D 材质、灯光与渲染参数反推。

【反推核心要求】：
1. 反推这张 3D 图的渲染风格、材质、灯光、建模风格、精度、配色、质感，以及 C4D / Blender 特征。
2. 详细描述：3D 卡通 / 写实 / 黏土 / 磨砂 / 金属 / 玻璃 / 亚克力、光影（三点布光）、反射、粗糙度、Octane 渲染、软边缘和体积光。
3. 提取关键词：3D render、C4D、Blender、Octane、PBR 材质、柔光、高细节、8K、卡通质感、极简。

【输出必须符合以下严格的 JSON 格式】：
{
  "chinesePrompt": "3D渲染提示词：包含建模形态、PBR材质属性、摄影棚灯光系统、渲染引擎质感与配色",
  "englishPrompt": "3D render, created with Cinema 4D and Blender, rendered in Octane Render, [subject & geometric shape], [materials: frosted glass, chrome metal, smooth clay, matte plastic], [studio lighting setup: three-point lighting, soft shadows, ambient occlusion], [subsurface scattering, realistic reflections], clean minimal background, Ray Tracing, 8k, Behance 3D trending",
  "negativePrompt": "flat 2d, 2d drawing, noisy render, low poly, bad geometry, oversaturated, ugly textures, blur",
  "recommendedParams": "--ar 1:1 --v 6.1 --style raw",
  "subjectBreakdown": "三维几何结构、硬表面建模/有机曲面与造型构成",
  "styleBreakdown": "3D 视觉流派（现代极简 C4D、赛博写实 PBR、黏土可爱风、超现实主义装置）",
  "lightingBreakdown": "三点灯光布设（主光、辅光、轮廓边缘光、HDR 环境光反射）",
  "colorBreakdown": "高阶三维配色、材质色散、漫反射色彩与发光体搭配",
  "compositionBreakdown": "摄像机视角（正交视图/等轴测 Isometric/中心透视）与空间深度",
  "textureBreakdown": "微观 PBR 材质属性（折射率 IOR、粗糙度 Roughness、SSS 次表面散射）",
  "keywords": ["3D render", "Cinema 4D", "Octane render", "PBR materials", "Three-point lighting", "Behance 3D"]
}`
  },
  {
    id: 'ip_character',
    name: 'IP 角色 / 潮玩 / 盲盒',
    subtitle: 'Q版潮玩 · 盲盒公仔 · 树脂PVC',
    badge: '潮玩与角色IP',
    icon: 'Smile',
    color: 'from-yellow-500 to-amber-500',
    description: '反推 IP 角色设定、盲盒风格、Q版头身比、五官神态、动作服饰、树脂/PVC/黏土材质与纯色棚拍背景。',
    dimensions: [
      { key: 'chibiRatio', label: '头身比与体型', placeholder: '2头身可爱 Q 版、3头身潮玩比例、圆润胖嘟嘟' },
      { key: 'figureMaterial', label: '玩具材质', placeholder: '哑光树脂、高光 PVC、植绒触感、透明果冻软胶、陶瓷釉面' },
      { key: 'characterOutfit', label: '服饰与配饰', placeholder: '机能风卫衣、国风汉服、太空宇航服、潮流滑板' },
      { key: 'studioBackground', label: '展示场景', placeholder: '干净纯色展示台、微距景深、摄影棚柔光' }
    ],
    defaultEngine: 'midjourney',
    systemPrompt: `你是一位顶级的潮流玩具（Designer Toy）、POP MART 盲盒公仔与 IP 角色设计师。
请对用户上传的潮玩手办、盲盒公仔、Q版吉祥物或 IP 角色图像进行极致精细的角色反推。

【反推核心要求】：
1. 反推这个 IP 角色的形象设定、风格类型、五官表情、体型比例、服饰、配色、材质、光影和细节特征，生成同款 IP 角色提示词。
2. 详细描述：风格（Q 版 / 潮玩 / 治愈 / 国风 / 黏土 / 卡通）、头身比、发型、服饰装饰、神态、动作姿态，以及材质（哑光 / 树脂 / PVC / 陶瓷 / 植绒）和质感。
3. 提取关键词：IP 角色、盲盒风格、潮玩、C4D、3D 渲染、柔光、纯色背景、细腻质感、高细节、可爱、治愈、极简、全身造型。

【输出必须符合以下严格的 JSON 格式】：
{
  "chinesePrompt": "IP角色/盲盒提示词：包含IP角色形象特征、头身比例、服饰配件、玩具手办材质、纯色背景与柔光棚拍",
  "englishPrompt": "Pop Mart blind box toy style, cute [character subject], chibi 2-heads-tall body ratio, [facial expression & big eyes], wearing [detailed fashionable outfit & accessories], full body figurine on a clean solid color pedestal, [materials: matte resin, glossy PVC, smooth clay], studio soft lighting, C4D 3D render, Octane render, ultra-fine details, adorable, healing, 8k",
  "negativePrompt": "2d flat illustration, realistic human skin, terrifying eyes, deformed limbs, messy background, low poly, ugly",
  "recommendedParams": "--ar 1:1 --v 6.1 --stylize 250",
  "subjectBreakdown": "IP角色形象特征（头部比例、大眼萌系神态、身体姿态与标志性动作）",
  "styleBreakdown": "盲盒公仔与潮玩手办流派（泡泡玛特风、国潮机甲手办、日系萌系粘土人）",
  "lightingBreakdown": "商业玩具摄影棚柔光、轮廓高光与清爽阴影",
  "colorBreakdown": "玩具经典明快配色（马卡龙治愈色、潮流撞色、金属电镀点缀）",
  "compositionBreakdown": "手办展示台居中构图、全身全景、干净背景与适度微距景深",
  "textureBreakdown": "玩具实物触感材质（哑光树脂、搪胶、珠光漆、半透水晶果冻件）",
  "keywords": ["Blind box toy", "Pop Mart style", "Chibi character", "PVC figure", "Studio lighting", "3D render"]
}`
  }
];

export const AI_ENGINES = [
  { id: 'midjourney', name: 'Midjourney v6.1', prefix: '/imagine prompt: ', suffix: ' --ar 16:9 --v 6.1', badge: 'MJ' },
  { id: 'niji', name: 'Niji Journey v6 (动漫)', prefix: '/imagine prompt: ', suffix: ' --ar 16:9 --niji 6', badge: 'Niji' },
  { id: 'flux', name: 'FLUX.1 (Dev/Schnell)', prefix: '', suffix: '', badge: 'FLUX' },
  { id: 'sdxl', name: 'Stable Diffusion XL', prefix: '', suffix: ', masterpiece, highly detailed', badge: 'SDXL' },
  { id: 'dalle3', name: 'DALL-E 3', prefix: '', suffix: '', badge: 'DALL-E' },
  { id: 'comfyui', name: 'ComfyUI 结构化', prefix: '', suffix: '', badge: 'ComfyUI' },
  { id: 'video_ai', name: '可灵/LTX/Minimax 视频', prefix: '', suffix: ' cinematic movement, high frame rate, 4k', badge: 'Video' }
];
