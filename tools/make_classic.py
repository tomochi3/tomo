"""MV版のクラシック版の曲を、JingleScript の楽譜（JSON）として書き出す（mv/classic.json）。

クラシックの名曲の冒頭を、ジャズ風（スウィング）にアレンジしたもの。
映像はEDM版と同じ拍の表で動くので、テンポ 128・全146拍の組み立ては変えず、
言葉が出る拍・家やはんこが並ぶ拍・ボールが弾ける4拍ごとの区切りに、同じように音を置く。
裏拍の8分音符は、拍の 2/3 の位置まで遅らせて跳ねさせる（スウィング）。映像のほうも同じだけ遅らせる。
  0〜8   バッハ「トッカータとフーガ ニ短調」の出だし（ジャズオルガン）：1拍に1文字
  8〜16  ベートーヴェン「運命」の「ダダダダーン」を3連符の食い込みで
  16〜48 モーツァルト「アイネ・クライネ・ナハトムジーク」をミディアムスウィングで（ウッドベースが4分音符で歩く）
  48〜80 ベートーヴェン「歓喜の歌」を、II-V の和音で
  80〜96 パッヘルベル「カノン」をバラードで（ブラシと時計の音）
  96〜128 ベートーヴェン「運命」をアップテンポのシャウトで
  128〜146 ハ長調で締める（C6/9 の和音とビブラフォン）

楽器：ジャズオルガン（イントロ）、ピアノ（旋律と伴奏）、ビブラフォン、ウッドベース、
      ライドシンバル・ハイハット・ブラシ・バスドラム・クラッシュ（どれも JingleScript の部品で作った音）、トランペット、時計。

使い方: python3 tools/make_classic.py          # mv/classic.json を書く
        npx -y jinglescript@1.1.0 render mv/classic.json -o mv/classic.mp3
        （mv/classic.mp3 と mv/classic.timing.json ができる。ピアノの録音は初回にダウンロードされる）
"""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / 'mv' / 'classic.json'
SW = 2 / 3   # 裏拍を置く位置（8分音符の跳ね）


def sw(at):
    """裏拍（x.5）の8分音符を、スウィングの位置（x.667）に動かす"""
    whole = int(at // 1)
    return round(whole + SW, 4) if abs(at - whole - .5) < 1e-6 else at


tracks = {}
def track(name, instrument, **kw):
    tracks[name] = {'instrument': instrument, 'name': name, **kw, 'notes': []}

def n(name, at, pitch=None, len=None, vel=0.85, **kw):
    note = {'at': round(at, 4)}
    if pitch is not None:
        note['pitch'] = pitch
    if len is not None:
        note['len'] = round(len, 3)
    note['vel'] = round(min(1, vel), 3)
    note.update(kw)
    tracks[name]['notes'].append(note)

def oct2(p):
    """1オクターブ下を重ねる（"G4" → ["G3", "G4"]）"""
    name, o = p[:-1], int(p[-1])
    return [f'{name}{o - 1}', p]

# ジャズの和音（左手で弾く、根音を抜いた形）と、ベースの根音
CH = {
    'Cm9': (['Eb3', 'G3', 'Bb3', 'D4'], 'C'), 'Cm6': (['Eb3', 'A3', 'C4', 'D4'], 'C'),
    'G7b9': (['F3', 'Ab3', 'B3', 'D4'], 'G'), 'G7alt': (['F3', 'A#3', 'B3', 'Eb4'], 'G'), 'G13': (['F3', 'B3', 'E4'], 'G'),
    'Abmaj7': (['G3', 'C4', 'Eb4'], 'Ab'), 'Bb13': (['Ab3', 'D4', 'G4'], 'Bb'), 'Fm9': (['Ab3', 'C4', 'Eb4', 'G4'], 'F'),
    'Gmaj7': (['F#3', 'B3', 'D4'], 'G'), 'G6': (['E3', 'B3', 'D4'], 'G'), 'Em9': (['G3', 'B3', 'D4', 'F#4'], 'E'),
    'Am7': (['G3', 'C4', 'E4'], 'A'), 'A7': (['G3', 'C#4', 'E4'], 'A'), 'D7': (['F#3', 'C4', 'E4'], 'D'), 'D7#9': (['F#3', 'C4', 'F4'], 'D'),
    'C6': (['E3', 'A3', 'D4'], 'C'), 'C9': (['E3', 'Bb3', 'D4'], 'C'), 'Cmaj7': (['E3', 'G3', 'B3', 'D4'], 'C'),
    'Dm9': (['F3', 'A3', 'C4', 'E4'], 'D'), 'Em7': (['G3', 'B3', 'D4'], 'E'), 'A7#9': (['G3', 'C#4', 'F4'], 'A'),
    'Fmaj7': (['E3', 'A3', 'C4'], 'F'), 'C69': (['E3', 'A3', 'D4', 'G4'], 'C'),
    'Dmaj9': (['F#3', 'A3', 'C#4', 'E4'], 'D'), 'A6': (['F#3', 'C#4', 'E4'], 'A'), 'Bm9': (['D3', 'F#3', 'A3', 'C#4'], 'B'),
    'F#m7': (['E3', 'A3', 'C#4'], 'F#'), 'Gmaj9': (['F#3', 'A3', 'B3', 'D4'], 'G'), 'A13': (['G3', 'C#4', 'F#4'], 'A'),
}
NOTE_NUM = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11}
NAMES = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']
def nm(num):
    return f'{NAMES[num % 12]}{num // 12 - 1}'
