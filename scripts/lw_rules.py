#!/usr/bin/env python3
"""规则翻译：处理模板化最强、出现次数最多的几类句子（国服没翻到的新内容）。

只做“高置信度”改写：命中规则才写，不命中就不动，避免产出生硬文本。
输出 lw_work/trans_rules.json（优先级最高，覆盖前面几层）。
"""
import os, sys, json, re, msgpack

ROOT = os.path.dirname(os.path.abspath(__file__))
NAMES = json.load(open(os.path.join(ROOT, 'lw_work', 'table_names.json'), encoding='utf-8'))
# 整串精确词表（国服对照挖出来的名字/短语，只做完全相等匹配，避免误替换）
NAME_EXACT = {}
_np = os.path.join(ROOT, 'lw_work', 'names_exact.json')
if os.path.exists(_np):
    NAME_EXACT = json.load(open(_np, encoding='utf-8'))
OUT = os.path.join(ROOT, 'lw_work', 'trans_rules.json')

# ---------------------------------------------------------------- 词表
TERM = {
    'CRI攻撃': '會心攻擊', 'CRI防御': '會心防禦', 'CRI命中': '會心命中', 'CRI回避': '會心迴避',
    '陽攻': '陽攻', '陰攻': '陰攻', '陽防': '陽防', '陰防': '陰防',
    '速力': '速度', '回避': '迴避', '命中': '命中', '霊力': '靈力', '体力': '體力',
    '結界': '結界', '注目': '仇恨值', '与ダメージ': '受到的傷害', '受けるダメージ': '受到的傷害',
    'ダメージ': '傷害', 'バリア': '護盾', 'グレイズ': '擦彈', 'ブースト': '靈力強化',
    'スペルカード': '符卡', 'ラストワード': '終符', 'スキル': '技能', 'ショット': '射擊',
    '燃焼': '燃燒', '焼却': '燒卻', '帯電': '帶電', '暗闇': '黑暗', '凍結': '凍結',
    '毒霧': '毒霧', '基礎値': '基礎值', 'CRI率': '會心機率', 'HIT率': '命中率',
    '拡散': '擴散', '交代': '替換', '封印': '封印', '集中': '集中',
    '光弾': '光彈', 'エネルギー弾': '能量彈', 'レーザー弾': '雷射彈', '通常弾': '通常彈',
    '御札弾': '御札彈', '斬撃弾': '斬擊彈', '尖弾': '尖彈', '流体弾': '流體彈',
    '質量弾': '質量彈', '特攻': '特攻', '妖精': '妖精', '妖怪': '妖怪', '過毒': '過毒',
    'ファスト': '先制', 'バリア': '護盾', 'グレイズ': '擦彈', 'ブースト': '靈力強化',
    'スタン': '暈眩', 'ディレイ': '延遲', '貫通': '貫通', '焼却': '燒卻', '斬裂': '斬裂',
    '属性': '屬性', 'ターン': '回合',
    '剣士': '劍士', '神格': '神格', 'スタン': '暈眩',
    '通常弾': '通常彈', '肉弾': '肉彈', '質量弾': '質量彈',
}
UP = {'アップ': '上升', '上昇': '上升', 'ダウン': '下降', '低下': '下降',
      '増加': '增加', '回復': '回復'}
ATTR = {'無': '無', '火': '火', '水': '水', '木': '木', '金': '金', '土': '土', '日': '日',
        '月': '月', '星': '星', '陽': '陽', '陰': '陰', '幻': '幻'}

EXACT = {
    '仮テキスト': '臨時文本',
    '基本マガジン': '基本彈匣',
    'おすすめ': '推薦',
    '汎用': '通用',
    '妖精': '妖精',
    '虚空': '虛空',
    '辰星': '辰星',
    '太白': '太白',
    '月属性': '月屬性',
    '生魂解放': '生魂解放',
    '衣装解放': '服裝解放',
    '育成パック': '培育禮包',
    '育成素材が入ったお得なパック': '內含培育素材的超值禮包',
    '巫形代パック': '巫形代禮包',
    '巫形代が入ったお得なセット': '內含巫形代的超值套組',
    '天形代が入ったお得なセット': '內含天形代的超值套組',
    '華片と巻物が入ったお得なパック': '內含華片與卷軸的超值禮包',
    '效果、性能無し、マガジン1～5は無属性': '無效果、無性能，彈匣1～5為無屬性',
    '幻想おとぎ草子開催期間中にログインをしよう': '在幻想童話故事舉辦期間登入遊戲吧',
    'イベント期間中にログインしよう': '在活動期間登入遊戲吧',
    'デイリー探索を1回クリア': '通關1次每日探索',
    'デイリー探索を1回クリアしよう': '通關1次每日探索吧',
    'デイリー探索を1日1回クリア': '每天通關1次每日探索',
    '少女祈祷中': '少女祈禱中',
    # ---- UI 标签（这些在国服里往往与日文相同，所以之前被跳过）----
    '名簿': '名冊', '図録': '圖錄', '図鑑': '圖鑑', '物語': '故事', 'おとぎ文庫': '童話文庫',
    'フレンド': '好友', '素材': '素材', '伝書': '傳書', '告知': '公告', 'メニュー': '選單',
    'ショップ': '商店', '仲間': '同伴', '絵札': '繪札', '施設': '設施', '課題': '任務',
    'おいのり': '祈願', '交換所': '交換所', 'アイテム蒐集': '道具收集', '特設': '特設',
    '探索': '探索', 'にこり宛配便': '似鳥配送', '衣装表示': '服裝顯示', '解放数': '解放數',
    '衣装': '服裝', 'ボイス': '語音', 'セリフ鑑賞': '台詞鑑賞', '変更': '變更', '再生': '播放',
    '強化': '強化', '編成': '編成', 'ホーム': '主頁', 'ストーリー': '故事', 'バトル': '戰鬥',
    'ミッション': '任務', 'ガチャ': '祈願', 'プレゼント': '禮物', 'ログインボーナス': '登入獎勵',
    'ショップポイント': '商店點數', '所持': '持有', '詳細': '詳細', '閉じる': '關閉',
    '戻る': '返回', '決定': '確定', 'キャンセル': '取消', '一覧': '一覽', '更新': '更新',
    '解説': '解說', 'イラスト': '插畫', 'とじる': '關閉', '開放': '開放',
    'メイン': '主線', 'デイリー': '每日', '初心者': '新手', 'イベント': '活動',
    'おつかい': '跑腿', '毎日課題': '每日任務', '本日の課題': '今日任務',
    '今週の課題': '本週任務', '今期の課題': '本期任務', '取材レベル': '採集等級',
    'ポイント': '點數', 'レベル購入': '等級購買', 'チャレンジ': '挑戰',
    '一括受取': '全部領取', '課題': '任務', '挑戦': '挑戰',
}
for i in range(1, 8):
    EXACT[f'追加マガジン{i}'] = f'追加彈匣{i}'
for a in ('A', 'B'):
    for i in range(0, 4):
        EXACT[f'ショット{a}_{i}'] = f'射擊{a}_{i}'
        EXACT[f'ショット{a}'] = f'射擊{a}' if i == 0 else EXACT.get(f'ショット{a}', f'射擊{a}')
    EXACT[f'スペカ{a}'] = f'符卡{a}'
    EXACT[f'【ショット{a}】'] = f'【射擊{a}】'
    EXACT[f'【スペカ{a}】'] = f'【符卡{a}】'
