#!/usr/bin/env python3
"""东方归言录 日服汉化 · 反查工具（reverse lookup）

用途：把游戏里看到的一句日文/中文，反查到它到底存在哪张 master 表、哪条记录、哪个字段，
同时把国服（v6.6.0）同表同 id 同字段的中文一并列出来 —— 国服文本可以直接当译文用。

数据来源：
  dumped/<hash>.msgpack        日服 1.71.1 解出的 212 张表
  lw_work/dump_cn/<hash>.msgpack  国服 6.6.0 解出的 219 张表（同一 AES 密钥）
  lw_work/loc_ja.csv           APK 内 CommonStringMaster（UI 文本 1579 条，中文列空）

子命令：
  find <文本> [...]      反查文本（默认同时查日服与国服）
  show <表名> <id>       按字段对齐显示一条记录（日服 / 国服）
  missing [--table 名]   统计各表还有多少日文字段缺中文（= 待翻译量）
  stats                  总览
  names                  打印表名 -> hash 全表

常用参数：
  --side jp|cn|ui|all    只查某一侧（默认 all）
  --table 名/前缀        限定表（如 SkillEffect、Skill、Bullet）
  --exact                整字段完全相等（默认子串）
  --limit N              最多显示 N 条（默认 30）
  --width N              预览截断宽度（默认 100）

例：
  python lw_lookup.py find "結界異常"
  python lw_lookup.py find "毒霧" --table SkillEffect --limit 5
  python lw_lookup.py find "博麗霊夢-スペカA1" --exact
  python lw_lookup.py find "仇恨值" --side cn
  python lw_lookup.py show Spellcard 100111
"""
import os, sys, glob, json, hashlib, re, argparse, msgpack

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.abspath(__file__))
JP_DIR = os.path.join(ROOT, 'dumped')
CN_DIR = os.path.join(ROOT, 'lw_work', 'dump_cn')
CSV_PATH = os.path.join(ROOT, 'lw_work', 'loc_ja.csv')
NAMES_CACHE = os.path.join(ROOT, 'lw_work', 'table_names.json')

# 类名与文件名拼写不一致的几张表
ALIASES = {'DispatchDeperture': 'DispatchDeparture', 'UnitSFWLimitbreak': 'UnitSfwLimitbreak'}

KANA = re.compile(r'[\u3040-\u30ff]')
HAN = re.compile(r'[\u4e00-\u9fff\uf900-\ufaff]')
TAG = re.compile(r'<[^>]{1,40}>')


def snake(name: str) -> str:
    return re.sub(r'(?<=[a-z0-9])(?=[A-Z])', '_', name).lower()


def build_names():
    """表名 -> 文件名哈希：文件名 = md5(小写下划线表名 + "_master")"""
    tables = json.load(open(os.path.join(ROOT, 'lw_work', 'tables.json'), encoding='utf-8'))
    have = {os.path.basename(p)[:-8] for p in glob.glob(os.path.join(JP_DIR, '*.msgpack'))}
    have |= {os.path.basename(p)[:-8] for p in glob.glob(os.path.join(CN_DIR, '*.msgpack'))}
    names = {}
    for t in tables:
        for cand in {t, ALIASES.get(t, t)}:
            h = hashlib.md5((snake(cand) + '_master').encode()).hexdigest()
            if h in have:
                names[cand] = h
                break
    return names


