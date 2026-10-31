"""MV版のクラシック版の曲を、JingleScript の楽譜（JSON）として書き出す（mv/classic.json）。

映像はEDM版と同じ拍の表で動くので、テンポ 128・全146拍の組み立てはEDM版と同じにして、
文字が叩きつけられる拍・数が数え上がる拍・家やはんこが並ぶ拍などに、同じように音を置く。
使っている旋律は、どれも著作権の切れたクラシックの冒頭（リズムは映像に合わせて少し変えている）。
  0〜8   バッハ「トッカータとフーガ ニ短調」の出だし（オルガン）：1拍に1文字
  8〜16  ベートーヴェン「運命」の「ダダダダーン」
  16〜48 モーツァルト「アイネ・クライネ・ナハトムジーク」（01 本）
  48〜80 ベートーヴェン「歓喜の歌」（中の上の人生戦略）
  80〜96 パッヘルベル「カノン」の低音（02 運動×勉強会）。時計の音で時間を刻む
  96〜128 ベートーヴェン「運命」（03 作品）
  128〜146 ハ長調のファンファーレで終わり

使い方: python3 tools/make_classic.py          # mv/classic.json を書く
        npx -y jinglescript@1.1.0 render mv/classic.json -o mv/classic.mp3
        （mv/classic.mp3 と mv/classic.timing.json ができる。ピアノの録音は初回にダウンロードされる）
"""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / 'mv' / 'classic.json'

tracks = {}
def track(name, instrument, **kw):
    tracks[name] = {'instrument': instrument, 'name': name, **kw, 'notes': []}

def n(name, at, pitch=None, len=None, vel=0.85, **kw):
    note = {'at': round(at, 4)}
    if pitch is not None:
        note['pitch'] = pitch
    if len is not None:
        note['len'] = len
    note['vel'] = vel
    note.update(kw)
    tracks[name]['notes'].append(note)

def oct2(p):
    """1オクターブ下を重ねる（"G4" → ["G3", "G4"]）"""
    name, o = p[:-1], int(p[-1])
    return [f'{name}{o - 1}', p]

def chord_hit(at, notes, bass, len=1, vel=0.95, timp=None):
    n('melody', at, notes, len, vel)
    n('bass', at, bass, len, vel)
    if timp:
        n('timpani', at, timp, vel=vel)

track('organ', 'organ', gain=-2)
track('melody', 'grandpiano')
track('bass', 'grandpiano', gain=-3)
track('strings', 'strings', gain=-11)
track('timpani', 'timpani', gain=-5, reverb=True)
track('glock', 'glockenspiel', gain=-9)
track('brass', 'trumpet', gain=-10)
track('clock', 'clock', gain=-8, reverb=False)
track('fx', 'impact', gain=-6)

# ---------- 0〜8 トッカータ（ニ短調）：t・o・m・o・c・h・i が1拍ずつ ----------
n('organ', 0, ['A3', 'A4'], .125, .9)
n('organ', .125, ['G3', 'G4'], .125, .9)
n('organ', .25, ['A3', 'A4'], .7, .9)
for i, p in enumerate(['G', 'F', 'E', 'D', 'C#']):
    n('organ', 1 + i, [f'{p}3', f'{p}4'], .85, .9)
n('organ', 6, ['D2', 'D3', 'D4'], 1.1, 1.0)

# ---------- 8〜16 運命（ハ短調）：面白くて、/ できれば / ためになることを、/ みんなで / やる。 ----------
for at in (7.25, 7.5, 7.75):
    n('melody', at, ['G3', 'G4'], .2, .95)
n('melody', 8, ['Eb3', 'Eb4'], 1.2, 1.0); n('bass', 8, ['C2', 'C3'], 1.2, .95); n('timpani', 8, 'C2', vel=1)
for at in (9.25, 9.5, 9.75):
    n('melody', at, ['F3', 'F4'], .2, .95)
n('melody', 10, ['D3', 'D4'], 1.2, 1.0); n('bass', 10, ['G1', 'G2'], 1.2, .95); n('timpani', 10, 'G2', vel=1)
for at in (11.25, 11.5, 11.75):
    n('melody', at, ['G3', 'G4'], .2, .95)
chord_hit(12, ['Ab3', 'C4', 'Eb4', 'Ab4'], ['Ab1', 'Ab2'], 1.5, 1.0, 'C2')
chord_hit(14, ['G3', 'B3', 'D4', 'F4', 'G4'], ['G1', 'G2'], .9, 1.0, 'G2')
chord_hit(15, ['C4', 'Eb4', 'G4', 'C5'], ['C2', 'C3'], .7, 1.0, 'C2')
for i, at in enumerate([x / 4 for x in range(48, 63)]):   # 12〜15.75 ティンパニのロール
    n('timpani', at, 'G2', vel=round(.35 + i * .04, 2))