EXACT['【ラスワ】'] = '【終符】'
EXACT['ラスワ'] = '終符'
EXACT['スペカA'] = '符卡A'
EXACT['スペカB'] = '符卡B'

# ---------------------------------------------------------------- 规则
C = r'<color=(#[0-9A-Fa-f]{6})>'
TARGET = {'自身': '自身', '味方全体': '己方全體', '味方単体': '己方單體',
          '相手全体': '敵方全體', '相手単体': '敵方單體', '対象': '目標'}

# 自身の<color>X</color>を7段階<color>アップ</color> (2T)
RE_STAT = re.compile(
    r'^(自身|味方全体|味方単体|相手全体|相手単体|対象)の' + C + r'([^<]{1,12})</color>を(\d+)段階' +
    C + r'(アップ|上昇|ダウン|低下)</color> ?\((\d+)T\)$')
# 相手全体に結界異常「<color>毒霧</color>」を3枚<color>付与</color> (3T)
RE_BARRIER = re.compile(
    r'^(自身|味方全体|相手全体|相手単体|対象)に結界異常「' + C + r'([^<]{1,12})</color>」を(\d+)枚' +
    C + r'付与</color> ?\((\d+)T\)$')
# 带 {0}/{1}/{2} 的付与：相手全体に結界異常「X」を{0}枚付与 (3T) [発生率{1}%で追加効果+{2}]
RE_BARRIER_PH = re.compile(
    r'^(自身|味方全体|相手全体|相手単体|対象)に結界異常「' + C + r'([^<]{1,12})</color>」を'
    r'\{0\}枚' + C + r'付与</color> ?\((\d+)T\)( ?\[発生率\{1\}%で追加効果\+\{2\}\])?$')
# 味方全体の<color>体力</color>を10%<color>回復</color>
RE_STAT_PCT = re.compile(
    r'^(自身|味方全体|味方単体|相手全体|相手単体|対象)の' + C + r'([^<]{1,12})</color>を'
    r'(\d+)%' + C + r'(回復|上昇|アップ|ダウン|低下)</color>$')
RE_WIN = re.compile(r'^戦闘で(\d+)日(\d+)回勝利しよう$')
RE_EVENT_WIN = re.compile(r'^イベント探索の戦闘で(\d+)回勝利しよう$')
RE_GACHA = re.compile(r'^おいのりを(\d+)回しよう$')
RE_LOGIN = re.compile(r'^(イベント|幻想おとぎ草子).*登録?してい?しよう$')

# ---- 带 {0}/{1}/{2} 占位符的技能说明 ----
PH_STAT = re.compile(
    r'^(自身|味方全体|味方単体|相手全体|相手単体|対象)の(<color=#[0-9A-Fa-f]{6}>)([^<]{1,12})</color>を'
    r'\{0\}(段階)?(<color=#[0-9A-Fa-f]{6}>)(アップ|上昇|ダウン|低下|増加|回復)</color>'
    r'( \(\d+T\))?( ?\[発生率\{1\}%で追加効果\+\{2\}\])?$')
PH_BARRIER_N = re.compile(
    r'^(自身|味方全体|相手全体|相手単体)の(<color=#[0-9A-Fa-f]{6}>)(結界|霊力|体力)</color>を'
    r'(\d+)枚?(<color=#[0-9A-Fa-f]{6}>)(増加|上昇|回復)</color>$')


def tr_placeholder(s):
    m = PH_STAT.match(s)
    if m:
        who, c1, stat, stage, c2, verb, tail_t, tail_r = m.groups()
        term = TERM.get(stat, stat)
        v = UP.get(verb, verb)
        unit = '等級' if stage else ('' if stat in ('霊力', '結界', '与ダメージ', '受けるダメージ') else '')
        out = f'{TARGET[who]}{c1}{term}</color>{c2}{v}</color>{{0}}{unit}'
        if tail_t:
            n = re.sub(r'\D', '', tail_t)
            out += f' ({n}回合)'
        if tail_r:
            out += ' [發生率{1}%追加效果+{2}]'
        return out
    m = PH_BARRIER_N.match(s)
    if m:
        who, c1, stat, n, c2, verb = m.groups()
        unit = '張' if stat == '結界' else ''
        return f'{TARGET[who]}{c1}{TERM.get(stat, stat)}</color>{c2}{UP.get(verb, verb)}</color>{n}{unit}'
    return None

# ---- 弹幕/射击 的短标签 ----
DAN = {'通常弾': '通常彈', 'エネルギー弾': '能量彈', 'レーザー弾': '雷射彈', '光弾': '光彈',
       '御札弾': '御札彈', '斬撃弾': '斬擊彈', '硬質弾': '硬質彈', '貫通弾': '貫通彈',
       '爆発弾': '爆炸彈', '反射弾': '反射彈', '流体弾': '流體彈', '尖弾': '尖彈',
       '質量弾': '質量彈', '硬質': '硬質', '斬裂': '斬裂', '氷解': '冰解', '焼却': '燒卻',
       '吸収': '吸收', '過毒': '過毒', '必中': '必中', 'CRI': '會心', 'バレット': '彈幕',
       '精密': '精密', '閃光': '閃光', '氷解': '冰解'}
RE_BARET_ADD = re.compile(r'^基本バレットに(.+)$')
KI = {'陽気': '陽氣', '陰気': '陰氣'}
RE_ATTR_ONLY = re.compile(r'^(.{1,2})属性$')
RE_KIHON = re.compile(r'^基本に(.+)$')
RE_ALLBARET = re.compile(r'^全バレット(.+)参照$')
RE_SANKI = re.compile(r'^(.+)参照$')
RE_YORI = re.compile(r'^(陽気|陰気)寄り$')
RE_COUNT = re.compile(r'^(単体|全体) (\d+)発$')
RE_DAN_DESC = re.compile(r'^(陽気|陰気|無)/(.+)の(.+)(弾)?。$')

# ---- 内部标识 / 編号类 ----
RE_SHOT_ID = re.compile(r'^ショット([AB]):基本に(.+)$')
RE_SHOT_USE = re.compile(r'^ショット([AB])_([NH])用$')
RE_TAISEI = re.compile(r'^(.+)の耐性属性$')
RE_LIMITED = re.compile(r'^リミテッドパック([SML])$')
RE_BASIC2 = re.compile(r'^基本に(.+?)\+基本に(.+)$')
RE_STAT_PLAIN = re.compile(
    r'^(自身|味方全体|味方単体|相手全体|相手単体|対象)の(.{1,14}?)を?(\d+)段階(アップ|ダウン|上昇|低下) ?\(?(\d+)T\)?$')

# 无 <color> 的纯文本效果行（Skill / Shot 大量出现）
RE_PE_DEPOSIT = re.compile(
    r'^(\[先行行動\])?(自身|相手全体|相手単体|味方全体|味方単体|対象)に(.{1,10}?)(\{0\}|\d+)枚付与'
    r'\((\{1\}|\d+)T\)( 付与率(\{2\}|\d+)%)?$')
RE_PE_STAT = re.compile(
    r'^(\[先行行動\])?(自身|相手全体|相手単体|味方全体|味方単体|対象)の(.{1,10}?)(\{0\}|\d+)段階'
    r'(アップ|ダウン|上昇|低下)\((\{1\}|\d+)T\)( 付与率(\{2\}|\d+)%)?$')