def num(pitch):
    return NOTE_NUM[pitch[:-1]] + 12 * (int(pitch[-1]) + 1)

def walk(at, chords):
    """ウッドベースの4分音符：根音 → 3度か5度 → 5度 → 次の根音へ半音で寄る"""
    for i, ch in enumerate(chords):
        root = 36 + NOTE_NUM[CH[ch][1]]
        if root > 45:
            root -= 12
        nxt = chords[i + 1] if i + 1 < len(chords) else ch
        target = 36 + NOTE_NUM[CH[nxt][1]]
        if target > 45:
            target -= 12
        line = [root, root + (3 if 'm' in ch.replace('maj', '') else 4), root + 7, target + (1 if target < root + 7 else -1)]
        for k, p in enumerate(line):
            n('bass', at + i * 4 + k, nm(p), .9, .9 if k == 0 else .78)

def comp(at, ch, vel=.55):
    """伴奏：チャールストン（1拍目と、2拍目の裏）"""
    n('comp', at, CH[ch][0], .55, vel)
    n('comp', sw(at + 1.5), CH[ch][0], .3, vel - .08)

def swing_drums(a, b, ride=.6):
    """ライドの「チン、チキ、チン、チキ」とハイハットの2・4拍"""
    beat = a
    while beat < b - 1e-6:
        n('ride', beat, vel=ride + (.08 if beat % 2 == 1 else 0))
        if beat % 2 == 1:
            n('ride', sw(beat + .5), vel=ride - .15)
            n('hat', beat, vel=.6)
        beat += 1

def hit(at, ch, bass_oct=2, vel=1.0, crash=True, kick=True, brass=None, len=1):
    """みんなで合わせる一撃（シャウト）"""
    notes, root = CH[ch]
    n('comp', at, notes, len, vel)
    lo = 36 + NOTE_NUM[root] - (12 if bass_oct == 1 else 0)
    n('bass', at, nm(lo), len, vel)
    if kick:
        n('kick', at, vel=vel)
    if crash:
        n('crash', at, vel=vel * .8)
    if brass:
        n('brass', at, brass, len * .8, vel * .9)

track('organ', 'organ', gain=-3)
track('melody', 'grandpiano')
track('comp', 'grandpiano', gain=-5)
track('vibes', 'vibraphone', gain=-6)
track('bass', 'upright', gain=-1)
track('brass', 'trumpet', gain=-11)
track('ride', 'ride', gain=-13, reverb=False)
track('hat', 'hat', gain=-15, reverb=False)
track('brush', 'brush', gain=-12, reverb=False)
track('kick', 'kick', gain=-6, reverb=False)
track('crash', 'crash', gain=-13)
track('clock', 'clock', gain=-10, reverb=False)
track('fx', 'impact', gain=-12)

