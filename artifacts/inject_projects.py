#!/usr/bin/env python3
"""注入30个实战成果项目到 Notebook"""
import json, re, sys

# 加载 notebook
with open('artifacts/30_days_python_by_cloudclaw.ipynb') as f:
    nb = json.load(f)

cells = nb['cells']

# 每个项目的代码，存在独立文件里避免转义问题
projects_code = json.load(open('artifacts/projects_code.json'))

insertions = []
for i, cell in enumerate(cells):
    if cell['cell_type'] != 'markdown':
        continue
    src = ''.join(cell['source']) if isinstance(cell['source'], list) else str(cell.get('source', ''))
    m = re.search(r'🏋️ Day (\d+)', src)
    if not m:
        continue
    day = int(m.group(1))
    code = projects_code.get(str(day), '')
    if not code:
        continue

    proj_title = f"Day {day} 实战项目"  # 会被具体的 title 覆盖
    md_cell = {
        "cell_type": "markdown",
        "metadata": {},
        "source": [f"---\n\n## 🚀 Day {day} 今日成果：{projects_code.get(f'{day}_title', '实战')}\n\n**学完今天的内容，你就能做这个 👇**\n\n{projects_code.get(f'{day}_desc', '')}"]
    }
    code_cell = {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [code]
    }
    insertions.append((i + 1, [md_cell, code_cell]))
    print(f"✅ Day {day}: {projects_code.get(f'{day}_title', '?')}")

insertions.sort(key=lambda x: -x[0])
for idx, new_cells in insertions:
    for j, c in enumerate(new_cells):
        cells.insert(idx + j, c)

print(f"\n📊 注入了 {len(insertions)} 个项目")
with open('artifacts/30_days_python_by_cloudclaw.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)
print("💾 已保存")