RE_PREFIX = re.compile(r'^([^:：]{1,14}?)(\{?\d+\}?)[:：](.+)$')
RE_PE_SEAL = re.compile(
    r'^(\[先行行動\])?(自身|相手全体|相手単体|味方全体|味方単体|対象)の(.{1,10}?)封印\((\{?\d+\}?)T\)$')

# ---- 弹幕说明句（Spellcard/Shot 的 field 3，占剩余量很大）----
WHO = {'相手単体': '敵方單體', '相手全体': '敵方全體', '自身': '自身',
       '味方全体': '己方全體', '味方単体': '己方單體', '対象': '目標', '自分': '自身'}
SHOT_MAIN = re.compile(
    r'^(相手単体|相手全体|自身|味方全体|味方単体|対象)に(.{1,8}?)(属性)?(.{0,6}?)ショット。'
    r'(陽気|陰気|無)(寄り)?(のみ)?。$')
CRIT_LINE = re.compile(r'^対象の(.{1,8}?)が上がっているとクリティカルが出やすい。$')
DIFF = {'ノーマル': '普通', 'ハード': '困難', 'ルナ': '月狂', 'EX': 'EX'}
BREAK = re.compile(r'^対象の(.{1,8}?)状態の結界をブレイクする。$')
DANMAKU = re.compile(r'^\[弾幕構成\](.+)$')
SCALE = re.compile(r'^(自身|相手全体|相手単体|味方全体|味方単体)の(.{1,10}?)が高いほどダメージが上昇する。$')
MODIFY = re.compile(r'^(自身|相手全体|相手単体|味方全体|味方単体)の(.{1,10}?)を(上げる|下げる)。$')
TAGLINE = re.compile(r'^\[(.{1,6})\](.+)$')
TAGNAME = {'攻撃前': '攻擊前', '攻撃': '攻擊', '弾幕構成': '彈幕構成', 'ブースト追加': '靈力強化追加',
           'グレイズ': '擦彈', 'ターン開始': '回合開始', '移動': '移動'}


def tr_line(line):
    m = SHOT_MAIN.match(line)
    if m:
        who, attr, _has_attr, typ, ki, yori, nomi = m.groups()
        t = DAN.get(typ) or (typ[:-1] + '彈' if typ.endswith('弾') else (typ + '彈' if typ else ''))
        a = '&'.join(ATTR.get(x, x) for x in attr.split('&'))
        k = KI.get(ki, '無') + ('偏' if yori else '')
        k = ('偏' + KI[ki]) if yori else KI.get(ki, '無')
        only = '僅' if nomi else ''
        return f'對{WHO[who]}發射{a}屬性{t}射擊。{only}{k}。'
    m = CRIT_LINE.match(line)
    if m:
        return f'目標{replace_terms(m.group(1))}提升時容易觸發會心。'
    if line == '命中すると体力を回復する。':
        return '命中時回復體力。'
    if line == '自身の結界を増加させる。':
        return '增加自身結界。'
    m = re.match(r'^相手全体に結界異常「(.{1,8}?)」を付与する。$', line)
    if m:
        return f'對敵方全體賦予結界異常「{TERM.get(m.group(1), m.group(1))}」。'
    m = re.match(r'^自身の結界を(\d+)枚増加させる。$', line)
    if m:
        return f'增加自身結界{m.group(1)}張。'
    m = BREAK.match(line)
    if m:
        st = m.group(1)
        return f'破壞目標{replace_terms(st)}狀態的結界。'
    m = DANMAKU.match(line)
    if m:
        body = m.group(1)
        body = body.replace('陽気寄り', '偏陽氣').replace('陰気寄り', '偏陰氣')
        body = body.replace('陽気のみ', '僅陽氣').replace('陰気のみ', '僅陰氣')
        body = replace_terms(body)
        return f'[彈幕構成]{body}'
    m = SCALE.match(line)
    if m:
        who, stat = m.groups()
        return f'{WHO[who]}{TERM.get(stat, stat)}越高造成的傷害越高。'
    m = MODIFY.match(line)
    if m:
        who, stat, verb = m.groups()
        v = '提升' if verb == '上げる' else '降低'
        return f'{v}{WHO[who]}{TERM.get(stat, stat)}。'
    m = TAGLINE.match(line)
    if m:
        tag, rest = m.groups()
        if tag not in TAGNAME:
            return None
        sub = tr_tag_content(rest)
        if not sub:
            return None
        return f'[{TAGNAME[tag]}]{sub}'
    return tr_tag_content(line)


def tr_tag_content(s):
    """处理「自分回避/陽防上昇。」这类句子"""
    m = re.match(r'^(自分|対象|味方全体|相手全体|自身|相手単体)(.+?)(上昇|低下|アップ|ダウン)。$', s)
    if m:
        who, stats, verb = m.groups()
        parts = [TERM.get(x, x) for x in stats.split('/')]
        return f'{WHO.get(who, who)}{"/".join(parts)}{UP.get(verb, verb)}。'
    # 纯名词性短句（例：妖精特攻光弾。）：术语替换后没有假名就算成功
    if s.endswith('。'):
        body = replace_terms(s[:-1])
        if not KANA.search(body):
            return body + '。'
    return None


def tr_multiline(s):
    if '\n' not in s:
        return None
    lines = s.split('\n')
    outs = []
    for ln in lines:
        r = tr_line(ln)
        if not r:
            return None
        outs.append(r)
    return '\n'.join(outs)


_TERM_KEYS = None
KANA = re.compile(r'[\u3040-\u30ff]')


def replace_terms(s):
    """把字符串里出现的已知术语逐个替换成繁中（长词优先）"""
    global _TERM_KEYS
    if _TERM_KEYS is None:
        _TERM_KEYS = sorted(TERM, key=len, reverse=True)
    for k in _TERM_KEYS:
        if k in s:
            s = s.replace(k, TERM[k])
    return s


RE_BARET_REF = re.compile(r'^基本バレット(.{1,8}?)参照$')
RE_SHOT_USE2 = re.compile(r'^(ショット|スペカ)([AB])_(.{1,12}?)用$')
RE_BASIC_PCT = re.compile(r'^基本に(.{1,10}?)\((\d+)%\)$')
RE_BASIC_PCT2 = re.compile(r'^基本に(.{1,10}?)(\d+)%$')
RE_KEKKA_PLAIN = re.compile(r'^味方全体の(結界|結界異常)(\d+)枚回復$')
RE_EXDIFF = re.compile(r'^EX(\S{1,6})$')
RE_BARET_ATTR2 = re.compile(r'^基本バレット(.{1,4}?)属性$')
RE_SHOT_MID = re.compile(r'^ショットとスペカの中間$')
RE_BARRIER_LINE = re.compile(r'^対象に結界異常「(.{1,8}?)」を付与する。$')
RE_PE_PCT_PLAIN = re.compile(r'^(自身|味方全体|相手全体|相手単体|対象)の(.{1,8}?)(\d+)%回復$')
RE_KEKKA_SIMPLE = re.compile(r'^結界を(\d+)枚回復$')
RE_NAME_SHOT = re.compile(r'^(.{2,8}?)ショット$')
RE_BASIC_BARET = re.compile(r'^基本バレット(.{1,8}?)(\d+%)?$')
RE_BASIC_NO = re.compile(r'^基本の(.{1,10})$')
RE_KEKKA_REC2 = re.compile(r'^(自身|味方全体|相手全体|相手単体|対象)の(結界|結界異常)(\d+)枚(回復|増加)$')
RE_STUN = re.compile(r'^(?:対象|自身|相手全体)に(.{1,6}?)付与\((\{1\}|\d+)T\)( 付与率(\d+)%)?$')
RE_SINGLE_DELAY = re.compile(r'^(単体|全体) (\d+)発(.{1,10}?)\((\d+)%\)$')
RE_NAME_SHOT2 = re.compile(r'^(.{1,10}?)[ 　](ショット|スペカ)([AB])$')
RE_USE_SHOT = re.compile(r'^(.{1,10}?)用(ショット|スペカ)([AB])$')
RE_ALLBARET_ATTR = re.compile(r'^全バレット(.{1,4}?)属性$')
RE_ALLBARET_ADD = re.compile(r'^全バレットに(.{1,10})$')
RE_BARET_POWER = re.compile(r'^バレット威力期待値(\d+)$')
RE_BARET_OF = re.compile(r'^基本バレットの(.{1,16})$')
RE_BARET_ATTR = re.compile(r'^基本バレットが(.{1,4}?)属性$')
RE_KEKKA = re.compile(
    r'^(自身|味方全体|相手全体|相手単体|対象)の' + C + r'(結界|結界異常)</color>を(\{0\}|\d+)枚' +
    C + r'(増加|回復)</color>( ?\[発生率\{1\}%で追加効果\+\{2\}\])?$')
