# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 规范，版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [0.1.0] - 2026-10-06

首个公开版本，重点是修复前端泄露 API Key 的安全问题。

### 安全

- 移除 `chat.html` 中硬编码的 DashScope `API_KEY`、接口地址与系统提示词，前端不再暴露任何密钥。
- 新增本地后端代理 `server.py`：由服务端持有密钥并转发模型请求，密钥从环境变量 `DASHSCOPE_API_KEY` 或本地 `config.json` 读取；`config.json` / `.env` 已被 `.gitignore` 排除。

### 新增

- `server.py`：零第三方依赖（仅标准库），提供静态文件服务、`POST /api/chat`（对话）与 `POST /api/reset`（清空历史）。
- 服务端保存最近 20 轮对话历史，实现「有记忆」的对话。
- `config.example.json`：API Key 配置模板。
- `chat.html`：AI 角色「雷米埃尔丹」聊天界面（头像状态切换、推荐问题、错误提示）。
- `index.html`：绝区零素材随机展示页。
- `collage.py`：随机拼贴生成脚本。

[0.1.0]: https://github.com/miaom4702-art/zzz-chat/releases/tag/v0.1.0
