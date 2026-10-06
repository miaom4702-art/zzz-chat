import random
from pathlib import Path

folder = Path(__file__).parent
files = list(folder.glob("*.webp"))

if not files:
    print("没找到 webp 文件")
    exit()

picked = random.sample(files, min(len(files), 3))
print(f"随机选中 {len(picked)} 个素材:")
for f in picked:
    print(f"  {f.name}")

# 生成一个随机排序的 HTML 拼贴
html = """<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><title>随机拼贴</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#111;display:flex;min-height:100vh;align-items:center;justify-content:center;padding:40px}
.collage{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px;max-width:1000px;width:100%}
.collage img{width:100%;border-radius:12px;box-shadow:0 8px 40px rgba(0,0,0,0.6);transition:transform .3s}
.collage img:hover{transform:scale(1.03)}
</style></head>
<body>
<div class="collage">
"""
for f in picked:
    html += f'  <img src="{f.name}" alt="zzz">\n'
html += """</div>
</body>
</html>"""

out = folder / "random_collage.html"
out.write_text(html, encoding="utf-8")
print(f"\n已生成随机拼贴: {out}")
