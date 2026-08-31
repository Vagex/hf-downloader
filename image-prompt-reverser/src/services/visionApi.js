import { CATEGORIES } from './categories';

const API_SETTINGS_KEY = 'image_reverser_api_settings';

export function getStoredApiSettings() {
  try {
    const data = localStorage.getItem(API_SETTINGS_KEY);
    if (data) return JSON.parse(data);
  } catch (e) {
    console.error('Failed to load api settings', e);
  }
  return {
    provider: 'simulation', // 'simulation', 'openai', 'claude', 'gemini', 'custom'
    baseUrl: 'https://api.openai.com/v1',
    apiKey: '',
    model: 'gpt-4o',
    temperature: 0.4,
    detailLevel: 'standard' // 'compact', 'standard', 'deep'
  };
}

export function saveApiSettings(settings) {
  try {
    localStorage.setItem(API_SETTINGS_KEY, JSON.stringify(settings));
  } catch (e) {
    console.error('Failed to save api settings', e);
  }
}

/**
 * Perform Image Reverse Engineering with Vision API or Smart Simulator
 */
export async function reverseImageToPrompt({
  imageDataUrl,
  imageInfo,
  categoryId,
  engineId,
  userNotes = ''
}) {
  const category = CATEGORIES.find(c => c.id === categoryId) || CATEGORIES[0];
  const settings = getStoredApiSettings();

  // If simulation mode or missing key, use high-precision smart generator
  if (settings.provider === 'simulation' || !settings.apiKey) {
    return generateSmartReverseResult(category, imageInfo, engineId, userNotes);
  }

  try {
    // Try sending to server proxy first, or direct API
    const response = await fetch('/api/reverse', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        image: imageDataUrl,
        categoryId: category.id,
        categoryName: category.name,
        systemPrompt: category.systemPrompt,
        engineId,
        userNotes,
        settings: {
          provider: settings.provider,
          baseUrl: settings.baseUrl,
          apiKey: settings.apiKey,
          model: settings.model,
          temperature: settings.temperature
        }
      })
    });

    if (!response.ok) {
      const errJson = await response.json().catch(() => ({}));
      throw new Error(errJson.error || `API 响应错误: ${response.status}`);
    }

    const data = await response.json();
    return data.result;
  } catch (apiError) {
    console.warn('API error, falling back to smart simulation generator:', apiError);
    // If backend isn't running or API key failed, fallback gracefully with a warning
    const fallback = generateSmartReverseResult(category, imageInfo, engineId, userNotes);
    fallback._warning = `API 请求失败 (${apiError.message})，已为您启动智能仿真反推引擎。`;
    return fallback;
  }
}

/**
 * Smart Heuristic Reverse Engineering Generator (Offline & Instant)
 */
