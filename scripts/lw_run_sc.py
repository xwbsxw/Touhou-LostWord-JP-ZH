# -*- coding: utf-8 -*-
"""按顺序重跑翻译管线，输出简体译文到 trans_all.json。

    python lw_run_sc.py            # 全流程
各步骤失败不中断，最后汇总。
"""
import os, subprocess, sys, time, json

ROOT = os.path.dirname(os.path.abspath(__file__))
STEPS = [
    ('tm',        'lw_tm.py'),
    ('autocn',    'lw_autocn.py'),
    ('cnpatch',   'lw_cnpatch.py'),
    ('names',     'lw_names.py'),
    ('namesub',   'lw_namesub.py'),
    ('rules',     'lw_rules.py'),
    ('merge',     'lw_merge.py'),
]

env = dict(os.environ)
env['LW_MODE'] = 'sc'
env['PYTHONIOENCODING'] = 'utf-8'

print(f'LW_MODE={env["LW_MODE"]}\n')
for name, script in STEPS:
    if not os.path.exists(os.path.join(ROOT, script)):
        print(f'[{name}] 跳过：{script} 不存在')
        continue
    t0 = time.time()
    print(f'=== [{name}] {script} ===', flush=True)
    r = subprocess.run([sys.executable, script], cwd=ROOT, env=env,
                       capture_output=True, encoding='utf-8', errors='replace')
    dt = time.time() - t0
    tail = [l for l in (r.stdout or '').strip().splitlines() if l.strip()]
    for l in tail[-6:]:
        print('   ', l)
    if r.returncode != 0:
        print(f'    !! 退出码 {r.returncode}')
        err = (r.stderr or '').strip().splitlines()
        for l in err[-8:]:
            print('    ERR', l)
    print(f'    用时 {dt:.1f}s\n', flush=True)

p = os.path.join(ROOT, 'lw_work', 'trans_all.json')
if os.path.exists(p):
    d = json.load(open(p, encoding='utf-8'))
    n_tbl = len(d)
    n_row = sum(len(v) for v in d.values())
    n_f = sum(len(f) for v in d.values() for f in v.values())
    print(f'最终 trans_all.json: {n_tbl} 张表 / {n_row} 条 / {n_f} 字段 '
          f'({os.path.getsize(p)/1048576:.1f} MB)')
