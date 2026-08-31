import express from 'express';
import cors from 'cors';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3005;

// Middleware
app.use(cors());
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

// Health Check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', time: new Date().toISOString() });
});

/**
 * Universal Vision API Proxy Route
 */
app.post('/api/reverse', async (req, res) => {
  try {
    const { image, categoryId, categoryName, systemPrompt, engineId, userNotes, settings } = req.body;

    if (!image) {
      return res.status(400).json({ error: '请上传有效图像' });
    }

    const provider = settings?.provider || 'openai';
    const apiKey = settings?.apiKey || process.env.VISION_API_KEY;
    const baseUrl = settings?.baseUrl || 'https://api.openai.com/v1';
    const model = settings?.model || 'gpt-4o';
    const temperature = Number(settings?.temperature) || 0.4;

    if (!apiKey && provider !== 'simulation') {
      return res.status(400).json({ error: '未配置 API Key，请在右上角设置中填写密钥或选择仿真模式。' });
    }

    let parsedResult = null;

    // 1. OpenAI / OpenAI Compatible
    if (provider === 'openai' || provider === 'custom' || provider === 'deepseek') {
      const url = `${baseUrl.replace(/\/$/, '')}/chat/completions`;
      
      const payload = {
        model,
        temperature,
        response_format: { type: "json_object" },
        messages: [
          {
            role: "system",
            content: `${systemPrompt}\n\n请务必只返回合法 JSON，不要返回 markdown 代码块以外的任何无关文本。`
          },
          {
            role: "user",
            content: [
              {
                type: "text",
                text: `请针对这张图片，执行【${categoryName}】维度的深度反推与精准提示词生成。${userNotes ? `\n用户特别要求：${userNotes}` : ''}`
              },
              {
                type: "image_url",
                image_url: {
                  url: image
                }
              }
            ]
          }
        ]
      };

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${apiKey}`
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errText = await response.text();
        throw new Error(`OpenAI API 响应失败 (${response.status}): ${errText}`);
      }

      const data = await response.json();
      const content = data.choices?.[0]?.message?.content || '{}';
      parsedResult = extractJsonFromText(content);
    } 
    // 2. Claude (Anthropic)
    else if (provider === 'claude') {
      const url = `${baseUrl.replace(/\/$/, '')}/messages`;
      
      // Parse data URL for Claude
      const base64Data = image.split(',')[1];
      const mediaType = image.split(';')[0].split(':')[1] || 'image/jpeg';

      const payload = {
        model,
        max_tokens: 2000,
        temperature,
        system: systemPrompt,
        messages: [
          {
            role: "user",
            content: [
              {
                type: "image",
                source: {
                  type: "base64",
                  media_type: mediaType,
                  data: base64Data
                }
              },
              {
                type: "text",
                text: `请针对此图执行【${categoryName}】反推，以纯 JSON 格式输出。${userNotes ? `用户补充: ${userNotes}` : ''}`
              }
            ]
          }
        ]
      };

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': apiKey,
          'anthropic-version': '2023-06-01'
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errText = await response.text();
        throw new Error(`Claude API 响应失败 (${response.status}): ${errText}`);
      }

      const data = await response.json();
      const content = data.content?.[0]?.text || '{}';
      parsedResult = extractJsonFromText(content);
    }
    // 3. Gemini
    else if (provider === 'gemini') {
      const base64Data = image.split(',')[1];
      const mimeType = image.split(';')[0].split(':')[1] || 'image/jpeg';
      const url = `${baseUrl.replace(/\/$/, '')}/models/${model}:generateContent?key=${apiKey}`;

      const payload = {
        contents: [
          {
            parts: [
              {
                inlineData: {
                  mimeType,
                  data: base64Data
                }
              },
              {
                text: `${systemPrompt}\n\n请针对此图执行【${categoryName}】专业反推，并严格以标准 JSON 结构输出。${userNotes ? `用户补充: ${userNotes}` : ''}`
              }
            ]
          }
        ],
        generationConfig: {
          temperature,
          responseMimeType: "application/json"
        }
      };

      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errText = await response.text();
        throw new Error(`Gemini API 响应失败 (${response.status}): ${errText}`);
      }

      const data = await response.json();
      const content = data.candidates?.[0]?.content?.parts?.[0]?.text || '{}';
      parsedResult = extractJsonFromText(content);
    }

    if (!parsedResult) {
      throw new Error('未能从模型回复中提取到有效 JSON');
    }

    res.json({ status: 'success', result: parsedResult });

  } catch (error) {
    console.error('Reverse API Error:', error);
    res.status(500).json({ error: error.message || '反推处理异常' });
  }
});

function extractJsonFromText(text) {
  try {
    return JSON.parse(text);
  } catch (e) {
    // Try regex extraction of JSON block
    const match = text.match(/\{[\s\S]*\}/);
    if (match) {
      try {
        return JSON.parse(match[0]);
      } catch (innerErr) {
        console.error('Failed to parse matched JSON block', innerErr);
      }
    }
    throw new Error('返回内容非合法 JSON 格式: ' + text.slice(0, 150));
  }
}

// Serve Frontend in Production
const distPath = path.join(__dirname, 'dist');
if (fs.existsSync(distPath)) {
  app.use(express.static(distPath));
  app.get('*', (req, res) => {
    res.sendFile(path.join(distPath, 'index.html'));
  });
}

app.listen(PORT, () => {
  console.log(`\n======================================================`);
  console.log(`🚀 AI 图像反推与精准 Prompt 工作台 服务已启动!`);
  console.log(`📡 本地访问地址: http://localhost:${PORT}`);
  console.log(`🎯 涵盖 7 大专业反推体系 · 开箱即用`);
  console.log(`======================================================\n`);
});
