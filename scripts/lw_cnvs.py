# -*- coding: utf-8 -*-
"""关键判定：汉化包在国际服留下英文的那些格子，国服（简体中文官方）到底有没有中文？

如果有 -> 汉化包作者只是没翻到位，我拿更新的国服数据能捞到更多。
如果没有 -> 这是死路，只能自己翻。
"""
import os, re, sys, json, msgpack
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lw_master import decrypt

ROOT = os.path.dirname(os.path.abspath(__file__))
NAMES = json.load(open(os.path.join(ROOT, 'lw_work', 'table_names.json'), encoding='utf-8'))
KANA = re.compile(r'[\u3040-\u309f\u30a0-\u30ff]')
HAN = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf]')
ASCII = re.compile(r'^[\x20-\x7e]*$')

CN_DIRS = ['lw_work/dump_cn', 'dev_cn/master', 'dev_cn/cncache', 'dev_cn/cache']


def load_patch(h):
    p = f'dl/ext/lwlocal/dec/{h}.msgpack'
    return msgpack.unpackb(open(p, 'rb').read(), raw=False, strict_map_key=False)


def load_cn(h):
    for d in CN_DIRS:
        for name in (h + '.msgpack', h):
            p = os.path.join(ROOT, d, name)
            if not os.path.isfile(p):
                continue
            raw = open(p, 'rb').read()
            if name.endswith('.msgpack'):
                try:
                    return msgpack.unpackb(raw, raw=False, strict_map_key=False), p
                except Exception:
                    continue
            try:
                return msgpack.unpackb(decrypt(raw), raw=False, strict_map_key=False), p
            except Exception:
                continue
    return None, None


for tname in ('Bullet', 'SkillEffect', 'Skill', 'Spellcard', 'Shot', 'Voice', 'Resist'):
    h = NAMES[tname]
    jp = msgpack.unpackb(open(f'dumped/{h}.msgpack', 'rb').read(), raw=False, strict_map_key=False)
    P = load_patch(h)
    C, path = load_cn(h)
    print(f'=== {tname}  CN 来源: {path} ===')
    if C is None:
        print('  找不到国服数据')
        continue
    n_jp = n_patch_en = n_cn_has_cn = n_cn_none = 0
    samp = []
    for rid in set(P) & set(jp):
        pr, jr = P[rid], jp[rid]
        cr = C.get(rid)
        if not isinstance(pr, list) or not isinstance(jr, list):
            continue
        for i in range(min(len(pr), len(jr))):
            pv, jv = pr[i], jr[i]
            if not isinstance(jv, str) or not KANA.search(jv):
                continue
            n_jp += 1
            if not (isinstance(pv, str) and pv.strip() and not KANA.search(pv) and not HAN.search(pv)):
                continue          # 汉化包这格有中文（已处理），跳过
            n_patch_en += 1
            if isinstance(cr, list) and i < len(cr) and isinstance(cr[i], str) and HAN.search(cr[i]) and not KANA.search(cr[i]):
                n_cn_has_cn += 1
                if len(samp) < 3:
                    samp.append((rid, i, jv, pv, cr[i]))
            else:
                n_cn_none += 1
    print(f'  日文格 {n_jp}  其中汉化包留英文 {n_patch_en}')
    print(f'    国服有中文: {n_cn_has_cn}   国服也没有: {n_cn_none}')
    for rid, i, jv, pv, cv in samp:
        print(f'    [{rid}.{i}] 日:{jv[:34]!r}')
        print(f'                包EN:{pv[:34]!r}  国服:{cv[:34]!r}')