# ---------- 0〜8 トッカータ（ジャズオルガン）：t・o・m・o・c・h・i が1拍ずつ ----------
n('organ', 0, ['A3', 'A4'], .125, .9)
n('organ', .125, ['G3', 'G4'], .125, .9)
n('organ', .25, ['A3', 'A4'], .6, .9)
for i, p in enumerate(['G', 'F', 'E', 'D', 'C#']):
    n('organ', 1 + i, [f'{p}3', f'{p}4'], .7, .88)
n('organ', 6, ['D3', 'F3', 'A3', 'C4', 'E4'], 1, .95)      # Dm9 でふわっと着地
n('bass', 6, 'D2', 1, .8)
n('ride', 6, vel=.5)

# ---------- 8〜16 運命を3連符で食い込ませる ----------
for at, p, hp, ch, drum in [(7, 'G4', 'Eb4', 'Cm9', 'C'), (9, 'F4', 'D4', 'G7b9', 'G'), (11, 'G4', 'Ab4', 'Abmaj7', 'Ab')]:
    for k in range(3):
        n('melody', at + k / 3, oct2(p), .25, .9)
        n('brush', at + k / 3, vel=.4 + k * .1)
    n('melody', at + 1, oct2(hp), 1.3, 1.0)
    hit(at + 1, ch, 1, 1.0, brass=hp)
hit(14, 'G7alt', 1, 1.0, brass=['B3', 'F4'], len=.9)
n('melody', 14, ['F4', 'B4', 'Eb5'], .9, .95)
hit(15, 'Cm6', 1, 1.0, brass=['C4', 'G4'], len=.7)
n('melody', 15, ['C5', 'Eb5', 'G5'], .7, 1.0)
for i in range(15):                                         # 12〜15.75 ブラシのロール
    n('brush', 12 + i / 4, vel=round(.25 + i * .04, 2))

# ---------- 16〜48 アイネ・クライネ・ナハトムジーク（ミディアムスウィング） ----------
def nacht(at, bars=4):
    m = [(0, 'G4', 1), (1.5, 'D4', .5), (2, 'G4', 1), (3.5, 'D4', .5),
         (4, 'G4', .5), (4.5, 'D4', .5), (5, 'G4', .5), (5.5, 'B4', .5), (6, 'D5', 2),
         (8, 'C5', 1), (9.5, 'A4', .5), (10, 'C5', 1), (11.5, 'A4', .5),
         (12, 'C5', .5), (12.5, 'A4', .5), (13, 'F#4', .5), (13.5, 'A4', .5), (14, 'D4', 2)]
    for o, p, l in m:
        if o >= bars * 4:
            continue
        n('melody', sw(at + o), oct2(p), l * .85, .92 if o % 4 == 0 else .8)
        n('vibes', sw(at + o), p, l * .85, .55)
    # 7拍目の長い音の間に、ピアノの小さな合いの手（ブルーノートの B♭ → B）
    n('melody', sw(at + 7.5), ['Bb4'], .2, .6)

n('fx', 16, vel=.8, variant='soft')
hit(16, 'Gmaj7', 1, .95)
nacht(16)
walk(16, ['Gmaj7', 'G6', 'Am7', 'D7'])
for at, ch in [(16, 'Gmaj7'), (20, 'G6'), (24, 'Am7'), (28, 'D7')]:
    comp(at, ch)
    comp(at + 2, ch, .5)
swing_drums(16, 32)
# 24「ひとつの家に、」と 25「住まない暮らし。」に軽いアクセント
n('kick', 24, vel=.8); n('kick', 25, vel=.7)
# 28〜32 家が16分音符で建つ：ビブラフォンの駆け上がり（ここだけ跳ねさせない）
for i in range(16):
    n('vibes', 28 + i / 4, ['D5', 'E5', 'F#5', 'G5', 'A5', 'B5', 'C#6', 'D6'][i % 8], .2, .7)
# 32〜38 はんこ：跳ねた8分音符で11回、全員で合わせる
stamps = ['G6'] * 4 + ['C9'] * 4 + ['D7#9'] * 3
for i, ch in enumerate(stamps):
    at = sw(32 + i * .5)
    hit(at, ch, 2, round(.72 + i * .02, 2), crash=False, kick=True, brass=CH[ch][0][-1], len=.28)