for at, c, l in [(8, ['C4', 'Eb4', 'G4'], 2), (10, ['B3', 'D4', 'G4'], 2), (12, ['Ab3', 'C4', 'Eb4'], 2), (14, ['G3', 'B3', 'F4'], 1), (15, ['C4', 'Eb4', 'G4'], .75)]:
    n('strings', at, c, l, .8)

# ---------- 16〜48 アイネ・クライネ・ナハトムジーク（ト長調） ----------
def nacht(at):
    """冒頭の4小節（16拍）"""
    m = [(0, 'G4', 1), (1.5, 'D4', .5), (2, 'G4', 1), (3.5, 'D4', .5),
         (4, 'G4', .5), (4.5, 'D4', .5), (5, 'G4', .5), (5.5, 'B4', .5), (6, 'D5', 2),
         (8, 'C5', 1), (9.5, 'A4', .5), (10, 'C5', 1), (11.5, 'A4', .5),
         (12, 'C5', .5), (12.5, 'A4', .5), (13, 'F#4', .5), (13.5, 'A4', .5), (14, 'D4', 2)]
    for o, p, l in m:
        n('melody', at + o, oct2(p), l * .9, .95 if o in (0, 6, 8, 14) else .85)
    for b in range(16):
        root = ['G2', 'G2', 'G2', 'G2', 'G2', 'G2', 'G2', 'G2', 'D2', 'D2', 'D2', 'D2', 'D2', 'D2', 'D2', 'D2'][b]
        n('bass', at + b, [root, root[:-1] + '3'], .45, .8)
        n('bass', at + b + .5, root[:-1] + '3', .4, .6)
    n('strings', at, ['G3', 'B3', 'D4'], 8, .75)
    n('strings', at + 8, ['F#3', 'A3', 'C4', 'D4'], 8, .75)
    for b in (0, 4, 8, 12):
        n('timpani', at + b, 'G2' if b < 8 else 'D2', vel=.9)

nacht(16)
n('fx', 16, vel=1)
n('timpani', 27, 'D2', vel=1)              # 398 が着地
n('melody', 27, ['D3', 'D4', 'F#4', 'A4'], .4, .9)
for i in range(16):                        # 28〜32 家が16分音符で建つ
    n('glock', 28 + i / 4, ['D5', 'E5', 'F#5', 'G5', 'A5', 'B5', 'C#6', 'D6'][i % 8], vel=.8)
# 32〜38 はんこ：8分音符ごとに和音を押す（11回）
stamps = [(['G3', 'B3', 'D4', 'G4'], 'G2')] * 4 + [(['C4', 'E4', 'G4', 'C5'], 'C3')] * 4 + [(['D4', 'F#4', 'A4', 'D5'], 'D3')] * 3
for i, (c, b) in enumerate(stamps):
    at = 32 + i * .5
    n('melody', at, c, .3, .8 + i * .015)
    n('bass', at, [b[:-1] + '2', b], .3, .85)
    n('timpani', at, 'G2' if i < 8 else 'D2', vel=round(.6 + i * .03, 2))
chord_hit(38, ['G3', 'B3', 'D4', 'G4', 'B4'], ['G1', 'G2'], 1.6, 1.0, 'G2')
n('strings', 32, ['G3', 'B3', 'D4'], 4, .8); n('strings', 36, ['D4', 'F#4', 'A4'], 2, .8); n('strings', 38, ['G3', 'B3', 'D4', 'G4'], 2, .85)
# 40〜48 『ホームレス大学院生』：冒頭をもう一度（前半だけ）して、47 からロール
for o, p, l in [(0, 'G4', 1), (1.5, 'D4', .5), (2, 'G4', 1), (3.5, 'D4', .5), (4, 'G4', .5), (4.5, 'D4', .5), (5, 'G4', .5), (5.5, 'B4', .5), (6, 'D5', 1)]:
    n('melody', 40 + o, oct2(p), l * .9, .95)
for b in range(7):
    n('bass', 40 + b, ['G2', 'G3'], .45, .8); n('bass', 40.5 + b, 'G3', .4, .6)
