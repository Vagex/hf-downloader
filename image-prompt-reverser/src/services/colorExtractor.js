/**
 * Extracts dominant color palette and basic image metrics from an Image object or Data URL using HTML5 Canvas
 */
export async function extractImageInfo(imageSrc) {
  return new Promise((resolve) => {
    const img = new Image();
    img.crossOrigin = 'Anonymous';
    img.onload = () => {
      try {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        // Resize for quick pixel analysis
        const sampleWidth = 100;
        const sampleHeight = 100;
        canvas.width = sampleWidth;
        canvas.height = sampleHeight;
        ctx.drawImage(img, 0, 0, sampleWidth, sampleHeight);

        const imgData = ctx.getImageData(0, 0, sampleWidth, sampleHeight).data;
        const colorMap = {};
        const colors = [];

        // Sample pixels with step 4 for speed
        for (let i = 0; i < imgData.length; i += 16) {
          const r = imgData[i];
          const g = imgData[i + 1];
          const b = imgData[i + 2];
          const a = imgData[i + 3];

          // Skip nearly transparent pixels
          if (a < 128) continue;

          // Quantize color to 16-step buckets
          const qr = Math.round(r / 24) * 24;
          const qg = Math.round(g / 24) * 24;
          const qb = Math.round(b / 24) * 24;
          const hex = `#${((1 << 24) + (qr << 16) + (qg << 8) + qb).toString(16).slice(1).toUpperCase()}`;

          colorMap[hex] = (colorMap[hex] || 0) + 1;
        }

        // Sort by frequency
        const sortedColors = Object.entries(colorMap)
          .sort((a, b) => b[1] - a[1])
          .slice(0, 5)
          .map(([hex]) => ({
            hex,
            name: getColorName(hex)
          }));

        // Calculate aspect ratio string
        const gcd = (a, b) => (b === 0 ? a : gcd(b, a % b));
        const divisor = gcd(img.naturalWidth, img.naturalHeight);
        let ratioW = Math.round(img.naturalWidth / divisor);
        let ratioH = Math.round(img.naturalHeight / divisor);

        // Approximate standard ratios
        let standardRatio = '1:1';
        const rawRatio = img.naturalWidth / img.naturalHeight;
        if (Math.abs(rawRatio - 1.777) < 0.15) standardRatio = '16:9';
        else if (Math.abs(rawRatio - 0.5625) < 0.15) standardRatio = '9:16';
        else if (Math.abs(rawRatio - 1.333) < 0.15) standardRatio = '4:3';
        else if (Math.abs(rawRatio - 0.75) < 0.15) standardRatio = '3:4';
        else if (Math.abs(rawRatio - 1.5) < 0.15) standardRatio = '3:2';
        else if (Math.abs(rawRatio - 0.666) < 0.15) standardRatio = '2:3';
        else if (Math.abs(rawRatio - 1) < 0.1) standardRatio = '1:1';
        else standardRatio = `${ratioW}:${ratioH}`;

        resolve({
          width: img.naturalWidth,
          height: img.naturalHeight,
          ratio: standardRatio,
          palette: sortedColors.length > 0 ? sortedColors : [
            { hex: '#1E293B', name: '深蓝灰' },
            { hex: '#0EA5E9', name: '天空蓝' },
            { hex: '#F8FAFC', name: '纯白' }
          ]
        });
      } catch (err) {
        console.warn('Palette extraction fallback:', err);
        resolve({
          width: img.naturalWidth || 1024,
          height: img.naturalHeight || 1024,
          ratio: '1:1',
          palette: [
            { hex: '#3B82F6', name: '经典蓝' },
            { hex: '#10B981', name: '翡翠绿' },
            { hex: '#F59E0B', name: '琥珀金' }
          ]
        });
      }
    };
    img.onerror = () => {
      resolve({
        width: 1024,
        height: 1024,
        ratio: '1:1',
        palette: [{ hex: '#3B82F6', name: '经典蓝' }]
      });
    };
    img.src = imageSrc;
  });
}

function getColorName(hex) {
  const c = hexToRgb(hex);
  if (!c) return '色彩';
  const { r, g, b } = c;

  if (r > 230 && g > 230 && b > 230) return '纯净白';
  if (r < 35 && g < 35 && b < 35) return '深邃黑';
  if (Math.abs(r - g) < 20 && Math.abs(g - b) < 20 && Math.abs(r - b) < 20) return '高级灰';

  if (r > g && r > b) {
    if (g > 150 && b < 80) return '暖橙色';
    if (g > 180 && b < 100) return '明黄色';
    if (b > 120) return '品红色/粉紫';
    return '赤红/深红';
  } else if (g > r && g > b) {
    if (b > 150) return '青碧色/湖蓝';
    if (r > 150) return '嫩草绿/黄绿';
    return '翠绿/深绿';
  } else {
    if (r > 150) return '梦幻紫/罗兰';
    if (g > 150) return '湛蓝/天青';
    return '深海蓝/群青';
  }
}

function hexToRgb(hex) {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result ? {
    r: parseInt(result[1], 16),
    g: parseInt(result[2], 16),
    b: parseInt(result[3], 16)
  } : null;
}