n('crash', 32, vel=.85)
hit(38, 'Gmaj7', 1, 1.0, brass=['B3', 'F#4'], len=1.4)
n('melody', 38, ['B4', 'D5', 'F#5', 'B5'], 1.4, .95)
n('brush', 39, vel=.5); n('brush', 39 + 1 / 3, vel=.6); n('brush', 39 + 2 / 3, vel=.7)
# 40〜48 「友人の家を、渡り歩いた。」：冒頭の前半をもう一度、ベースはそのまま歩く
nacht(40, 2)
walk(40, ['Gmaj7', 'Em9'])
comp(40, 'Gmaj7'); comp(44, 'Em9')
swing_drums(40, 47)
for k in range(3):                                          # 47 で3連符のフィル
    n('brush', 47 + k / 3, vel=.6 + k * .12)
    n('kick', 47 + k / 3, vel=.5 + k * .1)
n('melody', 47, ['D4', 'F#4', 'C5'], .8, .85)

# ---------- 48〜80 歓喜の歌（II-V の和音で） ----------
n('fx', 48, vel=.8, variant='soft')
ode = [(0, 'E4', 1), (1, 'E4', 1), (2, 'F4', 1), (3, 'G4', 1), (4, 'G4', 1), (5, 'F4', 1), (6, 'E4', 1), (7, 'D4', 1),
       (8, 'C4', 1), (9, 'C4', 1), (10, 'D4', 1), (11, 'E4', 1), (12, 'E4', 1.5), (13.5, 'D4', .5), (14, 'D4', 2)]
for o, p, l in ode:
    n('melody', sw(48 + o), [p, p[:-1] + '5'], l * .9, .92 if o % 4 == 0 else .82)
harm = [(48, ['Cmaj7']), (52, ['Dm9', 'G13']), (56, ['Em7', 'A7']), (60, ['Dm9', 'G13']), (64, ['Cmaj7']), (72, ['Dm9', 'G13'])]
for at, chs in harm:
    walk_chords = chs if len(chs) == 1 else chs
    if len(chs) == 1:
        walk(at, chs)
        comp(at, chs[0]); comp(at + 2, chs[0], .5)
    else:
        for k, ch in enumerate(chs):
            root = 36 + NOTE_NUM[CH[ch][1]]
            n('bass', at + k * 2, nm(root if root <= 45 else root - 12), 1.8, .88)
            n('bass', at + k * 2 + 1, nm((root if root <= 45 else root - 12) + 7), .9, .75)
            comp(at + k * 2, ch)
swing_drums(48, 68)
hit(48, 'Cmaj7', 1, .95, crash=True)
# 60〜64 1週間のカード：跳ねた8分音符でビブラフォン
for i, p in enumerate(['E5', 'G5', 'C6', 'E6', 'G6', 'E6', 'C6']):
    n('vibes', sw(60 + i * .5), p, .4, .8)
for o, p, l in [(0, 'E4', 1), (1, 'E4', 1), (2, 'F4', 1), (3, 'G4', 1)]:
    n('melody', 64 + o, [p, p[:-1] + '5'], l * .9, .88)
# 68〜72 4つのテーマ：1拍ずつ和音を合わせる
for i, ch in enumerate(['Dm9', 'G13', 'Em7', 'A7#9']):
    hit(68 + i, ch, 1, 1.0, brass=CH[ch][0][-1], len=.8)
    n('melody', 68 + i, [['A4', 'D5'], ['B4', 'E5'], ['B4', 'G5'], ['C#5', 'G5']][i], .8, .95)
swing_drums(72, 76)
for o, p, l in [(0, 'C4', 1), (1, 'C4', 1), (2, 'D4', 1), (3, 'E4', 1)]:
    n('melody', 72 + o, [p, p[:-1] + '5'], l * .9, .88)
# 76〜79 「超一流じゃない、／どこにでもいる人／のための人生戦略。」に3つの和音
hit(76, 'Dm9', 1, .95, brass='C4', len=.9)
hit(77, 'G13', 1, .95, brass='B3', len=.9)
hit(78, 'C69', 1, 1.0, brass=['E4', 'G4'], len=1.2)
n('melody', 78, ['E5', 'G5', 'A5', 'D6'], 1.2, .95)
for k in range(3):
    n('brush', 79 + k / 3, vel=.55 + k * .12)