n('strings', 40, ['G3', 'B3', 'D4'], 7, .75)
n('timpani', 40, 'G2', vel=.95); n('timpani', 44, 'G2', vel=.95)
for i in range(4):
    n('timpani', 47 + i / 4, 'G2', vel=round(.6 + i * .1, 2))
n('melody', 47, ['D4', 'F#4', 'A4', 'C5'], .9, .85)

# ---------- 48〜80 歓喜の歌（ハ長調） ----------
n('fx', 48, vel=1)
ode1 = [(0, 'E4', 1), (1, 'E4', 1), (2, 'F4', 1), (3, 'G4', 1), (4, 'G4', 1), (5, 'F4', 1), (6, 'E4', 1), (7, 'D4', 1),
        (8, 'C4', 1), (9, 'C4', 1), (10, 'D4', 1), (11, 'E4', 1), (12, 'E4', 1.5), (13.5, 'D4', .5), (14, 'D4', 2)]
for o, p, l in ode1:
    n('melody', 48 + o, [p, p[:-1] + '5'], l * .92, .95 if o % 4 == 0 else .85)
harm = {48: 'C', 52: 'G', 56: 'C', 60: 'G', 64: 'C', 68: 'G', 72: 'C', 76: 'G'}
CH = {'C': (['C4', 'E4', 'G4'], 'C'), 'G': (['B3', 'D4', 'G4'], 'G')}
for at, h in harm.items():
    c, r = CH[h]
    n('strings', at, c, 4, .75)
    for b in range(4):
        if 68 <= at + b < 72:
            continue
        n('bass', at + b, [r + '2', r + '3'], .45, .8)
        n('bass', at + b + .5, r + '3', .4, .6)
    n('timpani', at, 'C2' if h == 'C' else 'G2', vel=.9)
for i in range(8):                          # 60〜64 1週間のカードが8分音符で落ちる
    if i < 7:
        n('glock', 60 + i / 2, ['E5', 'G5', 'C6', 'E6', 'G6', 'E6', 'C6'][i], vel=.85)
ode2 = [(0, 'E4', 1), (1, 'E4', 1), (2, 'F4', 1), (3, 'G4', 1)]
for o, p, l in ode2:
    n('melody', 64 + o, [p, p[:-1] + '5'], l * .92, .9)
# 68〜72 4つのテーマ：1拍ずつ和音を叩きつける
for i, (c, b) in enumerate([(['G4', 'B4', 'D5', 'G5'], 'G'), (['F4', 'A4', 'D5', 'F5'], 'D'), (['E4', 'G4', 'C5', 'E5'], 'C'), (['D4', 'G4', 'B4', 'D5'], 'G')]):
    chord_hit(68 + i, c, [b + '1', b + '2'], .8, 1.0, 'G2' if b != 'C' else 'C2')
for o, p, l in [(0, 'C4', 1), (1, 'C4', 1), (2, 'D4', 1), (3, 'E4', 1), (4, 'D4', 1.5), (5.5, 'C4', .5), (6, 'C4', 2)]:
    n('melody', 72 + o, [p, p[:-1] + '5'], l * .92, .9)
n('timpani', 76, 'G2', vel=.95); n('timpani', 77, 'G2', vel=.9); n('timpani', 78, 'C2', vel=1)
n('melody', 77, ['G3', 'B3', 'D4'], .4, .8); n('melody', 78, ['C3', 'E3', 'G3', 'C4'], 1.2, .95)
for i in range(4):
    n('timpani', 79 + i / 4, 'D2', vel=round(.55 + i * .12, 2))

# ---------- 80〜96 カノン（ニ長調）の低音。84〜92 は時計の音 ----------
n('fx', 80, vel=.8, variant='soft')
canon = [('D', ['D4', 'F#4', 'A4']), ('A', ['C#4', 'E4', 'A4']), ('B', ['B3', 'D4', 'F#4']), ('F#', ['A3', 'C#4', 'F#4']),
         ('G', ['B3', 'D4', 'G4']), ('D', ['A3', 'D4', 'F#4']), ('G', ['B3', 'D4', 'G4']), ('A', ['C#4', 'E4', 'A4'])]
for i, (r, c) in enumerate(canon):
    at = 80 + i * 2
    lo = r + ('2' if r in ('D', 'F#', 'G') else '1')
    n('bass', at, [lo, r + ('3' if r in ('D', 'F#', 'G') else '2')], 1.9, .85)
    n('strings', at, c, 2, .7)
    if at < 92:                              # 上は8分音符の分散和音
        for k in range(4):
            n('melody', at + k * .5, [c[0][:-1] + '5', c[1][:-1] + '5', c[2][:-1] + '5', c[1][:-1] + '5'][k], .45, .55)
