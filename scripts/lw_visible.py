#!/usr/bin/env python3
"""可见性过滤 v2：用「国服自己翻不翻这一格」当判据。

v1 只用「字段白名单 + 正则黑名单」，结果把 Bullet[1] / SkillEffect[1] 里
连官方简体客户端都留着日文的内部标识算成了「玩家可见待译」，例如：
    博麗霊夢-スペカA1 / 博麗霊夢-ラスワ1 / 博麗霊夢-スキルA1
    八意永琳 - ラスワ / ウォーク＆トロット / 春っぽい何か
这些改了也没人看到（国服玩家看到的也是日文）。

v2 增加两道数据判据（拿国服 dump 做 oracle）：
  · 国服同格也是日文（== 原文）      -> 内部标识
  · 国服同格只差标点（・ / · / 〜）  -> 内部标识
只有「国服表里没有这一行」（新内容）或「国服这格是中文但漏网」才算真正待译。

输出：
  lw_work/work_visible.json    {表: {字段: [[待译串, 次数], ...]}}  仅「真正待译」
  lw_work/visible_report.json  统计 + 分桶 + 每表每字段的待译量
"""
import os, json, re, msgpack, collections

ROOT = os.path.dirname(os.path.abspath(__file__))
NAMES = json.load(open(os.path.join(ROOT, 'lw_work', 'table_names.json'), encoding='utf-8'))
TRANS = json.load(open(os.path.join(ROOT, 'lw_work', 'trans_all.json'), encoding='utf-8'))
CN_DIR = os.path.join(ROOT, 'lw_work', 'dump_cn')

KANA = re.compile(r'[\u3040-\u30ff]')
HAN = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf]')

# 会上屏的字段（表名 -> 字段集合；None 表示全字段）
VISIBLE_FIELDS = {
    'Ability': {1, 2, 3, 9, 10, 15, 16, 18, 19},
    'AbilitySeal': None, 'AbilitySealEffect': {1, 2},
    'Achievement': None, 'Bgm': {2}, 'Bullet': {1, 2}, 'BulletExtraEffect': {1, 2},
    'Characteristic': {1, 2, 9, 10, 17, 18, 25, 26},
    'CommonString': {1}, 'Costume': {4, 5}, 'Enemy': {3}, 'Episode': None,
    'Event': None, 'Item': {1, 2}, 'Mission': {2}, 'Picture': {1, 2, 3, 4, 5, 7, 8},
    'Shot': {1, 2, 3}, 'Skill': {1, 2}, 'SkillEffect': {1, 2},
    'Spellcard': {1, 2, 3}, 'UnitSpeech': {3, 4}, 'Voice': {3}, 'VoiceSet': {3},
    'SpecialRulesEffect': {1, 2}, 'Resist': {1, 2}, 'ValuePackShop': None,
    'ArenaEnemy': {3}, 'Npc': None,
}

# 内部调试串特征
INTERNAL_PATTERNS = [
    re.compile(r'^\d{3,}'),                      # 4051/...
    re.compile(r'^\d+\s*[_/]'),                   # 19002_...
    re.compile(r'ユニットID[:：]'),
    re.compile(r'^スキル\d'),
    re.compile(r'スキル\d+[-‐]\d+'),
    re.compile(r'_スキル\d'),
    re.compile(r'^精霊_'),
    re.compile(r'キャンプスタッフ'),
    re.compile(r'ゲージ\d'),
    re.compile(r'^\d+~\d+層'),
    re.compile(r'^\[?[A-Za-z]{1,4}\]?\s*\d{3,}'),
    re.compile(r'^\d{1,4}$'),
    re.compile(r'^[A-Za-z0-9_./:%+\- ]+$'),      # 纯 ASCII
    # v2 新增：角色-招式槽位 这类纯内部命名
    re.compile(r'[-‐ー]\s*(スペカ|スキル|ラスワ|ショット)[A-Za-z]?\d*$'),
    re.compile(r'^(スペルカード|ラストワード)'),
]

# 标点归一化：只差这些标点的两串视为同一串
PUNCT = str.maketrans({
    '·': '・', '･': '・', '•': '・', '‧': '・', '∙': '・',
    '〜': '～', '~': '～', '－': '-', 'ー': '-', '−': '-', '‐': '-',
    '：': ':', '　': ' ', '，': ',', '．': '.', '！': '!', '？': '?',
})


