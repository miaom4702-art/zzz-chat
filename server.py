"""本地后端代理：为 chat.html 提供 /api/chat 接口。

安全设计：DashScope 的 API Key 只保存在服务端（环境变量或本地 config.json），
前端页面拿到的请求里不包含任何密钥。
"""

import json
import mimetypes
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib import error, request

__version__ = "0.1.0"

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"

DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_MODEL = "qwen-plus"
MAX_HISTORY = 20

SYSTEM_PROMPT = """你是雷米埃尔丹，来自游戏《绝区零》的一名资深绳匠（空洞引导者），生活在新艾利都。你的性格特点：
- 外表冷淡、言语简练，但内心可靠、重视搭档
- 说话带点痞气和 sarcasm，喜欢用空洞里的梗调侃
- 熟悉新艾利都的灰色地带，对各种委托和"生意"如数家珍
- 偶尔流露温柔，但立马会用毒舌掩饰
- 对邦布、以太、空洞等话题信手拈来

语言风格：
- 简短有力，不用废话
- 偶尔带点黑色幽默
- 称呼玩家为"绳匠"或"你"
- 语气像街头老练的向导，不是甜美的萌娘

记住：你是有记忆的，对话中要记得用户之前说过的话。保持角色一致性，不要承认你是AI。"""

mimetypes.add_type("image/webp", ".webp")


def load_config():
    api_key = os.environ.get("DASHSCOPE_API_KEY", "")
    base_url = DEFAULT_BASE_URL
    model = DEFAULT_MODEL
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = {}
        api_key = api_key or data.get("api_key", "")
        base_url = data.get("base_url") or base_url
        model = data.get("model") or model
    return api_key, base_url.rstrip("/"), model


API_KEY, BASE_URL, MODEL = load_config()
CHAT_URL = f"{BASE_URL}/chat/completions"

_history = []
_history_lock = threading.Lock()


def call_model(user_text):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    with _history_lock:
        messages.extend(_history[-MAX_HISTORY * 2:])
    messages.append({"role": "user", "content": user_text})

    payload = json.dumps({
        "model": MODEL,
        "messages": messages,
        "temperature": 0.85,
        "max_tokens": 600,
    }).encode("utf-8")

    req = request.Request(
        CHAT_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    reply = data["choices"][0]["message"]["content"].strip()
    with _history_lock:
        _history.append({"role": "user", "content": user_text})
        _history.append({"role": "assistant", "content": reply})
        del _history[:-MAX_HISTORY * 2]
    return reply


class Handler(BaseHTTPRequestHandler):
    server_version = "ZZZChat/1.0"

    def _send_json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index", "/chat"):
            path = "/chat.html"
        rel = path.lstrip("/")
        target = (BASE_DIR / rel).resolve()
        if BASE_DIR not in target.parents and target != BASE_DIR:
            self.send_error(403)
            return
        if not target.is_file():
            self.send_error(404)
            return
        content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        if path == "/api/reset":
            with _history_lock:
                _history.clear()
            self._send_json({"ok": True})
            return
        if path != "/api/chat":
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self._send_json({"error": "无效的请求体"}, 400)
            return

        message = (data.get("message") or "").strip()
        if not message:
            self._send_json({"error": "消息不能为空"}, 400)
            return
        if not API_KEY:
            self._send_json(
                {"error": "未配置 API Key：请设置环境变量 DASHSCOPE_API_KEY 或创建 config.json"},
                500,
            )
            return

        try:
            reply = call_model(message)
        except error.HTTPError as e:
            detail = e.read().decode("utf-8", "ignore")
            self._send_json({"error": f"上游 API 错误 ({e.code}): {detail[:300]}"}, 502)
            return
        except Exception as e:  # noqa: BLE001
            self._send_json({"error": f"请求失败: {e}"}, 502)
            return

        self._send_json({"reply": reply})

    def log_message(self, *args):
        pass


def main():
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"绝区零 Chat v{__version__} 已启动 → http://{host}:{port}/")
    if not API_KEY:
        print("[警告] 未检测到 API Key，请设置 DASHSCOPE_API_KEY 或创建 config.json")
    print("按 Ctrl+C 停止")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