n('clock', 84, vel=.9, variant=['tick', 'tock'], repeat={'every': 1, 'count': 8})
n('timpani', 80, 'D2', vel=.9); n('timpani', 84, 'A2', vel=.7); n('timpani', 88, 'G2', vel=.7)
# 92〜95 盛り上げ：16分音符のトレモロとティンパニのロール。95〜95.25 は一瞬の無音
for i in range(12):
    at = 92 + i / 4
    n('melody', at, ['A4', 'C#5', 'E5'] if at < 94 else ['A4', 'D5', 'F#5'], .2, round(.45 + i * .04, 2))
for i in range(12):
    n('timpani', 92 + i / 4, 'A2', vel=round(.4 + i * .05, 2))
# 運命の頭（G G G）で 03 に飛び込む
for at in (95.25, 95.5, 95.75):
    n('melody', at, ['G3', 'G4'], .2, 1.0)

# ---------- 96〜128 運命（ハ短調）：8分音符で刻む低音の上に、ダダダダーン ----------
n('fx', 96, vel=1, variant='hard')
bars = {96: ('Cm', ['C4', 'Eb4', 'G4'], 'C'), 100: ('G', ['B3', 'D4', 'G4'], 'G'), 104: ('Cm', ['C4', 'Eb4', 'G4'], 'C'), 108: ('G', ['B3', 'D4', 'F4'], 'G'),
        112: ('Ab', ['Ab3', 'C4', 'Eb4'], 'Ab'), 116: ('Fm', ['Ab3', 'C4', 'F4'], 'F'), 120: ('Fm', ['Ab3', 'C4', 'F4'], 'F'), 124: ('G', ['B3', 'D4', 'G4'], 'G')}
for at, (_, c, r) in bars.items():
    n('strings', at, c, 4, .8)
    lo = r + ('1' if r in ('Ab', 'G') else '2')
    for k in range(8):
        if 112 <= at + k / 2 < 116 or at + k / 2 >= 124:
            continue
        n('bass', at + k / 2, [lo, r + ('2' if r in ('Ab', 'G') else '3')], .4, .85 if k % 2 == 0 else .65)
    n('timpani', at, 'C2' if r in ('C', 'Ab', 'F') else 'G2', vel=.95)
for at, low, hi in [(96, 'Eb4', None), (100, 'D4', ('F4',)), (104, 'Eb4', ('G4',)), (108, 'D4', ('F4',))]:
    pick = 'G4' if low == 'Eb4' else 'F4'
    if at > 96:
        for p in (at - .75, at - .5, at - .25):
            n('melody', p, oct2(pick), .2, .95)
    n('melody', at, oct2(low), 2.5, 1.0)
    n('brass', at, low[:-1] + '4', 2, .9)
# 112〜116 小さな作品4つ：1拍ずつ和音
for i, (c, b) in enumerate([(['Ab3', 'C4', 'Eb4', 'Ab4'], 'Ab'), (['Bb3', 'D4', 'F4', 'Bb4'], 'Bb'), (['C4', 'Eb4', 'G4', 'C5'], 'C'), (['B3', 'D4', 'G4', 'B4'], 'G')]):
    chord_hit(112 + i, c, [b + '1', b + '2'], .8, 1.0, 'C2' if b in ('Ab', 'C') else 'G2')
for i, p in enumerate(['C5', 'D5', 'Eb5', 'F5', 'G5', 'Ab5', 'B5', 'C6']):   # 116〜120 駆け上がり
    n('melody', 116 + i / 2, oct2(p), .4, round(.7 + i * .03, 2))
chord_hit(120, ['F3', 'Ab3', 'C4', 'F4'], ['F1', 'F2'], 1.6, 1.0, 'C2')
chord_hit(122, ['G3', 'B3', 'D4', 'G4'], ['G1', 'G2'], 1.6, 1.0, 'G2')
# 124〜128 写真が8分音符で切り替わる：和音も8分音符で
for i in range(8):
    c = ['C4', 'Eb4', 'G4', 'C5'] if i % 2 == 0 else ['B3', 'D4', 'G4', 'B4']
    chord_hit(124 + i / 2, c, ['C2', 'C3'] if i % 2 == 0 else ['G1', 'G2'], .35, round(.75 + i * .03, 2), 'C2' if i % 2 == 0 else 'G2')

