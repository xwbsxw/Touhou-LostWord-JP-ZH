# -*- coding: utf-8 -*-
"""把项目整理成可上传 GitHub 的目录结构。

目标目录: C:\\Users\\Administrator\\Desktop\\新建文件夹 (2)

包含：
  scripts/       全部 .py（扁平，因为脚本之间按模块名互相 import）
  data/          table_names.json / trans_all.json / choice_todo.json
  bundles/story/ 6 个已译好的剧情包（可直接推送，小体积）
  docs/          说明文档
排除：out/ ui_out/ ui_text_out/ font_out/ master_stage/（可再生产物，
      且字体含方正雅宋版权）
"""
import os, shutil, glob, json

ROOT = os.path.dirname(os.path.abspath(__file__))
DST = r'C:\Users\Administrator\Desktop\新建文件夹 (2)'

if os.path.isdir(DST):
    shutil.rmtree(DST)
os.makedirs(DST)

def mk(*parts):
    p = os.path.join(DST, *parts)
    os.makedirs(p, exist_ok=True)
    return p

sc = mk('scripts')
dt = mk('data')
bd = mk('bundles', 'story')
dc = mk('docs')

# ---- scripts ----
n_py = 0
for f in glob.glob(os.path.join(ROOT, 'lw_*.py')):
    shutil.copy2(f, os.path.join(sc, os.path.basename(f)))
    n_py += 1
# 其它辅助脚本
for f in glob.glob(os.path.join(ROOT, '*.py')):
    base = os.path.basename(f)
    if base.startswith('lw_'):
        continue
    if base in ('scan_fonts.py',):
        shutil.copy2(f, os.path.join(sc, base))
        n_py += 1

# ---- data ----
for name in ('table_names.json', 'trans_all.json'):
    src = os.path.join(ROOT, 'lw_work', name)
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(dt, name))
for name in ('choice_todo.json', 'choice_unique.json'):
    src = os.path.join(ROOT, 'lw_work', name)
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(dt, name))

# ---- bundles/story ----
n_bd = 0
src_dir = os.path.join(ROOT, 'lw_work', 'story_sc_out')
if os.path.isdir(src_dir):
    for f in os.listdir(src_dir):
        if f.endswith('__data'):
            shutil.copy2(os.path.join(src_dir, f), os.path.join(bd, f))
            n_bd += 1

print(f'scripts: {n_py} 个')
print(f'data: {len(os.listdir(dt))} 个')
print(f'bundles/story: {n_bd} 个')

total = 0
for root, dirs, files in os.walk(DST):
    for f in files:
        total += os.path.getsize(os.path.join(root, f))
print(f'总计 {total/1048576:.2f} MB -> {DST}')