def norm(s):
    return re.sub(r'\s+', '', s.translate(PUNCT)).strip()


def is_internal(s):
    for p in INTERNAL_PATTERNS:
        if p.search(s):
            return True
    return False


def visible_field(tbl, idx):
    v = VISIBLE_FIELDS.get(tbl, None)
    if v is None:
        return True
    return idx in v


def main():
    st = collections.Counter()
    work = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    per_field = collections.Counter()
    samples = collections.defaultdict(list)

    for tbl, h in sorted(NAMES.items()):
        p = os.path.join(ROOT, 'dumped', h + '.msgpack')
        if not os.path.exists(p):
            continue
        J = msgpack.unpackb(open(p, 'rb').read(), raw=False, strict_map_key=False)
        if not isinstance(J, dict):
            continue
        cp = os.path.join(CN_DIR, h + '.msgpack')
        C = msgpack.unpackb(open(cp, 'rb').read(), raw=False, strict_map_key=False) \
            if os.path.exists(cp) else {}
        done = TRANS.get(tbl, {})
        for k, jv in J.items():
            if not isinstance(jv, list):
                continue
            df = done.get(str(k), {})
            for i, x in enumerate(jv):
                if not isinstance(x, str) or not KANA.search(x) or str(i) in df:
                    continue
                st['remaining'] += 1
                if not visible_field(tbl, i):
                    st['field_hidden'] += 1
                    continue
                if is_internal(x):
                    st['internal'] += 1
                    continue
                cr = C.get(k)
                cv = cr[i] if isinstance(cr, list) and i < len(cr) else None
                if not isinstance(cv, str) or not cv.strip():
                    bucket = 'new_row'          # 国服没这行 = 新内容
                elif HAN.search(cv) and not KANA.search(cv):
                    bucket = 'cn_missed'        # 国服有中文却漏网（应极少）
                elif norm(cv) == norm(x):
                    bucket = 'cn_same'          # 国服也不翻
                elif cv.strip() == x.strip():
                    bucket = 'cn_same'
                else:
                    bucket = 'cn_other'         # 国服有差异但非中文
                if bucket in ('cn_same',):
                    st['internal'] += 1
                    st['internal_by_cn'] += 1
                    continue
                if bucket == 'cn_other':
                    st['cn_other'] += 1
                    if len(samples['cn_other']) < 40:
                        samples['cn_other'].append((tbl, i, x, cv))
                    continue
                st[bucket] += 1
                st['visible'] += 1
                per_field[f'{tbl}[{i}]'] += 1
                work[tbl][i][x] += 1

    out = {}
    for tbl, fields in work.items():
        out[tbl] = {}
        for i, c in fields.items():
            out[tbl][str(i)] = [[s, n] for s, n in c.most_common()]
    json.dump(out, open(os.path.join(ROOT, 'lw_work', 'work_visible.json'), 'w', encoding='utf-8'),
              ensure_ascii=False)

    rep = dict(st)
    rep['per_field'] = dict(per_field.most_common(40))
    rep['cn_other_samples'] = [[t, i, x, str(c)] for t, i, x, c in samples['cn_other']]
    json.dump(rep, open(os.path.join(ROOT, 'lw_work', 'visible_report.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)

    print(f'剩余含假名字段 {st["remaining"]}')
    print(f'  字段不可见（表格隐藏列）   {st["field_hidden"]}')
    print(f'  内部标识（正则黑名单）     {st["internal"] - st["internal_by_cn"]}')
    print(f'  内部标识（国服也不翻）     {st["internal_by_cn"]}')
    print(f'  国服有差异但非中文(待查)   {st["cn_other"]}')
    print(f'  ── 真正待译                {st["visible"]}')
    print(f'       其中 国服没这行(新内容) {st["new_row"]}')
    print(f'       其中 国服有中文漏网     {st["cn_missed"]}')
    print('\n真正待译 top（表[字段]）:')
    for k, n in per_field.most_common(16):
        print(f'  {k:24s}{n:>7}')


if __name__ == '__main__':
    main()
