# ⚡ PromptHub (灵感词舱) - 专属 AI Prompt 视觉管理与引用系统

> 专为 **LTX 2.5**、**Minimax h3 (海螺)**、**可灵 Kling**、**Runway Gen-3**、**FLUX.1**、**Midjourney** 与 **大模型 (Claude / GPT-4o / DeepSeek)** 定制开发的高颜值、极简、开箱即用 Prompt 收藏与动态填槽管理平台。

---

## ✨ 核心特性

1. 🎬 **专为视频与视觉定制的多模态卡片**
   - **核心主力引擎预设**：重点支持 **LTX 2.5**（物理惯性与光影反射）、**Minimax h3**（海螺微表情与电影级叙事）、**可灵 Kling**、**Runway** 等。
   - 支持**多张参考图、首尾帧对比图**展示与悬浮高清预览。
   - 结构化突出画幅比（`9:16`、`16:9`）、时长参数、适配模型及负向约束词。

2. ⚡ **智能动态变量填槽 & 一键合成引用 (Dynamic Variable Interpolation)**
   - 在 Prompt 中任意使用 `{{变量名}}`（如 `{{航班号}}`、`{{出发地}}`、`{{镜头速度}}`）。
   - 点击卡片上的 **「填槽引用 ⚡」**，实时弹窗输入参数，右侧即时组装生成并一键复制到剪贴板。

3. 🔍 **多维分类、标签云与毫秒级搜索**
   - 分类体系：全部、AI 视频、AI 生图、大模型/文本、星标精选。
   - 标签云：按运镜方式（#一镜到底、#长镜头、#微距运镜）、画质光影多维筛选。
   - 毫秒级即时搜索：标题、镜头内容、负向词、标签全字段匹配。

4. 🌓 **现代化极简设计与全端适配**
   - 磨砂玻璃质感、暗黑 / 浅色模式自由切换。
   - 画廊大图卡片模式与紧凑列表模式一键切换。
   - 完全自适应手机端与平板，支持手机浏览器直接访问。

5. 💾 **数据完全私有化与一键备份**
   - 本地轻量化存储，图片自动保存在 `data/uploads/` 目录。
   - 支持一键导出 JSON 备份文件，支持增量合并或全量恢复。

---

## 🚀 极速上手使用

### 1. Windows 本地一键启动
- 双击运行根目录下的 `启动PromptHub.bat`，程序会自动启动服务并为您打开浏览器：`http://localhost:3000`。
- 若希望在后台静默运行（无控制台黑框），双击 `后台运行PromptHub(无黑框).vbs` 即可。

### 2. 开发模式运行 (Node.js)
```bash
cd prompthub
npm install
npm run dev
```

---

## 🌐 远程云服务器 / VPS 部署指南

### 方案 A：Docker Compose 一键部署（推荐）
在服务器上安装好 Docker 和 Docker Compose 后，只需执行：

```bash
# 1. 启动容器并在后台运行
docker compose up -d --build

# 2. 查看运行日志
docker compose logs -f
```
启动后即可通过 `http://你的服务器IP:3000` 远程访问。所有数据和上传的图片将持久化保存在当前目录下的 `./data` 文件夹中。

### 方案 B：PM2 / Node 生产部署
```bash
# 构建生产包
npm run build

# 使用 pm2 守护进程
npm install -g pm2
pm2 start server.js --name "prompthub"
```

### 方案 C：公网无端口域名访问（如配合 Nginx 反向代理或 Cloudflare Tunnel）
```nginx
server {
    listen 80;
    server_name prompt.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

---

## 💡 使用技巧示例

### 如何定义带变量的视频提示词？
在录入提示词时，将需要经常变化的部分使用双大括号包裹，例如：
```text
一条连续长镜头，不许切镜，写实摄影，竖屏 9:16。
从首帧开始：坐在飞机座位上向外看椭圆形舷窗...
准确落在尾帧：双手拿着登机牌，上面写着 FLIGHT {{flight_no}} | {{departure}} → {{destination}}...
```
录入后点击「自动识别并提取变量」，系统将自动解析出 `flight_no`、`departure`、`destination`。
下次使用时，只需点击卡片右下角的 **「填槽引用 ⚡」**，填入新的城市与航班，即可秒级复制出完整 Prompt！