function generateSmartReverseResult(category, imageInfo, engineId, userNotes) {
  const paletteText = (imageInfo?.palette || []).map(p => `${p.name}(${p.hex})`).join('、') || '经典配色';
  const ratio = imageInfo?.ratio || '16:9';
  const isSquare = ratio === '1:1';
  const isPortrait = ratio === '3:4' || ratio === '9:16' || ratio === '2:3';

  switch (category.id) {
    case 'typography':
      return {
        chinesePrompt: `高级 3D 文字与 Logo 视觉设计，字形采用现代极简加粗无衬线体，边缘带光滑立体倒角与金属质感。配色方案为 ${paletteText}，文字表面具有镜面反射与渐变发光特效。居中几何对称构图，摄影棚三点布光，纯净极简深色背景，Behance 流行设计，矢量排版，8K 分辨率。${userNotes ? `（用户补充：${userNotes}）` : ''}`,
        englishPrompt: `Modern minimalist 3D typography and logo graphic design, bold sans-serif letterforms with smooth beveled edges, chrome metal and frosted acrylic texture, color palette featuring ${imageInfo?.palette?.[0]?.hex || '#38BDF8'} and ${imageInfo?.palette?.[1]?.hex || '#FFFFFF'}, subtle glowing gradient effects, studio lighting, centered composition, clean slate background, Behance trending, C4D Octane render, vector art, 8k`,
        negativePrompt: `blurry text, ugly fonts, messy strokes, low resolution, artifacts, distorted glyphs`,
        recommendedParams: `--ar ${isSquare ? '1:1' : ratio} --v 6.1 --style raw`,
        subjectBreakdown: `核心文字主体结构饱满，笔画端庄有力，包含立体几何挤压与倒角切割工艺。`,
        styleBreakdown: `现代前沿平面与 3D 视觉设计流派（3D Graphic Design / Branding Identity）。`,
        lightingBreakdown: `摄影棚顶光与双侧冷暖补光，在笔画轮廓形成锐利的镜面反光和内发光辉光。`,
        colorBreakdown: `提取自图像的高级色谱：${paletteText}，色彩层次丰富且对比强烈。`,
        compositionBreakdown: `居中对称平衡排版，主体占据视觉黄金区域，背景留白干净透气。`,
        textureBreakdown: `精密电镀金属拉丝、高透亚克力与边缘微倒角高光质感。`,
        keywords: ["Typography", "3D Logo", "Chrome text", "Bevel edge", "Studio lighting", "Vector design"]
      };

    case 'landscape':
      return {
        chinesePrompt: `宏伟震撼的自然风光摄影大片，呈现开阔地貌与丰富的层叠景深。时段为绝美黄金时刻，天空弥漫着柔和朝霞与体积光晕。主要色调为 ${paletteText}。前景细节清晰丰富，中景主体纵深延展，远景山川云海在光雾中若隐若现。超广角镜头拍摄，大景深，8K 超清细节，国家地理获奖画质。${userNotes ? `（用户补充：${userNotes}）` : ''}`,
        englishPrompt: `Breathtaking cinematic landscape scenery, expansive terrain with dramatic depth of field, golden hour atmospheric volumetric lighting, vibrant sky with soft glowing clouds, palette of ${imageInfo?.palette?.[0]?.hex || '#0EA5E9'} and ${imageInfo?.palette?.[1]?.hex || '#F59E0B'}, crystal reflections and detailed foreground textures, shot on ultra-wide angle lens, deep focus, sharp details, National Geographic award winner, 8k`,
        negativePrompt: `low quality, haze, overexposed, noise, blurry, bad horizon, distortion, artifacts`,
        recommendedParams: `--ar ${isPortrait ? '9:16' : '16:9'} --v 6.1`,
        subjectBreakdown: `开阔的自然地貌空间，远中近三层景深递进，山水与大气云层层次分明。`,
        styleBreakdown: `顶级风光摄影大片与电影级环境美术概念风格。`,
        lightingBreakdown: `低角度自然斜射光（Golden Hour），产生通透的丁达尔体积光与柔和阴影。`,
        colorBreakdown: `以图像提取色彩为基调：${paletteText}，形成大自然独特的冷暖光影交融。`,
        compositionBreakdown: `大纵深透视引导线构图，天地比例适宜，视点宏大开阔。`,
        textureBreakdown: `岩石地表微观纹理、水面波光与空气中微粒晨雾的通透质感。`,
        keywords: ["Landscape photography", "Golden hour", "Volumetric sunbeams", "Ultra-wide angle", "Deep focus", "8K HDR"]
      };

    case 'photography':
      return {
        chinesePrompt: `专业商业摄影大片，使用顶级全画幅相机搭配 85mm f/1.4 镜头拍摄。主体轮廓立体鲜明，眼神与神态生动自然。布光采用大师级伦勃朗光与柔光箱侧光，呈现优美的明暗过渡。色彩呈现 ${paletteText} 的高级电影胶片调色。天然细腻的皮肤毛孔与材质真实触感，奶油般浅景深背景虚化，8K 画质。${userNotes ? `（用户补充：${userNotes}）` : ''}`,
        englishPrompt: `Masterpiece commercial photography, shot on Hasselblad H6D-100c / Sony A7R V with 85mm f/1.4 lens, stunning subject with authentic expressions and detailed pose, softbox Rembrandt studio lighting with subtle rim light, color graded with ${paletteText}, photorealistic natural skin texture, visible fine pores, creamy background bokeh, shallow depth of field, 8k resolution, award-winning portrait`,
        negativePrompt: `plastic skin, smooth doll skin, anime, painting, 3d render, deformed hands, blur, bad eyes`,
        recommendedParams: `--ar ${isPortrait ? '3:4' : '16:9'} --v 6.1 --style raw`,
        subjectBreakdown: `主体人物/静物居于画幅黄金位置，姿态优雅舒展，细节丰富生动。`,
        styleBreakdown: `国际时尚杂志大片（Vogue / GQ 封面级摄影标准）。`,
        lightingBreakdown: `经典商业人像布光（主光柔光箱 + 辅光反光板 + 轮廓发丝光），光比柔和立体。`,
        colorBreakdown: `主基调色谱：${paletteText}，胶片级暗部偏色与高光保留。`,
        compositionBreakdown: `半身/特写取景，利用大光圈实现背景平滑虚化，牢牢聚焦视觉中心。`,
        textureBreakdown: `毛孔肌理、发丝细节、服饰布料织物经纬度与镜面反光的真实物理还原。`,
        keywords: ["Portrait photography", "85mm f/1.4", "Rembrandt lighting", "Skin texture", "Creamy bokeh", "Photorealistic"]
      };

    case 'illustration':
      return {
        chinesePrompt: `精致唯美的二次元插画与数字绘画，画风细腻通透。线条流畅优美，色彩搭配呈现 ${paletteText} 的治愈梦幻感。光影处理通透璀璨，带有清澈的边缘发光与氛围光晕。赛璐璐与精细平涂结合，背景细节层次丰富，充满故事叙事感，Pixiv 热门榜首作品，8K 超清画质。${userNotes ? `（用户补充：${userNotes}）` : ''}`,
        englishPrompt: `Exquisite aesthetic anime illustration and digital concept painting, delicate and fluent lineart, captivating atmosphere with color palette of ${paletteText}, translucent glowing rim lights, soft particles and dreamy lens flare, cel shaded with subtle watercolor texture, Pixiv trending, masterpiece, highres, highly detailed background`,
        negativePrompt: `photorealistic, 3d, realistic photo, bad anatomy, deformed eyes, messy lines, lowres, blurry`,
        recommendedParams: `--ar ${isPortrait ? '9:16' : '16:9'} --niji 6 --style expressive`,
        subjectBreakdown: `二次元人物形象生动，动态线条飘逸，发型与服装具有鲜明的设计感。`,
        styleBreakdown: `日系新海诚 / Pixiv 殿堂级插画与治愈系数字动漫艺术风格。`,
        lightingBreakdown: `梦幻逆光与边缘轮廓光晕（Rim Light），伴随微小漂浮光斑与通透发丝透光。`,
        colorBreakdown: `画面主要取色：${paletteText}，马卡龙清新色与高通透冷暖互补。`,
        compositionBreakdown: `动势透视对角线构图，大面积天空/场景留白与主体人物的情绪呼应。`,
        textureBreakdown: `细致手绘铅笔勾线质感、赛璐璐分层平涂与局部水彩晕染肌理。`,
        keywords: ["Anime illustration", "Cel shaded", "Delicate lineart", "Pixiv trending", "Translucent lighting", "Masterpiece"]
      };

    case '3d_render':
      return {
        chinesePrompt: `现代高端 3D 渲染与 C4D / Blender 三维视觉大作，Octane 物理光线追踪渲染。几何形态饱满光滑，材质融合了磨砂亚克力、高光金属与半透明次表面散射（SSS）。配色为 ${paletteText}。摄影棚三点布光系统，柔和环境遮蔽（AO）与地面微弱倒影，Behance 3D 热门推荐，8K 超精细度。${userNotes ? `（用户补充：${userNotes}）` : ''}`,
        englishPrompt: `High-end 3D render, crafted with Cinema 4D and Blender, rendered in Octane Render with realistic ray-tracing, smooth geometric shapes, PBR materials including frosted glass, polished chrome metal, and soft matte plastic, color scheme featuring ${paletteText}, studio three-point lighting, subsurface scattering, ambient occlusion, clean pedestal background, Behance 3D trending, 8k`,
        negativePrompt: `flat 2d, hand drawing, noisy render, low poly, bad geometry, jagged edges, ugly textures`,
        recommendedParams: `--ar ${isSquare ? '1:1' : '16:9'} --v 6.1 --style raw`,
        subjectBreakdown: `严谨的三维硬表面或有机流体几何造型，曲率连续平滑，倒角圆润精密。`,
        styleBreakdown: `前沿商业 3D 视觉艺术（C4D / Octane / Redshift 极简风格）。`,
        lightingBreakdown: `摄影棚标准化三点布光（Key Light, Fill Light, Rim Light）配高动态 HDR 环境光。`,
        colorBreakdown: `三维物理提取色：${paletteText}，材质反射与色散过渡自然。`,
        compositionBreakdown: `等轴测视角（Isometric）或中心微仰角构图，空间结构均衡有序。`,
        textureBreakdown: `真实物理 PBR 材质属性（粗糙度、反射率、折射率及次表面散射）。`,
        keywords: ["3D render", "Cinema 4D", "Octane render", "PBR materials", "Subsurface scattering", "Behance 3D"]
      };

    case 'ip_character':
      return {
        chinesePrompt: `泡泡玛特风格潮玩盲盒公仔，2头身超可爱 Q 版 IP 角色设定。面部五官萌趣圆润，大眼睛富有灵气。身穿特色潮流服饰与精致配件。采用哑光树脂与高光 PVC 亲肤材质，站立在纯色展示台上。配色为 ${paletteText}。摄影棚柔光漫射，C4D 3D 渲染，治愈可爱，高细节手办，8K。${userNotes ? `（用户补充：${userNotes}）` : ''}`,
        englishPrompt: `Pop Mart blind box designer toy style, adorable chibi 2-heads-tall IP character figurine, charming facial expression with big glossy eyes, wearing stylish cute outfit and accessories, standing on a minimalist round pedestal, soft matte vinyl PVC and glossy resin materials, studio softbox lighting, color palette of ${paletteText}, C4D Octane 3D render, ultra-detailed, healing, 8k`,
        negativePrompt: `2d illustration, human realistic skin, scary look, deformed limbs, messy background, low poly`,
        recommendedParams: `--ar 1:1 --v 6.1 --stylize 250`,
        subjectBreakdown: `2头身 Q 版潮玩公仔，大头萌系体态，圆润饱满的手脚比例与生动造型。`,
        styleBreakdown: `泡泡玛特（Pop Mart）/ 寻找独角兽盲盒玩具与潮玩手办流派。`,
        lightingBreakdown: `玩具摄影棚 360 度环形漫射柔光，柔和的高光过渡与清爽微阴影。`,
        colorBreakdown: `活力与治愈并存的玩具配色：${paletteText}。`,
        compositionBreakdown: `正视居中全身特写，放置于圆形独立展台，极简单色背景。`,
        textureBreakdown: `哑光搪胶/PVC、微透果冻件与精密注塑光泽的实物玩具手感。`,
        keywords: ["Blind box toy", "Pop Mart style", "Chibi character", "Vinyl PVC figure", "Studio soft light", "Cute IP"]
      };

    default: // General
      return {
        chinesePrompt: `高品质大师级视觉作品，全要素精准呈现。画面主体形象鲜明突出，艺术风格严谨考究。色调呈现 ${paletteText} 的和谐共鸣。光影富有戏剧性冷暖明暗对比，构图比例严谨，景深层次分明。细节丰富质感真实，8K 超高清分辨率，极致精细度。${userNotes ? `（用户补充：${userNotes}）` : ''}`,
        englishPrompt: `Masterpiece, ultra-high quality, stunning visual artwork, [subject in center focus], dramatic cinematic lighting with rich depth, harmonious color palette of ${paletteText}, meticulous composition with perfect balance, exquisite surface textures, sharp focus, 8k resolution, award-winning`,
        negativePrompt: `low quality, blurry, distorted, deformed, artifacts, watermark, signature`,
        recommendedParams: `--ar ${ratio} --v 6.1`,
        subjectBreakdown: `核心主体位于画幅视觉中心，空间前后层次错落有序。`,
        styleBreakdown: `融合现代数字概念艺术与写实渲染的综合视觉流派。`,
        lightingBreakdown: `主光源方向明确，辅以环境漫射光与轮廓高光，层次丰富。`,
        colorBreakdown: `画面主基调：${paletteText}，色彩饱和度与冷暖搭配平衡。`,
        compositionBreakdown: `基于黄金分割与视线引导线的严谨构图，透视与景深控制得当。`,
        textureBreakdown: `微观表面纹理细腻，材质物理光泽与阴影过渡自然真实。`,
        keywords: ["Masterpiece", "Cinematic lighting", "8K resolution", "Ultra-detailed", "Award-winning"]
      };
  }
}