RE_DMG_DOWN = re.compile(
    r'^(自身|味方全体|相手全体|相手単体|対象)の' + C + r'([^<]{1,10})</color>から受けるダメージを'
    r'(\d+)%' + C + r'(ダウン|アップ|上昇|低下)</color> ?\((\d+)T\)$')
RE_APPLY = re.compile(
    r'^(自身|味方全体|相手全体|相手単体|対象)に' + C + r'([^<]{1,12})</color>を' + C + r'付与</color>$')


def tr_ui_label(s):
    m = RE_BARET_REF.match(s)
    if m:
        r = m.group(1)
        return '基礎彈幕參照' + (KI.get(r) or attr_of(r))
    m = RE_SHOT_USE2.match(s)
    if m:
        kind, ab, name = m.groups()
        nm = replace_terms(name)
        return f'{"射擊" if kind == "ショット" else "符卡"}{ab}_{nm}用'
    m = RE_BASIC_PCT.match(s)
    if m:
        name, pct = m.groups()
        t = DAN.get(name) or DAN.get(name + '弾') or name
        return f'基礎附加{t}({pct}%)'
    m = RE_BASIC_PCT2.match(s)
    if m:
        name, pct = m.groups()
        t = DAN.get(name) or DAN.get(name + '弾') or name
        return f'基礎附加{t}{pct}%'
    m = RE_KEKKA_PLAIN.match(s)
    if m:
        stat, n = m.groups()
        return f'己方全體{stat}回復{n}張'
    m = RE_EXDIFF.match(s)
    if m:
        return 'EX' + DIFF.get(m.group(1), m.group(1))
    m = RE_BARET_ATTR2.match(s)
    if m:
        return f'基礎彈幕{ATTR.get(m.group(1), m.group(1))}屬性'
    m = RE_SHOT_MID.match(s)
    if m:
        return '射擊與符卡之間'
    m = RE_BARRIER_LINE.match(s)
    if m:
        return f'對目標賦予結界異常「{TERM.get(m.group(1), m.group(1))}」。'
    m = RE_PE_PCT_PLAIN.match(s)
    if m:
        who, stat, pct = m.groups()
        return f'{TARGET[who]}{TERM.get(stat, stat)}{pct}%回復'
    m = RE_KEKKA_SIMPLE.match(s)
    if m:
        return f'結界回復{m.group(1)}張'
    m = RE_NAME_SHOT.match(s)
    if m:
        return replace_terms(m.group(1)) + '射擊'
    m = RE_BASIC_BARET.match(s)
    if m:
        name, pct = m.groups()
        t = DAN.get(name) or DAN.get(name + '弾') or replace_terms(name)
        return f'基礎彈幕{t}{pct or ""}'
    m = RE_BASIC_NO.match(s)
    if m:
        return '基礎的' + replace_terms(m.group(1))
    m = RE_KEKKA_REC2.match(s)
    if m:
        who, stat, n, verb = m.groups()
        return f'{TARGET[who]}{stat}{UP.get(verb, verb)}{n}張'
    m = RE_STUN.match(s)
    if m:
        what, t, rate_all, _r = m.groups()
        out = f'對目標賦予{TERM.get(what, what)} ({t}回合)'
        if rate_all:
            out += rate_all.replace('付与率', '賦予率')
        return out
    m = RE_SINGLE_DELAY.match(s)
    if m:
        who, n, what, pct = m.groups()
        return f'{"單體" if who == "単体" else "全體"} {n}發{replace_terms(what)}({pct}%)'
    m = RE_NAME_SHOT2.match(s)
    if m:
        name, kind, ab = m.groups()
        nm = NAME_EXACT.get(name) or replace_terms(name)
        return f'{nm} {"射擊" if kind == "ショット" else "符卡"}{ab}'
    m = RE_ALLBARET_ATTR.match(s)
    if m:
        return f'全彈幕{ATTR.get(m.group(1), m.group(1))}屬性'
    m = RE_ALLBARET_ADD.match(s)
    if m:
        rest = m.group(1)
        m2 = re.match(r'^(.+?)\((\d+)%\)$', rest)
        if m2:
            return f'全彈幕附加{DAN.get(m2.group(1), m2.group(1))}({m2.group(2)}%)'
        if rest.endswith('属性'):
            return f'全彈幕附加{ATTR.get(rest[:-2], rest[:-2])}屬性'
        return f'全彈幕附加{DAN.get(rest, replace_terms(rest))}'
    m = RE_USE_SHOT.match(s)
    if m:
        name, kind, ab = m.groups()
        nm = NAME_EXACT.get(name) or replace_terms(name)
        return f'{nm}用{"射擊" if kind == "ショット" else "符卡"}{ab}'
    if s == '威力スペカ相当':
        return '威力相當於符卡'
    m = RE_BARET_POWER.match(s)
    if m:
        return f'彈幕威力期望值{m.group(1)}'
    m = RE_BARET_OF.match(s)
    if m:
        return '基礎彈幕的' + replace_terms(m.group(1))
    m = RE_BARET_ATTR.match(s)
    if m:
        return f'基礎彈幕為{ATTR.get(m.group(1), m.group(1))}屬性'
    m = RE_KEKKA.match(s)
    if m:
        who, c1, stat, n, c2, verb, tail = m.groups()
        unit = '張' if stat == '結界' else '枚'
        out = f'{TARGET[who]}<color={c1}>{stat}</color><color={c2}>{UP.get(verb, verb)}</color>{n}{unit}'
        if tail:
            out += ' [發生率{1}%追加效果+{2}]'
        return out
    m = RE_DMG_DOWN.match(s)
    if m:
        who, c1, src, pct, c2, verb, t = m.groups()
        return f'{TARGET[who]}受到<color={c1}>{replace_terms(src)}</color>傷害{pct}%<color={c2}>{UP.get(verb, verb)}</color> ({t}回合)'
    m = RE_APPLY.match(s)
    if m:
        who, c1, what, c2 = m.groups()
        return f'{TARGET[who]}<color={c1}>{replace_terms(what)}</color><color={c2}>賦予</color>'
    return None


def tr_pct_term(s):
    m = re.match(r'^(.+?)(基礎値|率)(\d+(?:\.\d+)?%?)$', s)
    if m:
        head, kind, num = m.groups()
        head = replace_terms(head)
        kind = {'基礎値': '基礎值', '率': '率'}[kind]
        return f'{head}{kind}{num}'
    return None