# ---------- 128〜146 ハ長調のファンファーレで終わり ----------
n('fx', 128, vel=.9)
chord_hit(128, ['C4', 'E4', 'G4', 'C5'], ['C2', 'C3'], 1.2, 1.0, 'C2')
for at, p in [(128.5, 'E5'), (129, 'G5'), (130, 'C6')]:
    n('melody', at, oct2(p), .9, .95)
    n('brass', at, p[:-1] + '4' if p != 'C6' else 'C5', .9, .9)
n('strings', 128, ['C4', 'E4', 'G4'], 4, .8)
for b in range(4):
    n('bass', 128 + b, ['C2', 'C3'], .45, .8); n('bass', 128.5 + b, 'C3', .4, .6)
for i, (c, b) in enumerate([(['F4', 'A4', 'C5'], 'F'), (['G4', 'B4', 'D5'], 'G'), (['E4', 'G4', 'C5'], 'E'), (['A4', 'C5', 'E5'], 'A')]):
    chord_hit(132 + i, c, [b + '2', b + '3'], .85, .95, 'C2' if b in ('F', 'A') else 'G2')
    n('strings', 132 + i, c, 1, .8)
for i in range(4):
    n('timpani', 135.5 + i / 8, 'G2', vel=round(.6 + i * .1, 2))
n('fx', 136, vel=1, variant='hard')
chord_hit(136, ['C4', 'E4', 'G4', 'C5', 'E5'], ['C1', 'C2'], 5, 1.0, 'C2')
n('strings', 136, ['C4', 'E4', 'G4', 'C5'], 5, .85)
n('brass', 136, ['C4', 'G4'], 3, .9)
for i, p in enumerate(['C6', 'E6', 'G6', 'C7']):
    n('glock', 136 + i, p, vel=.8)

# 歓喜の歌の後半へ向けて、内声の分散和音で少しずつ温度を上げる。
# 主旋律より下の音域を使い、言葉に合わせた打撃音の場所は空ける。
for at in (48, 52, 56, 64, 72, 76):
    tones = ['C3', 'G3', 'E4', 'G3'] if harm[at] == 'C' else ['G2', 'D3', 'B3', 'D3']
    for k in range(8):
        n('melody', at + k * .5, tones[k % 4], .38, .32 + k * .012)

# カノンは低音から高音へ受け渡し、打楽器を引いて呼吸を作る。
for i, (_, chord) in enumerate(canon[:6]):
    n('glock', 80 + i * 2, chord[2][:-1] + '5', 1.5, .3 + i * .025)

# 拍の位置は固定して映像との同期を保ち、音量と音の切り方にフレーズを作る。
for name, tr in tracks.items():
    for note in tr['notes']:
        at = note['at']
        quiet = 80 <= at < 92
        if name == 'timpani' and quiet:
            note['vel'] *= .5
        if name == 'melody' and 16 <= at < 80:
            note['vel'] *= .9 if at % 4 else 1
        if name == 'strings' and 'len' in note:
            note['len'] = max(.1, note['len'] - .12)
        note['vel'] = round(note['vel'], 3)
    tr['notes'].sort(key=lambda note: note['at'])

score = {
    '$schema': 'https://raw.githubusercontent.com/receptron/jinglescript/main/schema/jinglescript-1.json',
    'format': 'jinglescript/1',
    'title': 'tomochi MV（クラシック版）',
    'tempo': 128,
    'length': {'beats': 146},
    'instruments': {
        'timpani': {'blocks': [
            {'modes': [{'ratio': 1, 'level': 1, 'decay': 1.6}, {'ratio': 1.5, 'level': .55, 'decay': 1.1},
                       {'ratio': 1.98, 'level': .35, 'decay': .8}, {'ratio': 2.44, 'level': .2, 'decay': .5}]},
            {'noise': 'white', 'burst': .01, 'level': .25},
            {'filter': 'lowpass', 'cutoff': 1800}]},
        'strings': {'blocks': [
            {'osc': 'saw', 'detune': -8}, {'osc': 'saw', 'detune': 8}, {'osc': 'saw', 'ratio': .5, 'level': .4},
            {'filter': 'lowpass', 'cutoff': 2600},
            {'env': {'attack': .12, 'decay': .4, 'sustain': .75, 'release': .5}},
            {'lfo': 'vibrato', 'rate': 5.2, 'depth': 10, 'delay': .25}]},
    },
    'tracks': list(tracks.values()),
}
OUT.write_text(json.dumps(score, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
print(f'{OUT.relative_to(OUT.parent.parent)}: {sum(len(t["notes"]) for t in tracks.values())} notes')
