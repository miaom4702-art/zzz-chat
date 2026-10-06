# 绝区零 AI 角色对话（雷米埃尔丹）

一个《绝区零》风格的 AI 角色对话网页。前端提供聊天界面，后端（`server.py`）代理调用阿里云 DashScope 的大模型接口。同时附带绝区零素材的随机展示页与拼贴生成脚本。

> 本项目的重点是**安全改造**：最初的版本把 DashScope API Key 硬编码在 `chat.html` 里，任何访问网页的人都能从源码中拿到密钥。现在改为「浏览器 → 本地后端 → DashScope」，API Key 只保存在服务端，前端不再暴露任何密钥。

## 1. 项目解决什么问题

- **做一个有「角色感」的对话网页**：以《绝区零》角色「雷米埃尔丹」为人格，接入大模型进行自由对话，而不是固定台词。
- **解决前端泄露 API Key 的安全问题**：密钥从前端移到后端代理，浏览器拿到的请求中不含任何密钥。
- **顺手提供素材展示**：一个绝区零素材的随机展示页，以及一个本地随机拼贴生成脚本。

## 2. 主要功能

- **AI 角色对话（`chat.html`）**
  - 人格化系统提示词（雷米埃尔丹：冷淡、简练、带痞气，称呼玩家为「绳匠」），提示词与密钥都放在后端。
  - 头像会随状态切换：待机（`待机.webp` / `待机2.webp`）、思考中（`思考中.webp`）、生成中（`生成答案.webp`）、沾沾自喜（`沾沾自喜.webp`）。
  - 推荐问题快捷按钮、回车发送、输入中动画、错误提示。
  - 前端只请求本地 `/api/chat`，不带任何密钥。
- **后端代理（`server.py`）**
  - **零第三方依赖**，仅使用 Python 标准库。
  - 同时充当静态文件服务器（可直接访问 `chat.html`、`index.html` 及图片素材）。
  - `POST /api/chat`：接收 `{"message": "..."}`，转发到 DashScope 的 OpenAI 兼容接口，返回 `{"reply": "..."}`。
  - `POST /api/reset`：清空服务端保存的对话历史。
  - API Key 从环境变量 `DASHSCOPE_API_KEY` 或本地 `config.json` 读取，后者已被 `.gitignore` 排除。
  - 服务端保存最近 20 轮对话历史，实现「有记忆」的对话。
- **素材展示页（`index.html`）**
  - 网格随机打乱展示 `.webp` 素材，点击可全屏查看，按 `R` 重新打乱，鼠标跟随光晕效果。
- **拼贴生成（`collage.py`）**
  - 从目录随机抽取 3 个 `.webp` 素材，生成 `random_collage.html`。

## 3. 安装方法

环境要求：**Python 3.8+**，无需安装任何第三方依赖。

1. 克隆仓库：

   ```bash
   git clone https://github.com/miaom4702-art/zzz-chat.git
   cd zzz-chat
   ```

2. 配置 API Key（二选一）：

   - 方式一：设置环境变量

     ```powershell
     $env:DASHSCOPE_API_KEY = "你的 DashScope API Key"
     ```

   - 方式二：复制 `config.example.json` 为 `config.json`，填入你的 Key：

     ```json
     {
         "api_key": "你的 DashScope API Key",
         "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
         "model": "qwen-plus"
     }
     ```

   > `config.json` 已在 `.gitignore` 中，**不要提交到仓库**。

## 4. 使用方法

### 启动服务

```bash
python server.py
```

启动后访问 **http://127.0.0.1:8000/** 即可聊天。可用环境变量调整监听地址与端口：

```powershell
$env:PORT = "8080"; python server.py
```

### 聊天

- 在输入框输入内容并回车（或点击推荐问题）发送，回复由后端调用大模型生成。
- 服务端会记住最近的对话内容；需要重置时调用 `POST /api/reset`。

### 素材展示页

访问 http://127.0.0.1:8000/index.html （页面引用的 `.webp` 素材需位于项目根目录）。

### 随机拼贴

```bash
python collage.py
```

运行后会在当前目录生成 `random_collage.html`。

## 5. 输入输出示例

### 示例一：网页聊天

输入（在页面输入框）：

```
你是谁
```

输出（页面显示，由模型生成，实际内容每次可能不同）：

```
雷米埃尔丹。新艾利都资深绳匠，带人下空洞的老手了。
找我接委托，还是单纯想唠两句？
```

### 示例二：调用后端接口

请求：

```bash
curl -X POST http://127.0.0.1:8000/api/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"message\":\"新艾利都最近怎样\"}"
```

响应：

```json
{"reply": "新艾利都还能怎样，天天有人在空洞边上讨生活。你要是想听点新鲜的，得先请我喝一杯。"}
```

### 示例三：未配置 Key 或出错

请求 `/api/chat` 但未配置密钥时：

```json
{"error": "未配置 API Key：请设置环境变量 DASHSCOPE_API_KEY 或创建 config.json"}
```

### 示例四：重置对话

```bash
curl -X POST http://127.0.0.1:8000/api/reset
```

响应：

```json
{"ok": true}
```

## 目录结构

```
绝区零/
├─ server.py              # 本地后端：静态服务 + /api/chat 代理（密钥在此读取）
├─ chat.html              # AI 角色聊天界面（不含密钥）
├─ index.html             # 素材随机展示页
├─ collage.py             # 随机拼贴生成脚本
├─ random_collage.html    # collage.py 生成的示例
├─ config.example.json    # 配置模板（复制为 config.json 使用）
├─ .gitignore             # 排除 config.json 等敏感文件
├─ bg.jpg                 # 聊天页背景
└─ *.webp                 # 角色立绘与素材
```

## 安全说明

- API Key 只通过环境变量或本地 `config.json` 提供给 `server.py`，前端 HTML 中不再包含任何密钥。
- 若此前的版本已把 Key 提交或公开过，请务必到 DashScope 控制台**禁用并更换**该 Key。
- 本项目为单用户本地设计：对话历史在服务端全局共享，不建议直接暴露到公网供多人使用；如需公网部署，请自行增加鉴权。

## 版权说明

- 本项目的**代码**（Python/HTML/CSS/JavaScript）以 [MIT License](LICENSE) 开源。
- `bg.jpg`、`*.webp` 等**游戏素材版权归米哈游 /《绝区零》所有**，不在 MIT 许可范围内，仅供个人学习交流使用。

## License

[MIT](LICENSE)