def tr_plain_effect(s):
    m = RE_PE_DEPOSIT.match(s)
    if m:
        adv, who, name, n, t, rate_all, _r = m.groups()
        out = f'{"[先行行動]" if adv else ""}對{TARGET[who]}賦予{n}枚{TERM.get(name, name)} ({t}回合)'
        if rate_all:
            out += rate_all.replace('付与率', '賦予率')
        return out
    m = RE_PE_STAT.match(s)
    if m:
        adv, who, stat, n, verb, t, rate_all, _r = m.groups()
        out = (f'{"[先行行動]" if adv else ""}{TARGET[who]}{TERM.get(stat, stat)}'
               f'{UP.get(verb, verb)}{n}等級 ({t}回合)')
        if rate_all:
            out += rate_all.replace('付与率', '賦予率')
        return out
    m = RE_PE_SEAL.match(s)
    if m:
        adv, who, what, t = m.groups()
        return f'{"[先行行動]" if adv else ""}{TARGET[who]}{replace_terms(what)}封印 ({t}回合)'
    m = RE_PREFIX.match(s)
    if m:
        head, idx, rest = m.groups()
        sub = tr_plain_effect(rest)
        if sub:
            return f'{head}{idx}:{sub}'
    return None


def tr_plain_stat(s):
    m = RE_STAT_PLAIN.match(s)
    if m:
        who, stat, n, verb, t = m.groups()
        return f'{TARGET[who]}{TERM.get(stat, stat)}{UP.get(verb, verb)}{n}等級 ({t}回合)'
    return None


RE_DOUBLE_STAT = re.compile(
    r'^基本に(.{1,14}?)\+(自身|味方全体|味方単体|相手全体|相手単体)の(.{1,8}?)\+(.{1,8}?)'
    r'(\d+)段階(アップ|ダウン|上昇|低下) ?\(?(\d+)T\)?$')


def tr_id(s):
    m = RE_DOUBLE_STAT.match(s)
    if m:
        base, who, a, b, n, verb, t = m.groups()
        base_tw = tr_bullet('基本に' + base) or ('基礎附加' + base)
        return f'{base_tw}+{TARGET[who]}{TERM.get(a, a)}/{TERM.get(b, b)}{UP.get(verb, verb)}{n}等級 ({t}回合)'
    m = RE_SHOT_ID.match(s)
    if m:
        return f'射擊{m.group(1)}:基礎附加{tr_bullet("基本に" + m.group(2)) or m.group(2)}'
    m = RE_SHOT_USE.match(s)
    if m:
        return f'射擊{m.group(1)}_{m.group(2)}用'
    m = RE_LIMITED.match(s)
    if m:
        return f'限定禮包{m.group(1)}'
    m = RE_BASIC2.match(s)
    if m:
        a = tr_bullet('基本に' + m.group(1)) or ('基礎附加' + m.group(1))
        b = tr_bullet('基本に' + m.group(2)) or ('基礎附加' + m.group(2))
        return a + '+' + b
    m = RE_TAISEI.match(s)
    if m:
        return f'{tr_id(m.group(1)) or m.group(1)}的耐性屬性'
    if '+' in s:
        outs = []
        for part in s.split('+'):
            r = (tr_ui_label(part) or tr_bullet(part) or tr_plain_stat(part) or tr_shop(part)
                 or EXACT.get(part) or tr_plain_effect(part) or tr_placeholder(part)
                 or tr_pct_term(part))
            if not r:
                rp = replace_terms(part)
                if (not KANA.search(rp) and re.search(r'[\u4e00-\u9fff]', rp)) or part in ('陽', '陰', 'CRI', '無'):
                    r = rp
            if not r:
                outs = None
                break
            outs.append(r)
        if outs:
            return '+'.join(outs)
    if s in ('スペカ', 'ショット'):
        return {'スペカ': '符卡', 'ショット': '射擊'}[s]
    return None

# ---- 商店礼包名 ----
SHOP = {
    '昇格': '晉升', '限界突破': '界限突破', 'ステップアップ': '階段式', 'サポート': '支援',
    '色々な素材': '各種素材', '白フェス祭絵馬': '白色祭典繪馬', '祭絵馬': '祭典繪馬',
    '人形代': '人形代', '大形代': '大形代', '靈形代': '靈形代', '天形代': '天形代',
    '巫形代': '巫形代', '華片と巻物': '華片與卷軸', '衣装': '服裝', '素材': '素材',
    '必要な': '所需的', 'に必要な': '所需的', 'と': '與', '＆': '＆',
}
RE_PACK = re.compile(r'^(.+?)が入ったお得な(パック|セット)$')
RE_PACK2 = re.compile(r'^(.+?)パック$')


def tr_shop_term(s):
    for k in sorted(SHOP, key=len, reverse=True):
        s = s.replace(k, SHOP[k])
    return s


def tr_shop(s):
    m = RE_PACK.match(s)
    if m:
        return f'內含{tr_shop_term(m.group(1))}的超值{"禮包" if m.group(2) == "パック" else "套組"}'
    m = RE_PACK2.match(s)
    if m:
        return f'{tr_shop_term(m.group(1))}禮包'
    if s.endswith('イベント') or '月イベント' in s:
        return s.replace('イベント', '活動')
    if re.fullmatch(r'イベント\d+', s):
        return s.replace('イベント', '活動')
    return None


def attr_of(x):
    if x.endswith('属性') and x[:-2] in ATTR:
        return ATTR[x[:-2]] + '屬性'
    return ATTR.get(x, x)


def tr_bullet(s):
    m = RE_BARET_ADD.match(s)
    if m:
        rest = m.group(1)
        m2 = re.match(r'^(.+?)\((\d+)%\)$', rest)
        if m2:
            name = DAN.get(m2.group(1), m2.group(1))
            return f'基礎彈幕附加{name}({m2.group(2)}%)'
        return f'基礎彈幕附加{DAN.get(rest, rest)}'
    m = RE_ATTR_ONLY.match(s)
    if m and m.group(1) in ATTR:
        return f'{ATTR[m.group(1)]}屬性'
    m = RE_KIHON.match(s)
    if m:
        rest = m.group(1)
        if rest.endswith('属性') and rest[:-2] in ATTR:
            return f'基礎附加{ATTR[rest[:-2]]}屬性'
        if rest in DAN:
            return f'基礎附加{DAN[rest]}'
        if rest in TERM:
            return f'基礎附加{TERM[rest]}'
        m2 = re.match(r'^(.+)\((\d+)%\)$', rest)
        if m2 and m2.group(1) in DAN:
            return f'基礎附加{DAN[m2.group(1)]}({m2.group(2)}%)'
    m = RE_ALLBARET.match(s)
    if m:
        r = m.group(1)
        return '全彈幕參照' + (KI.get(r) or attr_of(r))
    m = RE_SANKI.match(s)
    if m and m.group(1) in KI:
        return f'參照{KI[m.group(1)]}'
    m = RE_YORI.match(s)
    if m:
        return f'偏{KI[m.group(1)]}'
    m = RE_COUNT.match(s)
    if m:
        return f'{"單體" if m.group(1) == "単体" else "全體"} {m.group(2)}發'
    m = RE_DAN_DESC.match(s)
    if m:
        a, b, typ, _dan = m.groups()
        k = KI.get(a) or attr_of(a)
        if typ == '斬撃':
            t = '斬擊'
        elif typ in DAN:
            t = DAN[typ]
        elif typ == '流体':
            t = '流體'
        else:
            t = typ + '彈'
        return f'{k}/{attr_of(b)}{t}。'
    return None


