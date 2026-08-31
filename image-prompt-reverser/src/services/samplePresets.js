/**
 * Built-in Preset Images & Reverse Engineered Prompts for all 7 Categories
 */

const createSvgDataUrl = (svgString) => `data:image/svg+xml;utf8,${encodeURIComponent(svgString)}`;

export const SAMPLE_PRESETS = [
  {
    id: 'preset-general-1',
    categoryId: 'general',
    title: '赛博朋克雨夜未来机甲少女',
    subtitle: '通用全要素拆解范例',
    image: createSvgDataUrl(`
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" width="100%" height="100%">
        <defs>
          <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#090d16" />
            <stop offset="50%" stop-color="#111827" />
            <stop offset="100%" stop-color="#1e1035" />
          </linearGradient>
          <linearGradient id="neon" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#06b6d4" />
            <stop offset="50%" stop-color="#3b82f6" />
            <stop offset="100%" stop-color="#d946ef" />
          </linearGradient>
          <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="8" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        <rect width="800" height="600" fill="url(#bg)" />
        <circle cx="400" cy="280" r="160" fill="url(#neon)" opacity="0.15" filter="url(#glow)" />
        <path d="M 280 480 L 350 250 L 450 250 L 520 480 Z" fill="#1e293b" stroke="#06b6d4" stroke-width="3" />
        <circle cx="400" cy="220" r="45" fill="#f8fafc" opacity="0.9" />
        <path d="M 330 220 C 330 150 470 150 470 220 Z" fill="#d946ef" opacity="0.8" />
        <line x1="100" y1="520" x2="700" y2="520" stroke="#06b6d4" stroke-width="4" filter="url(#glow)" />
        <text x="400" y="560" fill="#94a3b8" font-family="sans-serif" font-size="18" text-anchor="middle">CYBERPUNK MECHA HEROINE · 8K HDR</text>
      </svg>
    `),
    result: {
      chinesePrompt: "赛博朋克机甲少女，站立在潮湿反光的雨夜未来都市街头，霓虹全息光影闪烁，青色与品红冷暖对比色调。精密钛合金机械外骨骼装甲，流线型发光管线，半透明发光面罩。细密雨丝与地面水洼倒影，电影级宽银幕镜头，大景深虚化，8K超精细画质，虚幻引擎5渲染。",
      englishPrompt: "Cinematic portrait of a cyberpunk mecha heroine standing in a neon-lit futuristic rainy street, glowing cybernetic exo-suit, intricate titanium armor, holographic cyan and magenta reflections on wet asphalt, volumetric mist, rain streaks, shallow depth of field, shot on 85mm lens, photorealistic, 8k resolution, Unreal Engine 5 render, trending on ArtStation",
      negativePrompt: "low quality, blurry, deformed armor, bad anatomy, text, watermark, oversaturated",
      recommendedParams: "--ar 16:9 --v 6.1 --style raw",
      subjectBreakdown: "未来机甲少女单人立姿，身着流线型发光外骨骼装甲与科技感兜帽，位于画面黄金分割中心。",
      styleBreakdown: "电影级赛博朋克科幻美学，融合了写实光追渲染与数字概念艺术风格。",
      lightingBreakdown: "双色霓虹边缘轮廓光（青蓝与品红），湿滑地面的高反光漫射与自发光机甲细节。",
      colorBreakdown: "暗黑冷夜底色（#090D16），辅以高饱和青蓝（#06B6D4）与紫粉（#D946EF）电光色调。",
      compositionBreakdown: "经典三分法主体居中构图，低机位微仰视增强英雄气场，纵深街道透视线条。",
      textureBreakdown: "金属拉丝拉光、玻璃高透材质、雨滴水渍质感与漆皮反光。",
      keywords: ["Cyberpunk", "Mecha heroine", "Neon reflections", "Wet street", "Volumetric lighting", "8K resolution"]
    }
  },
  {
    id: 'preset-typography-1',
    categoryId: 'typography',
    title: '液态流动金属 3D 字体设计',
    subtitle: '字体/Logo/文字质感特效',
    image: createSvgDataUrl(`
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="100%" height="100%">
        <defs>
          <linearGradient id="chrome" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#ffffff" />
            <stop offset="25%" stop-color="#94a3b8" />
            <stop offset="50%" stop-color="#f1f5f9" />
            <stop offset="75%" stop-color="#475569" />
            <stop offset="100%" stop-color="#ffffff" />
          </linearGradient>
        </defs>
        <rect width="600" height="600" fill="#020617" />
        <circle cx="300" cy="300" r="220" fill="none" stroke="#38bdf8" stroke-width="1.5" stroke-dasharray="8,8" opacity="0.3" />
        <text x="300" y="340" fill="url(#chrome)" font-family="Arial, sans-serif" font-weight="900" font-size="120" text-anchor="middle" letter-spacing="8">FUTURE</text>
        <text x="300" y="420" fill="#38bdf8" font-family="sans-serif" font-size="16" text-anchor="middle" letter-spacing="4">LIQUID CHROME 3D TYPOGRAPHY</text>
      </svg>
    `),
    result: {
      chinesePrompt: "现代无衬线 3D 铬合金液态金属字体设计，粗壮饱满字形，圆润平滑倒角，极致镜面反射与色散高光。文字呈现流动流体熔融金属质感，纯黑极简背景，摄影棚三点布光，清爽冷色边缘辉光，Behance 流行设计，矢量排版，8K 高分辨率。",
      englishPrompt: "Modern bold sans-serif 3D liquid chrome typography design, word 'FUTURE', smooth rounded bevel edges, ultra-reflective mercury chrome metal texture, soft chromatic aberration highlights, floating on pitch black minimalist background, studio three-point lighting, clean graphic design, Behance trending, C4D Octane render, 8k",
      negativePrompt: "blurry strokes, messy text, pixelated, jagged edges, low resolution, ugly letters",
      recommendedParams: "--ar 1:1 --v 6.1 --style raw",
      subjectBreakdown: "单行大写英文字体，笔画加粗几何无衬线，厚重立体 3D 挤压字形。",
      styleBreakdown: "Y2K 未来主义与液态铬金属（Liquid Chrome）前沿平面视觉风格。",
      lightingBreakdown: "顶部柔光箱主光配合底部反射板，字形边缘呈现高强度镜面高光与锐利反光线。",
      colorBreakdown: "高对比度铬银色阶（#FFFFFF 至 #475569），配纯黑背景与微量冷青色散。",
      compositionBreakdown: "纯正居中对称排版，四周留白充足，字体占画面中央 60% 视觉权重。",
      textureBreakdown: "无瑕疵高光镜面、微观色散（Dispersion）与液态张力曲面倒角。",
      keywords: ["Liquid chrome", "3D typography", "Bold sans-serif", "Chrome reflection", "Minimalist black", "Behance"]
    }
  },
  {
    id: 'preset-landscape-1',
    categoryId: 'landscape',
    title: '阿尔卑斯雪山日出金色时刻',
    subtitle: '自然风景大片全要素反推',
    image: createSvgDataUrl(`
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 500" width="100%" height="100%">
        <defs>
          <linearGradient id="sky" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#1e1b4b" />
            <stop offset="40%" stop-color="#db2777" />
            <stop offset="80%" stop-color="#f59e0b" />
            <stop offset="100%" stop-color="#fef08a" />
          </linearGradient>
        </defs>
        <rect width="800" height="500" fill="url(#sky)" />
        <polygon points="100,320 280,140 460,320" fill="#334155" />
        <polygon points="280,140 340,210 280,230 220,210" fill="#f8fafc" opacity="0.9" />
        <polygon points="340,350 520,110 700,350" fill="#1e293b" />
        <polygon points="520,110 590,190 520,210 450,190" fill="#fef08a" opacity="0.9" />
        <rect y="320" width="800" height="180" fill="#0f172a" opacity="0.8" />
        <path d="M 0 360 Q 400 330 800 360 L 800 500 L 0 500 Z" fill="#0369a1" opacity="0.7" />
        <text x="400" y="470" fill="#fef08a" font-family="sans-serif" font-size="16" text-anchor="middle" letter-spacing="3">ALPS GOLDEN HOUR SUNRISE · 8K</text>
      </svg>
    `),
    result: {
      chinesePrompt: "壮丽的阿尔卑斯雪山日出绝景，晨曦第一缕金光点亮嶙峋积雪山巅（日照金山）。山脚下如镜面般清澈的冰川高山湖泊，完美倒映着晚霞天空与金黄山峰。薄雾在针叶林间缭绕，朝霞呈现紫红到暖金的壮美渐变。超广角风光摄影，大景深，8K 超高清分辨率，国家地理风范。",
      englishPrompt: "Breathtaking landscape photography of jagged snowy Alpine mountain peaks illuminated by golden hour sunrise (Alpenglow), crystal clear glacial alpine lake with perfect mirror reflection, misty pine forest in the foreground, vibrant dawn gradient sky from deep violet to warm amber, ultra-wide angle, deep focus, sharp details, National Geographic award winner, 8k",
      negativePrompt: "blurry, low dynamic range, overexposed, noise, smog, artificial saturation",
      recommendedParams: "--ar 16:9 --v 6.1",
      subjectBreakdown: "远景主峰尖锐雪山、中景晨雾针叶林、近景平静如镜的冰川湖泊。",
      styleBreakdown: "顶级国家地理风光大片，自然写实主义与极致纯净画质。",
      lightingBreakdown: "日出金色时刻（Golden Hour）低角度暖阳斜射，冷调蓝阴影与高光金顶强烈对比。",
      colorBreakdown: "暖金（#FEF08A / #F59E0B）与冷蓝青（#1E1B4B / #0369A1）的经典风光互补配色。",
      compositionBreakdown: "经典三分法横向构图，地平线居中，利用湖面倒影形成上下呼应的对称美学。",
      textureBreakdown: "积雪冰川微观颗粒、岩石风化断层、水面微波与松针针叶细节。",
      keywords: ["Alps landscape", "Alpenglow", "Golden hour", "Glacial lake reflection", "Ultra-wide", "8K HDR"]
    }
  },
  {
    id: 'preset-photography-1',
    categoryId: 'photography',
    title: '高端时尚杂志人像大片',
    subtitle: '摄影镜头参数与胶片感反推',
    image: createSvgDataUrl(`
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 800" width="100%" height="100%">
        <defs>
          <linearGradient id="skin" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#fed7aa" />
            <stop offset="100%" stop-color="#fb923c" />
          </linearGradient>
        </defs>
        <rect width="600" height="800" fill="#18181b" />
        <circle cx="300" cy="320" r="140" fill="url(#skin)" />
        <path d="M 160 800 C 160 500 440 500 440 800 Z" fill="#09090b" />
        <ellipse cx="300" cy="200" rx="150" ry="90" fill="#27272a" />
        <line x1="180" y1="260" x2="220" y2="420" stroke="#f59e0b" stroke-width="6" opacity="0.7" />
        <text x="300" y="730" fill="#a1a1aa" font-family="sans-serif" font-size="16" text-anchor="middle" letter-spacing="4">VOGUE EDITORIAL · 85MM F/1.4</text>
      </svg>
    `),
    result: {
      chinesePrompt: "高级时装杂志人像摄影，使用索尼 A7R V 搭配 85mm f/1.4 镜头拍摄。模特半身特写，眼神清澈自信，面部立体轮廓光（伦勃朗布光法），柔光箱侧光营造优雅阴影过渡。真实细腻的皮肤毛孔纹理，无过度磨皮。柯达 Portra 400 胶片暖调色彩，背景深邃虚化，8K 画质。",
      englishPrompt: "Vogue editorial high-fashion portrait photography, shot on Sony A7R V with 85mm f/1.4 GM lens, elegant female model, half-body close-up, confident gaze, Rembrandt lighting with softbox side fill, golden rim light, authentic natural skin texture with visible pores, Kodak Portra 400 film grain tone, creamy bokeh background, 8k resolution, photorealistic",
      negativePrompt: "plastic smooth skin, anime, painting, 3d render, deformed fingers, blur, over-retouched",
      recommendedParams: "--ar 3:4 --v 6.1 --style raw",
      subjectBreakdown: "单人时尚模特半身肖像，微侧脸 45 度视角，极简高级剪裁黑色高领服饰。",
      styleBreakdown: "高端商业时尚人像大片（Vogue / Harper's Bazaar 封面美学）。",
      lightingBreakdown: "主光 45 度柔光箱 + 背后暖色轮廓光，形成面部清晰倒三角高光区（伦勃朗光）。",
      colorBreakdown: "柯达经典胶片暖黄肤色调（#FED7AA），搭配深黑（#18181B）高对比背景。",
      compositionBreakdown: "竖构图紧凑半身特写，眼睛置于上方三分之一黄金分割线上，浅景深奶油虚化。",
      textureBreakdown: "极致写实的天然皮肤毛孔、发丝根根分明、高级面料织物纹理与微量胶片颗粒感。",
      keywords: ["Fashion portrait", "85mm f/1.4", "Kodak Portra 400", "Rembrandt lighting", "Skin texture", "Creamy bokeh"]
    }
  },
  {
    id: 'preset-illustration-1',
    categoryId: 'illustration',
    title: '新海诚风治愈系唯美二次元',
    subtitle: '插画/二次元/光影氛围反推',
    image: createSvgDataUrl(`
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 500" width="100%" height="100%">
        <defs>
          <linearGradient id="animeSky" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#0284c7" />
            <stop offset="60%" stop-color="#38bdf8" />
            <stop offset="100%" stop-color="#fbcfe8" />
          </linearGradient>
        </defs>
        <rect width="800" height="500" fill="url(#animeSky)" />
        <ellipse cx="600" cy="200" rx="140" ry="70" fill="#ffffff" opacity="0.9" />
        <ellipse cx="680" cy="180" rx="100" ry="50" fill="#ffffff" opacity="0.9" />
        <polygon points="0,500 200,340 500,500" fill="#16a34a" opacity="0.8" />
        <polygon points="300,500 600,320 800,500" fill="#15803d" />
        <circle cx="280" cy="380" r="16" fill="#f43f5e" />
        <text x="400" y="470" fill="#ffffff" font-family="sans-serif" font-size="16" text-anchor="middle" letter-spacing="3">MAKOTO SHINKAI STYLE · ANIME ART</text>
      </svg>
    `),
    result: {
      chinesePrompt: "新海诚唯美治愈系二次元插画，蔚蓝晴空与层叠涌动的巨大积雨云，夕阳微泛粉白光晕。翠绿草坡在微风中摇曳，少女身穿水手服背影迎风伫立。精致细腻的赛璐璐线条，通透清澈的光影渲染，丁达尔光柱穿透云层，Pixiv 热门榜首，8K 超清壁纸画质。",
      englishPrompt: "Stunning Makoto Shinkai aesthetic anime illustration, magnificent towering cumulonimbus clouds in vibrant azure sky, soft pink sunset glow, lush green grassy hill fluttering in summer breeze, schoolgirl in sailor uniform standing gazing into distance, clean delicate lineart, translucent crystal lighting, volumetric sunbeams, Pixiv trending, masterpiece, highres",
      negativePrompt: "photorealistic, 3d, realistic photo, blurry, bad lineart, dull colors, low quality",
      recommendedParams: "--ar 16:9 --niji 6 --style expressive",
      subjectBreakdown: "夏日山丘上的水手服少女背影与占据画面 70% 的壮丽天空云海。",
      styleBreakdown: "日系新海诚 / 吉卜力电影动画唯美插画，高通透度治愈系二次元风格。",
      lightingBreakdown: "逆光与侧光结合，穿透云朵的体积光晕（God rays），高反差通透发光效果。",
      colorBreakdown: "澄澈天蓝（#0284C7）、马卡龙粉（#FBCFE8）与饱满草绿（#16A34A）。",
      compositionBreakdown: "仰视大空间构图，天空占绝对主体，人物作为情感锚点位于左下方黄金位置。",
      textureBreakdown: "轻盈半透明云层笔触、柔和赛璐璐渐变、纤细平滑的深色轮廓勾线。",
      keywords: ["Makoto Shinkai", "Anime scenery", "Cumulonimbus cloud", "Cel shaded", "Pixiv trending", "Healing"]
    }
  },
  {
    id: 'preset-3d-1',
    categoryId: '3d_render',
    title: 'C4D 磨砂玻璃与金属极简几何装置',
    subtitle: '3D 渲染与 Octane 材质反推',
    image: createSvgDataUrl(`
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="100%" height="100%">
        <defs>
          <linearGradient id="metal" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#f59e0b" />
            <stop offset="100%" stop-color="#d97706" />
          </linearGradient>
        </defs>
        <rect width="600" height="600" fill="#0f172a" />
        <circle cx="300" cy="300" r="160" fill="#38bdf8" opacity="0.3" stroke="#e0f2fe" stroke-width="2" />
        <rect x="220" y="220" width="160" height="160" rx="20" fill="url(#metal)" />
        <circle cx="380" cy="220" r="50" fill="#f43f5e" opacity="0.8" />
        <text x="300" y="540" fill="#94a3b8" font-family="sans-serif" font-size="14" text-anchor="middle" letter-spacing="3">C4D + OCTANE RENDER · PBR MATERIALS</text>
      </svg>
    `),
    result: {
      chinesePrompt: "现代极简 3D 抽象几何装置艺术，Cinema 4D 建模，Octane 物理渲染。包含半透明磨砂亚克力玻璃球体、高光拉丝电镀黄铜立方体与亮粉色悬浮球。摄影棚三点柔光布设，真实的次表面散射（SSS）与柔和漫反射环境遮蔽（AO），纯净深灰展示台，Behance 3D 热门作品，8K 分辨率。",
      englishPrompt: "Cinema 4D and Blender 3D render, minimalist abstract geometric composition, rendered in Octane Render with ray-tracing, frosted glass sphere with subsurface scattering, polished brass metallic cube with beveled edges, floating pastel pink sphere, studio softbox three-point lighting, clean slate pedestal, ambient occlusion, Behance 3D trending, 8k",
      negativePrompt: "flat 2d, hand drawn, noisy render, low poly, jagged edges, oversaturated, ugly materials",
      recommendedParams: "--ar 1:1 --v 6.1 --style raw",
      subjectBreakdown: "多材质三维几何体错落悬浮排布（球体、倒角立方体、环形）。",
      styleBreakdown: "现代高端 3D 商业视觉美学（Behance / Dribbble 3D 风格）。",
      lightingBreakdown: "三点影棚布光系统，大面积柔光箱提供柔和阴影与通透环境光。",
      colorBreakdown: "科技蓝磨砂（#38BDF8）、电镀金（#F59E0B）与高级深灰底座（#0F172A）。",
      compositionBreakdown: "等轴测视图（Isometric）或中心对称悬浮构图，极度平衡与秩序感。",
      textureBreakdown: "高精度 PBR 材质：磨砂玻璃微表面粗糙度（Roughness 0.2）、金属各向异性高光。",
      keywords: ["3D render", "Cinema 4D", "Octane render", "Frosted glass", "PBR metal", "Three-point lighting"]
    }
  },
  {
    id: 'preset-ip-1',
    categoryId: 'ip_character',
    title: '泡泡玛特风潮玩宇航员盲盒公仔',
    subtitle: 'IP 角色与 Q 版潮玩手办反推',
    image: createSvgDataUrl(`
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="100%" height="100%">
        <defs>
          <linearGradient id="suit" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#ffffff" />
            <stop offset="100%" stop-color="#e2e8f0" />
          </linearGradient>
        </defs>
        <rect width="600" height="600" fill="#fef3c7" />
        <circle cx="300" cy="240" r="110" fill="url(#suit)" stroke="#cbd5e1" stroke-width="3" />
        <ellipse cx="300" cy="240" rx="70" ry="50" fill="#3b82f6" opacity="0.85" />
        <circle cx="320" cy="230" r="14" fill="#ffffff" opacity="0.9" />
        <rect x="220" y="340" width="160" height="150" rx="40" fill="url(#suit)" />
        <ellipse cx="300" cy="510" rx="160" ry="25" fill="#fde68a" />
        <text x="300" y="560" fill="#b45309" font-family="sans-serif" font-size="14" text-anchor="middle" letter-spacing="3">POP MART BLIND BOX TOY · 3D CHIBI IP</text>
      </svg>
    `),
    result: {
      chinesePrompt: "泡泡玛特风格潮玩盲盒公仔，2头身超萌 Q 版宇航员小男孩。圆润大头与大眼睛反光面罩，身穿白色极简机能风宇航服，胸前配有荧光色科技徽章与小背包。站立在纯色鹅黄色圆形展示台上。哑光树脂配合高光透明面罩质感，摄影棚柔光漫射，C4D 3D 渲染，治愈可爱，高细节手办，8K。",
      englishPrompt: "Pop Mart designer toy blind box figurine, cute chibi 2-heads-tall astronaut boy, glossy blue visor helmet with reflection, wearing minimalist white ceramic textured space suit with cyber badge details, standing on warm yellow round display pedestal, studio soft lighting, smooth matte vinyl PVC and glossy glass materials, C4D Octane 3D render, adorable, highly detailed, 8k",
      negativePrompt: "2d illustration, realistic human skin, terrifying look, deformed arms, messy background, low poly",
      recommendedParams: "--ar 1:1 --v 6.1 --stylize 250",
      subjectBreakdown: "2头身比例 Q 版宇航员玩具手办，头部圆润大头娃娃造型，立于圆形展示底座。",
      styleBreakdown: "泡泡玛特（Pop Mart）/ 寻找独角兽风格潮玩手办与盲盒公仔设计。",
      lightingBreakdown: "玩具摄影棚 360 度柔和环形漫射光，无死角干净高光，柔和微阴影。",
      colorBreakdown: "治愈奶白色（#FFFFFF）、高亮电光蓝（#3B82F6）与暖鹅黄底座（#FEF3C7）。",
      compositionBreakdown: "正视微俯角展示台居中构图，全身像，干净极简纯色背景。",
      textureBreakdown: "哑光搪胶/PVC 亲肤手感、头盔高透高光亚克力材质、精密注塑合模线细节。",
      keywords: ["Blind box toy", "Pop Mart style", "Chibi astronaut", "Vinyl figure", "Studio lighting", "Adorable IP"]
    }
  }
];