# ---------- 80〜96 カノン（バラード）：ブラシと時計の音 ----------
canon = [('Dmaj9', 'D2'), ('A6', 'C#2'), ('Bm9', 'B1'), ('F#m7', 'F#1'), ('Gmaj9', 'G1'), ('Dmaj9', 'F#1'), ('Gmaj9', 'G1'), ('A13', 'A1')]
upper = ['F#5', 'E5', 'D5', 'C#5', 'B4', 'A4', 'B4', 'C#5']   # カノンの上の声
n('fx', 80, vel=.6, variant='soft')
for i, (ch, lo) in enumerate(canon):
    at = 80 + i * 2
    n('bass', at, lo, 1.9, .82)
    n('comp', at, CH[ch][0], 1.8, .5)
    if at < 92:
        n('vibes', at, upper[i], 1.8, .65)
        n('brush', at, vel=.35); n('brush', at + 1, vel=.3)
n('clock', 84, vel=.9, variant=['tick', 'tock'], repeat={'every': 1, 'count': 8})
n('kick', 80, vel=.7)
# 92〜95 盛り上げ：3連符のスネアがだんだん強く。95〜95 は一瞬ためる
for i in range(9):
    n('brush', 92 + i / 3, vel=round(.4 + i * .05, 2))
    n('kick', 92 + i / 3, vel=round(.3 + i * .05, 2)) if i % 3 == 0 else None
for i in range(6):
    n('melody', 94 + i / 6, ['A4', 'C#5', 'E5', 'G5', 'B5', 'C#6'][i], .15, .6 + i * .05)
# 運命の頭（G G G、3連符）で 03 に飛び込む
for k in range(3):
    n('melody', 95 + k / 3, ['G3', 'G4'], .25, 1.0)
    n('brush', 95 + k / 3, vel=.7 + k * .1)

# ---------- 96〜128 運命（アップテンポのシャウト） ----------
n('fx', 96, vel=.9, variant='hard')
fate = [(96, 'Eb4', 'Cm9'), (100, 'D4', 'G7b9'), (104, 'Eb4', 'Cm9'), (108, 'D4', 'G7alt')]
for at, low, ch in fate:
    if at > 96:
        pick = 'G4' if low == 'Eb4' else 'F4'
        for k in range(3):
            n('melody', at - 1 + k / 3, oct2(pick), .25, .95)
            n('brass', at - 1 + k / 3, pick, .25, .8)
    n('melody', at, oct2(low), 2.4, 1.0)
    hit(at, ch, 1, 1.0, brass=low, len=1.4)
walk(96, ['Cm9', 'G7b9', 'Cm9', 'G7alt'])
for at, ch in [(96, 'Cm9'), (100, 'G7b9'), (104, 'Cm9'), (108, 'G7alt')]:
    n('comp', sw(at + 2.5), CH[ch][0], .3, .55)
swing_drums(96, 112, .65)
# 112〜116 小さな作品4つ：1拍ずつ合わせる
for i, ch in enumerate(['Abmaj7', 'Bb13', 'Cm9', 'G7alt']):
    hit(112 + i, ch, 1, 1.0, brass=CH[ch][0][-1], len=.8)
# 116〜120 ビバップの駆け上がり（跳ねた8分音符）
for i, p in enumerate(['C5', 'D5', 'Eb5', 'F5', 'G5', 'Ab5', 'A5', 'B5']):
    n('melody', sw(116 + i * .5), oct2(p), .4, round(.72 + i * .03, 2))
walk(116, ['Fm9'])
swing_drums(116, 120, .65)
hit(120, 'Fm9', 1, 1.0, brass=['Ab3', 'Eb4'], len=1.6)
hit(122, 'G7alt', 1, 1.0, brass=['B3', 'F4'], len=1.6)
# 124〜128 写真が跳ねた8分音符で切り替わる：シャウトも同じ位置で
for i in range(8):
    ch = 'Cm9' if i % 2 == 0 else 'G7alt'
    hit(sw(124 + i * .5), ch, 1, round(.78 + i * .03, 2), crash=i == 0, brass=CH[ch][0][-1], len=.3)

# ---------- 128〜146 ハ長調で締める ----------
n('fx', 128, vel=.8, variant='soft')
hit(128, 'C69', 1, 1.0, brass=['E4', 'G4'], len=1.2)
for at, p in [(sw(128.5), 'E5'), (129, 'G5'), (130, 'C6')]:
    n('melody', at, oct2(p), .9, .95)
    n('vibes', at, p, .9, .7)