RE_MISSION_CLEAR = re.compile(r'^(.+?)をクリアしよう$')
RE_MISSION_STAR = re.compile(r'^(.+?)の★を全て取ろう$')
RE_MISSION_N = re.compile(r'^(.+?)を(\d+)回クリアしよう$')
RE_MISSION_WIN = re.compile(r'^(.+?)で(\d+)回勝利しよう$')
RE_MISSION_DAILY = re.compile(r'^(.+?)を1日(\d+)回クリアしよう$')
RE_M_DONE_N = re.compile(r'^(.+?)を(\d+)回完了させよう$')
RE_M_DONE = re.compile(r'^(.+?)を完了させよう$')
RE_M_COUNT = re.compile(r'^(.+?)を(\d+)つクリアしよう$')


def _inner(name):
    return NAME_EXACT.get(name) or EXACT.get(name)


def tr_mission(s):
    m = RE_M_DONE_N.match(s)
    if m and _inner(m.group(1)):
        return f'完成{m.group(2)}次{_inner(m.group(1))}'
    m = RE_M_DONE.match(s)
    if m and _inner(m.group(1)):
        return f'完成{_inner(m.group(1))}'
    m = RE_M_COUNT.match(s)
    if m and _inner(m.group(1)):
        return f'通關{m.group(2)}個{_inner(m.group(1))}'
    m = RE_MISSION_DAILY.match(s)
    if m:
        name, n = m.groups()
        inner = NAME_EXACT.get(name) or EXACT.get(name)
        if inner:
            return f'每天通關{n}次{inner}'
    for pat, fmt in ((RE_MISSION_N, '通關{n}次{name}'), (RE_MISSION_CLEAR, '通關{name}吧'),
                     (RE_MISSION_STAR, '取得{name}的全部★'), (RE_MISSION_WIN, '在{name}勝利{n}次')):
        m = pat.match(s)
        if not m:
            continue
        if pat is RE_MISSION_N or pat is RE_MISSION_WIN:
            name, n = m.group(1), m.group(2)
            inner = NAME_EXACT.get(name) or EXACT.get(name)
            if inner:
                return fmt.format(name=inner, n=n)
        else:
            name = m.group(1)
            inner = NAME_EXACT.get(name) or EXACT.get(name)
            if inner:
                return fmt.format(name=inner)
    return None


# ============================================================ v3 收尾：剩余长尾模板族
# lw_visible.py v2 判出的「真正待译」8624 条里，绝大多数仍是模板句，
# 只是内嵌了国服没有的专有标题（メイン名 / エピソード名 / 絵札名）。
# 这一层负责骨架，内层专有名词交给 titles_exact.json（第 4 步人工补）。
TITLE = {}
for _fn in ('titles_exact.json', 'atoms_tw.json', 'components.json'):
    _p2 = os.path.join(ROOT, 'lw_work', _fn)
    if os.path.exists(_p2):
        TITLE.update(json.load(open(_p2, encoding='utf-8')))

TERM2 = {
    'アニバーサリー': '週年', 'ステップアップ': '階段', '衣装': '服裝',
    '運命強化': '命運強化', '特別霊P': '特別靈P', '霊P': '靈P',
    '復刻': '復刻', '短縮版': '短縮版', 'プロローグ': '序章', 'エピローグ': '終章',
    '最終回': '最終回', '先行行動': '先行行動', '付喪神': '付喪神',
    'ラジオ体操': '廣播體操', 'ブートキャンプ': '集訓營',
}
TERM.update({k: v for k, v in TERM2.items() if k not in TERM})

SHOT_KIND = {'ショット': '射擊', 'スペカ': '符卡', 'ラスワ': '最終符卡'}

# 弹种 / 属性后缀的语法骨架术语（must 排在 TERM 之前先吃掉，否则 属性 会插进 レーザー弾 中间）
GRAMMAR = [
    ('基本に', '基礎附加'),
    ('のみ', '僅有'), ('寄り', '偏'), ('均衡', '均衡'),
]


# 弹种名：必须先整词替换，否则 属性/弾 会被插进词中间产生「レーザ屬性ー弾」
BULLET_TERMS = [('レーザー弾', '雷射彈'), ('ミサイル弾', '飛彈'), ('エネルギー弾', '能量彈'),
                ('レーザー', '雷射'), ('ミサイル', '飛彈'), ('エネルギー', '能量')]


def pre_norm(s):
    """先干掉对术语替换最致命的日语骨架与弹种词，避免「レーザ屬性ー弾」这类错切。"""
    for a, b in GRAMMAR:
        s = s.replace(a, b)
    # 弹种词必须整词先换（长词优先），否则 属性/弾 会被插进词中间
    for a, b in BULLET_TERMS:
        s = s.replace(a, b)
    return s


def _title(x):
    """内层专有名词：精确表 -> 术语替换；仍残留假名就放弃（留给人工）"""
    x = x.strip().strip('「」')
    for d in (TITLE, NAME_EXACT, EXACT):
        v = d.get(x)
        if v:
            return v
    v = replace_terms(x)
    return None if KANA.search(v) else v


def _name_any(x):
    """名字部分可能含 _ 分隔（絵札名_角色名），逐段翻译"""
    x = x.strip()
    if '_' in x:
        parts = [_title(p) for p in x.split('_')]
        return '_'.join(parts) if all(parts) else None
    return _title(x)


def _inner(x):
    """内层效果串：先规范骨架，再试战斗子句，再让既有规则跑，最后退到术语替换"""
    x = pre_norm(x.strip())
    t = tr_clause(x) or tr_one(x)
    if t:
        return t
    v = replace_terms(x)
    return None if KANA.search(v) else v


# ---- 任务 Mission ----
RE_M2_DAILY = re.compile(r'^(.+?)を1日(\d+)回クリアしよう$')
RE_M2_NCLEAR = re.compile(r'^(.+?)を(\d+)回クリアしよう$')
RE_M2_NDONE = re.compile(r'^(.+?)を(\d+)回完了させよう$')
RE_M2_NCNT = re.compile(r'^(.+?)を(\d+)つクリアしよう$')
RE_M2_WIN = re.compile(r'^(.+?)で(\d+)回勝利しよう$')
RE_M2_STARN = re.compile(r'^(.+?)の★を(\d+)個取ろう$')
RE_M2_STAR = re.compile(r'^(.+?)の★を全て取ろう$')
RE_M2_DONE = re.compile(r'^(.+?)を完了させよう$')
RE_M2_CLEAR = re.compile(r'^(.+?)をクリアしよう$')
RE_M2_CLEAR2 = re.compile(r'^(.+?)をクリア$')


def tr_mission2(s):
    for pat, fmt in ((RE_M2_DAILY, '每天通關{n}次：{t}'),
                     (RE_M2_NCLEAR, '通關{n}次：{t}'),
                     (RE_M2_NDONE, '完成{n}次：{t}'),
                     (RE_M2_NCNT, '通關{n}個：{t}'),
                     (RE_M2_WIN, '在{t}勝利{n}次'),
                     (RE_M2_STARN, '取得{t}的{n}個★'),
                     (RE_M2_STAR, '取得{t}的全部★'),
                     (RE_M2_DONE, '完成{t}'),
                     (RE_M2_CLEAR, '通關{t}'),
                     (RE_M2_CLEAR2, '通關{t}')):
        m = pat.match(s)
        if not m:
            continue
        g = m.groups()
        t = _name_any(g[0])
        if not t:
            return None
        return fmt.format(t=t) if len(g) == 1 else fmt.format(t=t, n=g[1])
    return None


