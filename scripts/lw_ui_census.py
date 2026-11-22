# -*- coding: utf-8 -*-
"""界面文字普查。

统计范围（全部日服缓存包）：
  1. LocalizeText.jpText    —— 日服真正显示的字段
  2. TextMeshProUGUI.m_text —— TMP 文本
  3. Sprite / Texture2D 名字 —— 判断哪些标签其实是图片

输出：
  lw_work/ui_census.json   逐包明细
  lw_work/ui_census.txt    可读报告
用法: python lw_ui_census.py <bundle_root>
"""
import os, sys, json, re, collections
import UnityPy

ROOT = os.path.dirname(os.path.abspath(__file__))
KANA = re.compile(r'[\u3040-\u30ff]')
HAN = re.compile(r'[\u4e00-\u9fff]')
ASCII = re.compile(r'^[\x00-\x7f]+$')


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'lw_work/jpuc3')
    keys = []
    for a in sorted(os.listdir(root)):
        pa = os.path.join(root, a)
        if not os.path.isdir(pa):
            continue
        for b in os.listdir(pa):
            f = os.path.join(pa, b, '__data')
            if os.path.exists(f):
                keys.append((a, b, f))
    print(f'待扫 {len(keys)} 包', flush=True)

    per_bundle = []
    tot_jp = tot_jp_kana = tot_jp_ok = 0
    tot_tmp = tot_tmp_kana = 0
    samples = []
    sprite_bundles = 0
    fonts_seen = collections.Counter()

    for i, (a, b, f) in enumerate(keys):
        if i % 300 == 0:
            print(f'  {i}/{len(keys)}  jpText待译 {tot_jp_kana}', flush=True)
        try:
            env = UnityPy.load(f)
        except Exception:
            continue

        jp_n = jp_kana = jp_ok = 0
        tmp_n = tmp_kana = 0
        has_sprite = False
        bundle_samples = []

        for o in env.objects:
            tn = o.type.name
            if tn in ('Sprite', 'Texture2D'):
                has_sprite = True
                continue
            if tn != 'MonoBehaviour':
                continue
            try:
                t = o.read_typetree()
            except Exception:
                continue
            if not isinstance(t, dict):
                continue
            jp = t.get('jpText')
            if isinstance(jp, str) and jp.strip():
                jp_n += 1
                if KANA.search(jp):
                    jp_kana += 1
                    if len(bundle_samples) < 3:
                        bundle_samples.append(jp[:70])
                else:
                    jp_ok += 1
            mt = t.get('m_text')
            if isinstance(mt, str) and mt.strip():
                tmp_n += 1
                if KANA.search(mt):
                    tmp_kana += 1

        if jp_n or tmp_n:
            per_bundle.append({
                'a': a, 'b': b, 'size': os.path.getsize(f),
                'jp_total': jp_n, 'jp_kana': jp_kana, 'jp_noKana': jp_ok,
                'tmp_total': tmp_n, 'tmp_kana': tmp_kana,
                'has_sprite': has_sprite,
                'samples': bundle_samples,
            })
            tot_jp += jp_n
            tot_jp_kana += jp_kana
            tot_jp_ok += jp_ok
            tot_tmp += tmp_n
            tot_tmp_kana += tmp_kana
            if has_sprite:
                sprite_bundles += 1

    per_bundle.sort(key=lambda x: -x['jp_kana'])
    json.dump(per_bundle, open(os.path.join(ROOT, 'lw_work/ui_census.json'), 'w',
                               encoding='utf-8'), ensure_ascii=False, indent=1)

    lines = []
    lines.append(f'扫描包数 {len(keys)}')
    lines.append(f'含文本组件的包 {len(per_bundle)}')
    lines.append('')
    lines.append(f'LocalizeText.jpText 总数 {tot_jp}')
    lines.append(f'  其中含假名（待译） {tot_jp_kana}')
    lines.append(f'  已无假名（可能已译/纯符号） {tot_jp_ok}')
    lines.append(f'TMP m_text 总数 {tot_tmp}，含假名 {tot_tmp_kana}')
    lines.append(f'带 Sprite/Texture 的包 {sprite_bundles}（这些包里的标签可能是图片）')
    lines.append('')
    lines.append('=== jpText 待译最多的包 ===')
    for r in per_bundle[:25]:
        lines.append(f"  {r['a'][:10]}/{r['b'][:8]}  jpText {r['jp_total']:>4} "
                     f"待译 {r['jp_kana']:>4}  tmp待译 {r['tmp_kana']:>3} "
                     f"sprite={r['has_sprite']}  {r['size']} B")
        for s in r['samples']:
            lines.append(f'        {s}')
    txt = '\n'.join(lines)
    open(os.path.join(ROOT, 'lw_work/ui_census.txt'), 'w', encoding='utf-8').write(txt)
    print('\n' + txt)


if __name__ == '__main__':
    main()