def load_names():
    if os.path.exists(NAMES_CACHE):
        try:
            names = json.load(open(NAMES_CACHE, encoding='utf-8'))
            if names:
                return names
        except Exception:
            pass
    names = build_names()
    json.dump(names, open(NAMES_CACHE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return names


NAMES = load_names()
NAME_OF = {v: k for k, v in NAMES.items()}
NAME_OF.update({'9739982db50db5cd8d2df0718b89a3a0': '(未知名A)',
                '8190bcb609e71d802f162028b97312a3': '(未知名B)'})


def table_files(root):
    out = {}
    for p in glob.glob(os.path.join(root, '*.msgpack')):
        h = os.path.basename(p)[:-8]
        out[h] = p
    return out


JP_FILES = table_files(JP_DIR)
CN_FILES = table_files(CN_DIR)


def load_table(h, side='jp'):
    p = (JP_FILES if side == 'jp' else CN_FILES).get(h)
    if not p:
        return None
    try:
        return msgpack.unpackb(open(p, 'rb').read(), raw=False, strict_map_key=False)
    except Exception:
        return None


def is_text(x):
    return isinstance(x, str) and len(x) > 0 and (KANA.search(x) or HAN.search(x))


def short(s, width):
    s = s.replace('\n', '\\n')
    return s if len(s) <= width else s[:width] + '…'


def resolve_table(spec):
    """允许表名、前缀、hash 片段。返回 [(name, hash)]"""
    spec = spec.strip()
    hits = []
    low = spec.lower()
    for name, h in NAMES.items():
        if name.lower() == low or h == low:
            hits.append((name, h))
    if not hits:
        for name, h in NAMES.items():
            if name.lower().startswith(low) or h.startswith(low):
                hits.append((name, h))
    return hits


# ---------------------------------------------------------------- find
def cmd_find(args):
    q = args.query
    if not q:
        print('用法: find <文本>')
        return
    sides = {'all': ('jp', 'cn', 'ui'), 'jp': ('jp',), 'cn': ('cn',), 'ui': ('ui',)}[args.side]
    limit = args.limit
    shown = 0
    hit_tables = 0

    tables = sorted(NAMES.items(), key=lambda kv: kv[0])
    if args.table:
        want = {h for _, h in resolve_table(args.table)}
        if not want:
            print(f'找不到表: {args.table}')
            return
        tables = [(n, h) for n, h in tables if h in want]

    # ---- master 表（jp / cn）----
    for side in ('jp', 'cn'):
        if side not in sides:
            continue
        cache = {}
        for name, h in tables:
            p = (JP_FILES if side == 'jp' else CN_FILES).get(h)
            if not p:
                continue
            raw = open(p, 'rb').read()
            qb = q.encode('utf-8')
            if not args.exact:
                qb = qb.lower()
                raw = raw.lower()
            if qb not in raw:
                continue
            if h not in cache:
                cache[h] = load_table(h, side)
            obj = cache[h]
            if not isinstance(obj, dict):
                continue
            nhit = 0
            for k, v in obj.items():
                if not isinstance(v, list):
                    continue
                for i, x in enumerate(v):
                    if not isinstance(x, str) or not x:
                        continue
                    ok = (x == q) if args.exact else (q.lower() in x.lower())
                    if not ok:
                        continue
                    nhit += 1
                    hit_tables += 1
                    if shown < limit:
                        jp_obj = obj if side == 'jp' else load_table(h, 'jp')
                        cn_obj = obj if side == 'cn' else load_table(h, 'cn')
                        jx = jp_obj.get(k, []) if isinstance(jp_obj, dict) else []
                        cx = cn_obj.get(k, []) if isinstance(cn_obj, dict) else []
                        jt = jx[i] if isinstance(jx, list) and i < len(jx) else ''
                        ct = cx[i] if isinstance(cx, list) and i < len(cx) else None
                        tag = '' if side == 'jp' else ' [CN命中]'
                        print(f'\n■ {name}  id={k}  field={i}{tag}')
                        print(f'   日: {short(jt, args.width)}')
                        if ct is None:
                            print('   中: (国服无此条)')
                        elif ct == jt:
                            print('   中: (与日文相同)')
                        else:
                            print(f'   中: {short(ct, args.width)}')
                        shown += 1
                    elif nhit <= 3:
                        print(f'   … {name} id={k} field={i}（超出 --limit）')
            if nhit and shown >= limit:
                break

    # ---- UI 文本（APK CommonStringMaster CSV）----
    if 'ui' in sides and os.path.exists(CSV_PATH):
        import csv
        rows = list(csv.DictReader(open(CSV_PATH, encoding='utf-8-sig')))
        for r in rows:
            key, ja = r.get('text_key', ''), r.get('japanese_value', '') or ''
            if not ja:
                continue
            ok = (ja == q) if args.exact else (q.lower() in ja.lower() or q.lower() in key.lower())
            if not ok:
                continue
            hit_tables += 1
            if shown < limit:
                print(f'\n■ UI/CommonString  text_key={key}')
                print(f'   日: {short(ja, args.width)}')
                print(f'   中: (APK 表中文列为空)')
                shown += 1

    print(f'\n—— 共 {hit_tables} 处命中，显示 {shown} 条')


# ---------------------------------------------------------------- show
def cmd_show(args):
    spec = args.table or args.query
    hits = resolve_table(spec)
    if not hits:
        print(f'找不到表: {spec}')
        return
    name, h = hits[0]
    jp = load_table(h, 'jp')
    cn = load_table(h, 'cn')
    if jp is None:
        print('日服无此表')
        return
    key = args.id
    k = int(key) if str(key).lstrip('-').isdigit() else key
    if k not in jp:
        print(f'{name} 无 id={key}；现有 id 示例: {list(jp)[:8]}')
        return
    jv = jp[k]
    cv = cn.get(k) if isinstance(cn, dict) else None
    print(f'{name} ({h})  id={k}  字段数={len(jv)}')
    for i, x in enumerate(jv):
        c = cv[i] if isinstance(cv, list) and i < len(cv) else None
        if not isinstance(x, str) and c is None:
            continue
        if not is_text(x) and not (isinstance(c, str) and is_text(c)):
            continue
        print(f'  [{i:>2}] 日: {short(str(x), args.width)}')
        if isinstance(c, str) and c:
            print(f'       中: {short(c, args.width)}')


# ---------------------------------------------------------------- missing
def cmd_missing(args):
    tables = sorted(NAMES.items(), key=lambda kv: kv[0])
    if args.table:
        want = {h for _, h in resolve_table(args.table)}
        tables = [(n, h) for n, h in tables if h in want]
    rows = []
    for name, h in tables:
        jp = load_table(h, 'jp')
        if not isinstance(jp, dict):
            continue
        cn = load_table(h, 'cn') or {}
        total = done = chars = 0
        for k, v in jp.items():
            if not isinstance(v, list):
                continue
            cv = cn.get(k) if isinstance(cn, dict) else None
            for i, x in enumerate(v):
                if not isinstance(x, str) or not KANA.search(x):
                    continue  # 只统计含假名的真日文
                total += 1
                c = cv[i] if isinstance(cv, list) and i < len(cv) else None
                if isinstance(c, str) and c.strip() and c != x and HAN.search(c):
                    done += 1
                else:
                    chars += len(x)
        if total:
            rows.append((name, h, total, done, total - done, chars))
    rows.sort(key=lambda r: -r[5])
    tot = sum(r[2] for r in rows)
    don = sum(r[3] for r in rows)
    print(f'{"表":32}{"日文字段":>10}{"国服可得":>10}{"待翻译":>10}{"待译字数":>12}')
    for name, h, total, done, left, chars in rows:
        if left == 0:
            continue
        print(f'{name:32}{total:>10}{done:>10}{left:>10}{chars:>12}')
    print(f'\n合计: {tot} 个含假名日文字段，国服可直接复用 {don} 个（{don/tot*100:.1f}%），剩余 {tot-don} 个需翻译')


# ---------------------------------------------------------------- stats
def cmd_stats(args):
    print(f'表数: 日服 {len(JP_FILES)} / 国服 {len(CN_FILES)} / 命名 {len(NAMES)}')
    common = set(JP_FILES) & set(CN_FILES)
    print(f'两边同名表: {len(common)}')
    tot_chars = tot_fields = 0
    for h in JP_FILES:
        o = load_table(h, 'jp')
        if not isinstance(o, dict):
            continue
        for v in o.values():
            if not isinstance(v, list):
                continue
            for x in v:
                if is_text(x):
                    tot_fields += 1
                    tot_chars += len(x)
    print(f'日文/汉字文本字段: {tot_fields}，合计 {tot_chars} 字符（含重复）')


# ---------------------------------------------------------------- names
def cmd_names(args):
    for name, h in sorted(NAMES.items()):
        f = JP_FILES.get(h)
        print(f'{name:36}{h}')


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument('cmd', nargs='?')
    ap.add_argument('query', nargs='?')
    ap.add_argument('id', nargs='?')
    ap.add_argument('--table', '-t')
    ap.add_argument('--side', '-s', default='all', choices=['all', 'jp', 'cn', 'ui'])
    ap.add_argument('--limit', '-l', type=int, default=30)
    ap.add_argument('--width', '-w', type=int, default=100)
    ap.add_argument('--exact', '-e', action='store_true')
    a = ap.parse_args()
    if a.cmd == 'show' and a.query and not a.table:
        a.table = a.query
    if a.cmd == 'find':
        cmd_find(a)
    elif a.cmd == 'show':
        cmd_show(a)
    elif a.cmd == 'missing':
        cmd_missing(a)
    elif a.cmd == 'stats':
        cmd_stats(a)
    elif a.cmd == 'names':
        cmd_names(a)
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