# ---- 招式槽位效果（Bullet[2] / Skill[2] / Shot[3]）----
RE_SLOT_EFF = re.compile(r'^\[(ショット|スペカ|ラスワ)([AB])\](.+)$')
RE_SLOT_COLON = re.compile(r'^(ショット|スペカ|ラスワ)([AB])[:：](.+)$')


def tr_slot_eff(s):
    m = RE_SLOT_COLON.match(s)
    if m:
        kind, ab, rest = m.groups()
        inner = tr_plus(rest) or _inner(rest)
        return f'{SHOT_KIND[kind]}{ab}:{inner}' if inner else None
    m = RE_SLOT_EFF.match(s)
    if m:
        kind, ab, rest = m.groups()
        inner = tr_plus(rest) or _inner(rest)
        return f'[{SHOT_KIND[kind]}{ab}]{inner}' if inner else None
    return None


# ---- 技能括号标签（Skill[2]）----
RE_BSKILL = re.compile(r'^\[(スキル\d*|先行行動|攻撃前|ブースト追加|弾幕構成)\](.+)$')
BSKILL = {'先行行動': '先行行動', '攻撃前': '攻擊前',
          'ブースト追加': '靈力強化追加', '弾幕構成': '彈幕構成'}


def tr_skill_tag(s):
    m = RE_BSKILL.match(s)
    if not m:
        return None
    tag, rest = m.groups()
    out_tag = '技能' + tag[3:] if tag.startswith('スキル') else BSKILL[tag]
    inner = tr_plus(rest) or _inner(rest)
    return f'[{out_tag}]{inner}' if inner else None


# ---- 「名字 + ショット/スペカ/ラスワ A/B」（Bullet[1] / Shot[1] / Shot[2]）----
RE_SLOT_NAME = re.compile(r'^(.+?)[ 　]*(ショット|スペカ|ラスワ)([AB])?$')


def tr_slot_name(s):
    m = RE_SLOT_NAME.match(s)
    if not m:
        return None
    name, kind, ab = m.groups()
    n = _name_any(name)
    return f'{n}{SHOT_KIND[kind]}{ab or ""}' if n else None


# ---- 章节/话数（Episode / Section / Chapter）----
RE_EP_EX = re.compile(r'^EX[ 　]+(.+)$')
RE_EP_N = re.compile(r'^(.+?)第(\d+)回$')
RE_EP_LAST = re.compile(r'^(.+?)最終回$')
RE_EP_PRO = re.compile(r'^(.+?)[ 　・]+プロローグ$')
RE_EP_EPI = re.compile(r'^(.+?)[ 　・]+エピローグ$')
RE_EP_DAY = re.compile(r'^(.+?)[ 　]+(\d+)日目$')


def tr_episode(s):
    m = RE_EP_N.match(s)
    if m:
        t = _name_any(m.group(1))
        return f'{t}第{m.group(2)}回' if t else None
    m = RE_EP_LAST.match(s)
    if m:
        t = _name_any(m.group(1))
        return f'{t}最終回' if t else None
    m = RE_EP_PRO.match(s) or RE_EP_EPI.match(s)
    if m:
        t = _name_any(m.group(1))
        if not t:
            return None
        return f'{t}序章' if 'プロローグ' in s else f'{t}終章'
    m = RE_EP_DAY.match(s)
    if m:
        t = _name_any(m.group(1))
        return f'{t}第{m.group(2)}天' if t else None
    m = RE_EP_EX.match(s)
    if m:
        t = _name_any(m.group(1))
        return f'EX {t}' if t else None
    return None


# ---- 商店礼包（ValuePackShop / FeatureProductShop）----
RE_PACK_TAIL = re.compile(r'^(.+?)(パック|セット)([SML]|\d+)?$')


def tr_pack(s):
    m = RE_PACK_TAIL.match(s)
    if not m:
        return None
    head, kind, num = m.groups()
    h = _inner(head)
    if not h:
        return None
    return f'{h}{"包" if kind == "パック" else "套組"}{num or ""}'


# ---- 「X程度の声」（VoiceSet）----
RE_VOICE_KIND = re.compile(r'^(.+?)程度の声$')


def tr_voice_kind(s):
    m = RE_VOICE_KIND.match(s)
    if not m:
        return None
    t = _name_any(m.group(1))
    return f'{t}程度的聲音' if t else None


# ---- 战斗效果子句（用 + 串联，Bullet[2] / Skill[2] / SkillEffect / Spellcard[3]）----
CL_WHO = {'味方全体': '己方全體', '味方単体': '己方單體', '相手全体': '敵方全體',
          '相手単体': '敵方單體', '自身': '自身', '対象': '目標'}
CL_FLAT = [
    (re.compile(r'^(味方全体|味方単体|相手全体|相手単体|自身|対象)の(.+?)特防(\d+)%\((\d+)T\)$'),
     lambda m: f'{CL_WHO[m.group(1)]}的{m.group(2)}特防{m.group(3)}%({m.group(4)}回合)'),
    (re.compile(r'^(味方全体|味方単体|相手全体|相手単体|自身|対象)の(.+?)(\d+)段階(アップ|ダウン)\((\d+)T\)$'),
     lambda m: f'{CL_WHO[m.group(1)]}的{m.group(2)}{m.group(3)}階段{UP.get(m.group(4), m.group(4))}({m.group(5)}回合)'),
    (re.compile(r'^(味方全体|味方単体|相手全体|相手単体|自身|対象)の(.+?)(\d+)%回復\((\d+)T\)$'),
     lambda m: f'{CL_WHO[m.group(1)]}的{m.group(2)}{m.group(3)}%回復({m.group(4)}回合)'),
    (re.compile(r'^(味方全体|味方単体|相手全体|相手単体)に(.+?)(\d+)枚付与\((\d+)T\)$'),
     lambda m: f'對{CL_WHO[m.group(1)]}賦予{m.group(3)}枚{m.group(2)}({m.group(4)}回合)'),
    (re.compile(r'^自身に「(.+?)」種族特攻\((\d+)T\)$'),
     lambda m: f'自身對「{m.group(1)}」種族特攻({m.group(2)}回合)'),
    (re.compile(r'^(味方全体|味方単体|相手全体|相手単体|自身|対象)の(.+?)を(\d+)段階(アップ|ダウン)$'),
     lambda m: f'{CL_WHO[m.group(1)]}的{m.group(2)}{m.group(3)}階段{UP.get(m.group(4), m.group(4))}'),
    (re.compile(r'^基本附加(.+)$'),
     lambda m: '基礎附加' + (replace_terms(m.group(1)))),
]


def tr_clause(s):
    s = pre_norm(s.strip())
    for pat, fn in CL_FLAT:
        m = pat.match(s)
        if m:
            out = fn(m)
            if not KANA.search(out):
                return out
            break
    # 兜底：术语替换 + 去掉残留的日语格助词
    v = replace_terms(s)
    # 长词先换过一遍后，残留的单字「弾」和「属性」统一转繁
    v = v.replace('弾', '彈').replace('属性', '屬性')
    v = re.sub(r'(?<=[\u4e00-\u9fff])の(?=[\u4e00-\u9fff])', '的', v)
    # 战斗子句里残留的 (5T) 补成 (5回合)
    v = re.sub(r'\((\d+)T\)', r'(\1回合)', v)
    return None if KANA.search(v) else v