walk(128, ['C69'])
comp(128, 'C69')
swing_drums(128, 132, .62)
for i, ch in enumerate(['Fmaj7', 'G13', 'Em7', 'A7']):
    hit(132 + i, ch, 2, .95, crash=False, brass=CH[ch][0][-1], len=.85)
for k in range(3):
    n('brush', 135.333 + k * .222, vel=.6 + k * .12)
n('fx', 136, vel=.9, variant='soft')
hit(136, 'C69', 1, 1.0, brass=['C4', 'G4'], len=5)
n('melody', 136, ['C4', 'E4', 'A4', 'D5', 'G5'], 5, 1.0)
n('bass', 136, 'C1', 5, .9)
for i, p in enumerate(['C6', 'E6', 'G6', 'C7']):
    n('vibes', 136 + i, p, 2, .75)
for i, p in enumerate(['G5', 'A5', 'C6', 'D6', 'E6', 'G6']):   # 最後にピアノがきらっと上がる
    n('melody', 138 + i / 6, p, .3, .5)

# ピアノの音は、鳴らしたあと長く残す（和音が変わるところでペダルを踏みかえる）
for name in ('melody', 'comp'):
    tracks[name]['pedal'] = [{'at': a, 'until': b} for a, b in [(0, 8), (8, 16), (136, 146)]]
for tr in tracks.values():
    tr['notes'].sort(key=lambda note: note['at'])

score = {
    '$schema': 'https://raw.githubusercontent.com/receptron/jinglescript/main/schema/jinglescript-1.json',
    'format': 'jinglescript/1',
    'title': 'tomochi MV（クラシックをジャズで）',
    'tempo': 128,
    'length': {'beats': 146},
    'instruments': {
        # ウッドベース：指で弾いた低い弦
        'upright': {'description': 'Upright jazz bass, finger-plucked', 'blocks': [
            {'string': {'pluck': 380, 'position': .22, 'damping': .82, 'ring': 1.2, 'body': 1100}},
            {'osc': 'sine', 'level': .35, 'env': {'attack': .004, 'decay': .9}}]},
        # ライドシンバル：金属の澄んだ「チン」
        'ride': {'kind': 'sfx', 'pitch': 'F6', 'description': 'Jazz ride cymbal ping', 'blocks': [
            {'modes': [{'ratio': 1, 'level': .5, 'decay': 1.4}, {'ratio': 1.47, 'level': .4, 'decay': 1.1}, {'ratio': 2.09, 'level': .35, 'decay': .9},
                       {'ratio': 2.56, 'level': .3, 'decay': .8}, {'ratio': 3.2, 'level': .25, 'decay': .6}, {'ratio': 4.1, 'level': .2, 'decay': .5}]},
            {'noise': 'white', 'level': .5, 'decay': .5, 'filter': {'type': 'highpass', 'cutoff': 6000}}]},
        'hat': {'kind': 'sfx', 'description': 'Closed hi-hat chick', 'blocks': [
            {'noise': 'white', 'level': 1, 'decay': .05, 'filter': {'type': 'highpass', 'cutoff': 7000}}]},
        'brush': {'kind': 'sfx', 'description': 'Brush on a snare', 'blocks': [
            {'noise': 'pink', 'level': 1, 'decay': .16, 'filter': {'type': 'bandpass', 'cutoff': 2600, 'q': .8}}]},
        'kick': {'kind': 'sfx', 'pitch': 'C2', 'description': 'Soft jazz kick drum', 'blocks': [
            {'osc': 'sine'}, {'pitchEnv': {'from': 12, 'to': 0, 'time': .07}}, {'env': {'attack': .002, 'decay': .35}}]},
        'crash': {'kind': 'sfx', 'description': 'Washy crash cymbal', 'blocks': [
            {'noise': 'white', 'level': 1, 'decay': 1.8, 'filter': {'type': 'highpass', 'cutoff': 4500}}]},
    },
    'tracks': list(tracks.values()),
}
OUT.write_text(json.dumps(score, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
print(f'{OUT.relative_to(OUT.parent.parent)}: {sum(len(t["notes"]) for t in tracks.values())} notes')