def tr_plus(s):
    """按 + 切段，每段都要能翻才拼回去；任一段失败就整体放弃"""
    parts = s.split('+')
    if len(parts) < 2:
        return None
    out = []
    for p in parts:
        t = tr_clause(p)
        if not t:
            return None
        out.append(t)
    return '+'.join(out)


# ---- 弹幕描述首行：相手X体に(属性&…)(弹种)ショット。陰気寄り。----
RE_DANMAKU_HEAD = re.compile(
    r'^(相手全体|相手単体|対象)(に|へ)(.+?)(ショット|弾幕|攻撃)。?(陰陽均衡|陰気寄り|陽気寄り|陰気のみ|陽気のみ)?。?$')


def tr_danmaku_head(s):
    m = RE_DANMAKU_HEAD.match(s)
    if not m:
        return None
    who, _p, body, kind, mood = m.groups()
    b = pre_norm(body)
    b = replace_terms(b)
    b = b.replace('弾', '彈').replace('属性', '屬性')
    tgt = {'相手全体': '敵方全體', '相手単体': '敵方單體', '対象': '目標'}[who]
    kd = {'ショット': '射擊', '弾幕': '彈幕', '攻撃': '攻擊'}[kind]
    mood_m = {'陰陽均衡': '陰陽均衡', '陰気寄り': '偏陰氣', '陽気寄り': '偏陽氣',
              '陰気のみ': '僅陰氣', '陽気のみ': '僅陽氣'}
    out = f'對{tgt}發射{b}{kd}。'
    if mood:
        out += mood_m[mood] + '。'
    return None if KANA.search(out) else out


def tr_danmaku(s):
    """多行弹幕描述：逐行翻，全行都成功才拼回去"""
    lines = s.split('\n')
    out = []
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        t = tr_danmaku_head(ln)
        if not t:
            t = tr_clause(ln)
        if not t:
            t = tr_line(ln)
        if not t:
            return None
        out.append(t)
    return '\n'.join(out) if out else None


def tr_late(s):
    for fn in (tr_mission2, tr_slot_eff, tr_skill_tag, tr_slot_name,
               tr_episode, tr_pack, tr_voice_kind, tr_plus, tr_danmaku):
        t = fn(s)
        if t:
            return t
    return None


def tr_one(s):
    if s in EXACT:
        return EXACT[s]
    norm = s.replace('％', '%')
    s = norm
    t = tr_ui_label(norm)
    if t:
        return t
    m = RE_STAT.match(s)
    if m:
        who, c1, stat, n, c2, verb, t = m.groups()
        term = TERM.get(stat, stat)
        v = UP.get(verb, verb)
        return f'{TARGET[who]}<color={c1}>{term}</color>{v}{n}等級 ({t}回合)'
    m = RE_BARRIER.match(s)
    if m:
        who, c1, name, n, c2, t = m.groups()
        return f'對{TARGET[who]}<color={c1}>「{TERM.get(name, name)}」</color>賦予{n}枚結界異常 ({t}回合)'
    m = RE_BARRIER_PH.match(s)
    if m:
        who, c1, name, _c2, t, tail = m.groups()
        out = f'對{TARGET[who]}賦予{{0}}枚結界異常「<color={c1}>{TERM.get(name, name)}</color>」 ({t}回合)'
        if tail:
            out += ' [發生率{1}%追加效果+{2}]'
        return out
    m = RE_STAT_PCT.match(s)
    if m:
        who, c1, stat, pct, c2, verb = m.groups()
        return f'{TARGET[who]}<color={c1}>{TERM.get(stat, stat)}</color>{pct}%<color={c2}>{UP.get(verb, verb)}</color>'
    m = RE_WIN.match(s)
    if m:
        d, n = m.groups()
        return f'戰鬥中{d}天內勝利{n}次'
    m = RE_EVENT_WIN.match(s)
    if m:
        return f'在活動探索的戰鬥中勝利{m.group(1)}次'
    m = RE_GACHA.match(s)
    if m:
        return f'進行{m.group(1)}次祈願'
    if 'ログイン' in s and s.endswith(('しよう', 'をしよう')):
        return '登入遊戲吧'
    t = tr_placeholder(s)
    if t:
        return t
    t = tr_plain_effect(s)
    if t:
        return t
    t = tr_mission(s)
    if t:
        return t
    t = tr_shop(s)
    if t:
        return t
    # 收尾族必须在 tr_bullet / tr_line 之前：它们要先剥掉 [先行行動] 这类前缀、
    # 再把 + 复合串按分句切干净，否则会被下面几族截成半截译文。
    t = tr_late(s)
    if t:
        return t
    t = tr_id(s)
    if t:
        return t
    t = tr_bullet(s)
    if t:
        return t
    t = tr_multiline(s) if '\n' in s else tr_line(s)
    if t:
        return t
    # 最后兜底：整串命中名字/短语词表
    return NAME_EXACT.get(s)


def main():
    # 规则内部用繁中字典书写；简体模式下把最终结果转成简体。
    from lw_cc import to_simplified, MODE as _CCMODE
    # 跳过「国服原文 / 汉化包 / 名词表 / 模板库 / 人工」已覆盖的字段；
    # 规则自己上一轮的结果不能当输入。
    # 注意：trans_cnpatch / trans_manual 的优先级低于规则层，若不在这里预读，
    # 规则会生成更差的文本去覆盖汉化包的高质量译文。
    trans = {}
    for p in ('trans_cn_tw.json', 'trans_cnpatch.json', 'trans_names.json',
              'trans_tm.json', 'trans_manual.json'):
        fp = os.path.join(ROOT, 'lw_work', p)
        if not os.path.exists(fp):
            continue
        d = json.load(open(fp, encoding='utf-8'))
        for tbl, rows in d.items():
            t = trans.setdefault(tbl, {})
            for k, f in rows.items():
                t.setdefault(k, {}).update(f)
    out = {}
    hit = miss = kana_rej = 0
    samples = []
    for tbl, h in sorted(NAMES.items()):
        p = os.path.join(ROOT, 'dumped', h + '.msgpack')
        if not os.path.exists(p):
            continue
        jp = msgpack.unpackb(open(p, 'rb').read(), raw=False, strict_map_key=False)
        if not isinstance(jp, dict):
            continue
        done = trans.get(tbl, {})
        rows = {}
        for k, jv in jp.items():
            if not isinstance(jv, list):
                continue
            df = done.get(str(k), {})
            for i, x in enumerate(jv):
                if not isinstance(x, str) or str(i) in df:
                    continue
                tw = tr_one(x)
                if tw and _CCMODE == 'sc':
                    tw = to_simplified(tw)
                if not tw or tw == x:
                    miss += 1
                    continue
                # 质量闸门：结果仍含假名 = 根本没翻（例如只把 ・ 换成 ·），丢弃
                if KANA.search(tw):
                    kana_rej += 1
                    continue
                rows.setdefault(str(k), {})[str(i)] = tw
                hit += 1
                if len(samples) < 12:
                    samples.append((x, tw))
        if rows:
            out[tbl] = rows
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)
    print(f'规则命中 {hit} 字段，未命中 {miss}，因残留假名丢弃 {kana_rej}')
    for a, b in samples:
        print(f'  日: {a[:80]}\n  繁: {b[:80]}')


if __name__ == '__main__':
    main()
