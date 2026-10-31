"""MV版のクラシック版の曲を、JingleScript の楽譜（JSON）として書き出す（mv/classic.json）。

クラシックの名曲の冒頭を、ジャズ風（スウィング）にアレンジしたもの。
映像はEDM版と同じ拍の表で動くので、テンポ 128・全146拍の組み立ては変えず、
言葉が出る拍・家やはんこが並ぶ拍・ボールが弾ける4拍ごとの区切りに、同じように音を置く。
裏拍の8分音符は、拍の 2/3 の位置まで遅らせて跳ねさせる（スウィング）。映像のほうも同じだけ遅らせる。
  0〜8   バッハ「トッカータとフーガ ニ短調」の出だし（ジャズオルガン）：1拍に1文字
  8〜16  ベートーヴェン「運命」の「ダダダダーン」を3連符の食い込みで
  16〜48 モーツァルト「アイネ・クライネ・ナハトムジーク」をミディアムスウィングで（ウッドベースが4分音符で歩く）
  48〜80 ベートーヴェン「歓喜の歌」
  80〜96 パッヘルベル「カノン」をバラードで（ブラシと時計の音）
  96〜128 ベートーヴェン「運命」をアップテンポで
  128〜146 ハ長調で締める

気持ちよく響かせるための決まり（ジャズの編曲で一般に言われていること）を、書き出す前に機械で確かめる（check()）：
  - 旋律の拍の頭の音・長い音は、その和音の音か、ぶつからない飾りの音（9度・13度など）にする。
    長調の和音の上の4度、属七の上の11度、短調の和音の上の短6度（いわゆるアヴォイド・ノート）は置かない。
  - 旋律と伴奏の間に、半音（短2度）や短9度のぶつかりを作らない。いちばん耳に障る響き。
  - 旋律が和音の根音のときは、長7度の和音ではなく6度の和音にする。
  - 低い音域では、伴奏の音どうしを近づけすぎない（低音の限界。濁って聞こえる）。
  - 旋律は伴奏より上に置く（伴奏のいちばん上の音より高く）。
  - 和音は、変化した属七（オルタード）を使わず、6・maj7・m7・7・9 のすなおな響きにする。

楽器：ジャズオルガン（イントロ）、ピアノ（旋律と伴奏）、ビブラフォン、ウッドベース、
      ライドシンバル・ハイハット・ブラシ・バスドラム・クラッシュ（どれも JingleScript の部品で作った音）、トランペット、時計。

使い方: python3 tools/make_classic.py          # 響きを確かめてから mv/classic.json を書く
        npx -y jinglescript@1.1.0 render mv/classic.json -o mv/classic.mp3
        （mv/classic.mp3 と mv/classic.timing.json ができる。ピアノの録音は初回にダウンロードされる）
"""
import json
import sys
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

NOTE_NUM = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11}
NAMES = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']
def nm(num):
    return f'{NAMES[num % 12]}{num // 12 - 1}'
def num(pitch):
    return NOTE_NUM[pitch[:-1]] + 12 * (int(pitch[-1]) + 1)

def up(p):
    """旋律は1オクターブ上を重ねて、伴奏より上で鳴らす（"G4" → ["G4", "G5"]）"""
    return [p, nm(num(p) + 12)]

# すなおなジャズの和音：伴奏の形（伴奏のいちばん上は D4〜E4 まで）と、根音・和音の種類
CH = {
    'C6': (['E3', 'A3', 'D4'], 'C', '6'), 'Cmaj7': (['E3', 'G3', 'B3'], 'C', 'maj'), 'C': (['E3', 'G3', 'C4'], 'C', '6'),
    'Cm7': (['G3', 'Bb3', 'Eb4'], 'C', 'm'), 'Dm7': (['F3', 'A3', 'C4'], 'D', 'm'), 'Em7': (['G3', 'B3', 'D4'], 'E', 'm'),
    'F6': (['D3', 'A3', 'C4'], 'F', '6'), 'Fmaj7': (['E3', 'A3', 'C4'], 'F', 'maj'), 'Fm7': (['Ab3', 'C4', 'Eb4'], 'F', 'm'),
    'G7': (['F3', 'B3', 'D4'], 'G', '7'), 'G9': (['F3', 'A3', 'B3'], 'G', '7'), 'G6': (['E3', 'G3', 'B3'], 'G', '6'),
    'Gmaj7': (['F#3', 'B3', 'D4'], 'G', 'maj'), 'Am7': (['G3', 'C4', 'E4'], 'A', 'm'), 'A7': (['G3', 'C#4', 'E4'], 'A', '7'),
    'D7': (['F#3', 'C4', 'E4'], 'D', '7'), 'D9': (['F#3', 'C4', 'E4'], 'D', '7'), 'Ab6': (['F3', 'C4', 'Eb4'], 'Ab', '6'),
    'Abmaj7': (['G3', 'C4', 'Eb4'], 'Ab', 'maj'), 'Bb7': (['Ab3', 'D4', 'F4'], 'Bb', '7'),
    'Dmaj7': (['F#3', 'A3', 'C#4'], 'D', 'maj'), 'A6': (['F#3', 'C#4', 'E4'], 'A', '6'), 'Bm7': (['F#3', 'A3', 'D4'], 'B', 'm'),
    'F#m7': (['E3', 'A3', 'C#4'], 'F#', 'm'), 'D6': (['F#3', 'B3', 'D4'], 'D', '6'),
}
# 旋律が和音の上で置いてよい音（根音からの半音の数）。アヴォイド・ノートは入れない
SAFE = {'maj': {0, 2, 4, 7, 9, 11}, '6': {0, 2, 4, 7, 9}, 'm': {0, 2, 3, 5, 7, 10}, '7': {0, 2, 4, 7, 9, 10}}
HARM = []   # [始まりの拍, 終わりの拍, 和音]。check() で旋律と照らし合わせる

def chord(at, until, ch):
    HARM.append((at, until, ch))

def bass_lo(ch):
    root = 36 + NOTE_NUM[CH[ch][1]]
    return root if root <= 43 else root - 12   # E2〜G2 あたりを中心に

def walk(at, chords, then=None):
    """ウッドベースの4分音符：根音 → 3度 → 5度 → 次の和音の5度（次の根音へ自然に戻る）。then は、続く和音"""
    for i, ch in enumerate(chords):
        root = bass_lo(ch)
        third = root + (3 if CH[ch][2] == 'm' else 4)
        nxt = bass_lo(chords[i + 1] if i + 1 < len(chords) else (then or ch))
        approach = nxt + 7 if nxt + 7 <= root + 9 else nxt - 5
        for k, p in enumerate([root, third, root + 7, approach]):
            n('bass', at + i * 4 + k, nm(p), .9, .9 if k == 0 else .76)
        chord(at + i * 4, at + i * 4 + 4, ch)

def comp(at, ch, vel=.55, beats=4):
    """伴奏：チャールストン（1拍目と、2拍目の裏）を、和音が続く間くり返す"""
    for o in range(0, beats, 2):
        n('comp', at + o, CH[ch][0], .55, vel - (.05 if o else 0))
        n('comp', sw(at + o + 1.5), CH[ch][0], .3, vel - .1)

def swing_drums(a, b, ride=.6):
    """ライドの「チン、チキ、チン、チキ」とハイハットの2・4拍"""
    beat = a
    while beat < b - 1e-6:
        n('ride', beat, vel=ride + (.08 if beat % 2 == 1 else 0))
        if beat % 2 == 1:
            n('ride', sw(beat + .5), vel=ride - .15)
            n('hat', beat, vel=.6)
        beat += 1

def hit(at, ch, vel=1.0, crash=True, kick=True, brass=True, len=1, low=True):
    """みんなで合わせる一撃：伴奏の和音・ベースの根音・トランペットは和音のいちばん上の音"""
    notes = CH[ch][0]
    n('comp', at, notes, len, vel)
    lo = bass_lo(ch) - (12 if low else 0)
    n('bass', at, nm(lo if lo >= 24 else lo + 12), len, vel)   # ウッドベースは C1 まで
    if kick:
        n('kick', at, vel=vel)
    if crash:
        n('crash', at, vel=vel * .8)
    if brass:
        n('brass', at, notes[-1], len * .8, vel * .9)
    chord(at, at + len, ch)

def melody(at, p, length, vel=.88, double=True):
    n('melody', at, up(p) if double else p, length, vel)

track('organ', 'organ', gain=-3)
track('melody', 'grandpiano')
track('comp', 'grandpiano', gain=-6)
track('vibes', 'vibraphone', gain=-7)
track('bass', 'upright', gain=-1)
track('brass', 'trumpet', gain=-12)
track('ride', 'ride', gain=-13, reverb=False)
track('hat', 'hat', gain=-15, reverb=False)
track('brush', 'brush', gain=-12, reverb=False)
track('kick', 'kick', gain=-6, reverb=False)
track('crash', 'crash', gain=-14)
track('clock', 'clock', gain=-10, reverb=False)
track('fx', 'impact', gain=-12)

# ---------- 0〜8 トッカータ（ジャズオルガン）：t・o・m・o・c・h・i が1拍ずつ ----------
n('organ', 0, ['A3', 'A4'], .125, .9)
n('organ', .125, ['G3', 'G4'], .125, .9)
n('organ', .25, ['A3', 'A4'], .6, .9)
for i, p in enumerate(['G', 'F', 'E', 'D', 'C#']):
    n('organ', 1 + i, [f'{p}3', f'{p}4'], .7, .88)
n('organ', 6, ['D3', 'A3', 'C4', 'F4', 'A4'], 1, .95)      # Dm7 で着地（低い音は5度で開ける）
n('bass', 6, 'D2', 1, .8)
n('ride', 6, vel=.5)

# ---------- 8〜16 運命を3連符で食い込ませる（ハ短調） ----------
for at, p, hp, ch in [(7, 'G4', 'Eb5', 'Cm7'), (9, 'F4', 'D5', 'G7'), (11, 'G4', 'Ab4', 'Ab6')]:
    for k in range(3):
        n('melody', at + k / 3, up(p), .25, .9)
        n('brush', at + k / 3, vel=.4 + k * .1)
    melody(at + 1, hp, 1.3, 1.0)
    hit(at + 1, ch, 1.0, len=1.3)
hit(14, 'G7', 1.0, len=.9)
n('melody', 14, ['B4', 'D5', 'F5'], .9, .95)
hit(15, 'Cm7', 1.0, len=.7)
n('melody', 15, ['C5', 'Eb5', 'G5'], .7, 1.0)
for i in range(15):                                         # 12〜15.75 ブラシのロール
    n('brush', 12 + i / 4, vel=round(.25 + i * .04, 2))

# ---------- 16〜48 アイネ・クライネ・ナハトムジーク（ト長調・ミディアムスウィング） ----------
NACHT = [(0, 'G4', 1), (1.5, 'D4', .5), (2, 'G4', 1), (3.5, 'D4', .5),
         (4, 'G4', .5), (4.5, 'D4', .5), (5, 'G4', .5), (5.5, 'B4', .5), (6, 'D5', 2),
         (8, 'C5', 1), (9.5, 'A4', .5), (10, 'C5', 1), (11.5, 'A4', .5),
         (12, 'C5', .5), (12.5, 'A4', .5), (13, 'F#4', .5), (13.5, 'A4', .5), (14, 'D4', 2)]
def nacht(at, bars=4):
    for o, p, l in NACHT:
        if o >= bars * 4:
            continue
        melody(sw(at + o), p, l * .85, .9 if o % 4 == 0 else .8)
        n('vibes', sw(at + o), nm(num(p) + 12), l * .85, .45)

n('fx', 16, vel=.8, variant='soft')
hit(16, 'G6', .95, brass=False)
nacht(16)
walk(16, ['G6', 'G6', 'Am7', 'D7'])
comp(16, 'G6'); comp(20, 'G6'); comp(24, 'Am7', beats=2); comp(26, 'D7', beats=2); comp(28, 'D7')
chord(26, 28, 'D7')
swing_drums(16, 32)
n('kick', 24, vel=.8); n('kick', 25, vel=.7)
# 28〜32 家が16分音符で建つ：D7 の分散和音（C は ♮。ここだけ跳ねさせない）
for i in range(16):
    n('vibes', 28 + i / 4, ['D5', 'F#5', 'A5', 'C6'][i % 4], .2, .7)
# 32〜38 はんこ：跳ねた8分音符で11回、全員で合わせる（G → C → D7）
for i, ch in enumerate(['G6'] * 4 + ['Cmaj7'] * 4 + ['D7'] * 3):
    hit(sw(32 + i * .5), ch, round(.72 + i * .02, 2), crash=False, len=.28)
n('crash', 32, vel=.85)
hit(38, 'Gmaj7', 1.0, len=1.4)
n('melody', 38, ['B4', 'D5', 'F#5', 'B5'], 1.4, .95)
n('brush', 39, vel=.5); n('brush', 39 + 1 / 3, vel=.6); n('brush', 39 + 2 / 3, vel=.7)
# 40〜48 「友人の家を、渡り歩いた。」：冒頭の前半をもう一度
nacht(40, 2)
walk(40, ['G6', 'Em7'], then='D7')
comp(40, 'G6'); comp(44, 'Em7')
swing_drums(40, 47)
for k in range(3):                                          # 47 で3連符のフィル（D7）
    n('brush', 47 + k / 3, vel=.6 + k * .12)
    n('kick', 47 + k / 3, vel=.5 + k * .1)
n('melody', 47, ['F#4', 'C5', 'D5'], .8, .85)
n('comp', 47, CH['D7'][0], .8, .6); chord(47, 48, 'D7')

# ---------- 48〜80 歓喜の歌（ハ長調）。旋律は1オクターブ上げて、伴奏から離す ----------
n('fx', 48, vel=.8, variant='soft')
ODE1 = [(0, 'E5', 1), (1, 'E5', 1), (2, 'F5', 1), (3, 'G5', 1), (4, 'G5', 1), (5, 'F5', 1), (6, 'E5', 1), (7, 'D5', 1),
        (8, 'C5', 1), (9, 'C5', 1), (10, 'D5', 1), (11, 'E5', 1), (12, 'E5', 1.5), (13.5, 'D5', .5), (14, 'D5', 2)]
for o, p, l in ODE1:
    n('melody', sw(48 + o), p, l * .9, .92 if o % 4 == 0 else .82)
    n('vibes', sw(48 + o), p, l * .9, .4)
# 和音：E E | F G は C6 → F6、G F E D は G7、C C D E は Am7、E. D D は G7
for at, ch, beats in [(48, 'C6', 2), (50, 'F6', 2), (52, 'G7', 4), (56, 'Am7', 4), (60, 'G7', 4)]:
    comp(at, ch, beats=beats)
    chord(at, at + beats, ch)
walk(52, ['G7', 'Am7', 'G7'])
for at, ch in [(48, 'C6'), (50, 'F6')]:
    n('bass', at, nm(bass_lo(ch)), 1.8, .88); n('bass', at + 1, nm(bass_lo(ch) + 7), .9, .75)
swing_drums(48, 68)
hit(48, 'C6', .95, brass=False)
# 60〜64 1週間のカード：跳ねた8分音符でビブラフォン（G7 の音だけ）
for i, p in enumerate(['D5', 'G5', 'B5', 'D6', 'F6', 'D6', 'B5']):
    n('vibes', sw(60 + i * .5), p, .4, .75)
for o, p in enumerate(['E5', 'E5', 'F5', 'G5']):
    n('melody', 64 + o, p, .9, .88)
comp(64, 'C6', beats=2); comp(66, 'F6', beats=2); chord(64, 66, 'C6'); chord(66, 68, 'F6')
for at, ch in [(64, 'C6'), (66, 'F6')]:
    n('bass', at, nm(bass_lo(ch)), 1.8, .88); n('bass', at + 1, nm(bass_lo(ch) + 7), .9, .75)
# 68〜72 4つのテーマ：G F E D に1拍ずつ和音を合わせる
for i, (ch, top) in enumerate([('G7', ['D5', 'G5']), ('Dm7', ['C5', 'F5']), ('C6', ['C5', 'E5']), ('G7', ['B4', 'D5'])]):
    hit(68 + i, ch, 1.0, len=.8)
    n('melody', 68 + i, top, .8, .95)
swing_drums(72, 76)
for o, p in enumerate(['C5', 'C5', 'D5', 'E5']):
    n('melody', 72 + o, p, .9, .88)
comp(72, 'Am7'); walk(72, ['Am7'])
# 76〜79 「超一流じゃない、／どこにでもいる人／のための人生戦略。」：D.（Dm7）→ G7 → C で着地
hit(76, 'Dm7', .95, len=.9)
n('melody', 76, 'D5', 1.4, .9)
hit(77, 'G7', .95, len=.9)
n('melody', sw(77.5), 'C5', .3, .7)                         # 短い経過音
hit(78, 'C6', 1.0, len=1.2)
n('melody', 78, ['C5', 'E5', 'A5'], 1.2, .95)
for k in range(3):
    n('brush', 79 + k / 3, vel=.55 + k * .12)

# ---------- 80〜96 カノン（ニ長調のバラード）：ブラシと時計の音 ----------
CANON = [('Dmaj7', 'D2'), ('A6', 'C#2'), ('Bm7', 'B1'), ('F#m7', 'F#1'), ('Gmaj7', 'G1'), ('D6', 'F#1'), ('Gmaj7', 'G1'), ('A7', 'A1')]
UPPER = ['F#5', 'E5', 'D5', 'C#5', 'B4', 'A4', 'B4', 'C#5']   # カノンの上の声
n('fx', 80, vel=.6, variant='soft')
for i, (ch, lo) in enumerate(CANON):
    at = 80 + i * 2
    n('bass', at, lo, 1.9, .82)
    n('comp', at, CH[ch][0], 1.8, .5)
    chord(at, at + 2, ch)
    if at < 92:
        n('vibes', at, UPPER[i], 1.8, .65)
        n('brush', at, vel=.35); n('brush', at + 1, vel=.3)
n('clock', 84, vel=.9, variant=['tick', 'tock'], repeat={'every': 1, 'count': 8})
n('kick', 80, vel=.7)
# 92〜95 盛り上げ：3連符のスネアがだんだん強く。旋律は A7 の分散和音
for i in range(9):
    n('brush', 92 + i / 3, vel=round(.4 + i * .05, 2))
    if i % 3 == 0:
        n('kick', 92 + i / 3, vel=round(.3 + i * .05, 2))
for i, p in enumerate(['A4', 'C#5', 'E5', 'G5', 'A5', 'C#6']):
    n('melody', 94 + i / 6, p, .15, .6 + i * .05)
# 運命の頭（G G G、3連符）で 03 に飛び込む
for k in range(3):
    n('melody', 95 + k / 3, up('G4'), .25, 1.0)
    n('brush', 95 + k / 3, vel=.7 + k * .1)

# ---------- 96〜128 運命（ハ短調・アップテンポ） ----------
n('fx', 96, vel=.9, variant='hard')
for at, low, ch in [(96, 'Eb5', 'Cm7'), (100, 'D5', 'G7'), (104, 'Eb5', 'Cm7'), (108, 'D5', 'G7')]:
    if at > 96:
        pick = 'G4' if low == 'Eb5' else 'F4'
        for k in range(3):
            n('melody', at - 1 + k / 3, up(pick), .25, .95)
    melody(at, low, 2.4, 1.0)
    hit(at, ch, 1.0, len=1.4)
walk(96, ['Cm7', 'G7', 'Cm7', 'G7'])
for at, ch in [(96, 'Cm7'), (100, 'G7'), (104, 'Cm7'), (108, 'G7')]:
    n('comp', sw(at + 2.5), CH[ch][0], .3, .55)
swing_drums(96, 112, .65)
# 112〜116 小さな作品4つ：1拍ずつ合わせる
for i, ch in enumerate(['Abmaj7', 'Bb7', 'Cm7', 'G7']):
    hit(112 + i, ch, 1.0, len=.8)
# 116〜120 駆け上がり：G7 の上で、ハ短調の和声的短音階（G から上へ。跳ねた8分音符）
for i, p in enumerate(['G4', 'Ab4', 'B4', 'C5', 'D5', 'Eb5', 'F5', 'G5']):
    n('melody', sw(116 + i * .5), up(p), .4, round(.72 + i * .03, 2))
walk(116, ['G7'])
comp(116, 'G7', beats=2)   # 後半は駆け上がりだけを聞かせる
swing_drums(116, 120, .65)
hit(120, 'Fm7', 1.0, len=1.6)
hit(122, 'G7', 1.0, len=1.6)
# 124〜128 写真が跳ねた8分音符で切り替わる：Cm7 と G7 を交互に
for i in range(8):
    hit(sw(124 + i * .5), 'Cm7' if i % 2 == 0 else 'G7', round(.78 + i * .03, 2), crash=i == 0, len=.3)

# ---------- 128〜146 ハ長調で締める ----------
n('fx', 128, vel=.8, variant='soft')
hit(128, 'C6', 1.0, len=1.2)
for at, p in [(sw(128.5), 'E5'), (129, 'G5'), (130, 'C6')]:
    n('melody', at, p, .9, .95)
    n('vibes', at, p, .9, .7)
walk(128, ['C6'])
comp(128, 'C6')
for i, ch in enumerate(['Fmaj7', 'G7', 'Em7', 'A7']):
    hit(132 + i, ch, .95, crash=False, len=.85, low=False)
swing_drums(128, 132, .62)
for k in range(3):
    n('brush', 135.333 + k * .222, vel=.6 + k * .12)
n('fx', 136, vel=.9, variant='soft')
hit(136, 'C6', 1.0, len=5)
n('melody', 136, ['E4', 'A4', 'D5', 'G5'], 5, 1.0)          # C6/9 の上の声（低い音域は伴奏とベースに任せる）
n('bass', 136, 'C2', 5, .9)
for i, p in enumerate(['C6', 'E6', 'G6', 'C7']):
    n('vibes', 136 + i, p, 2, .75)
for i, p in enumerate(['G5', 'A5', 'C6', 'D6', 'E6', 'G6']):   # 最後にピアノがきらっと上がる（ペンタトニック）
    n('melody', 138 + i / 6, p, .3, .5)


# ---------- 響きの確かめ ----------
def sounding(tr, t):
    for note in tracks[tr]['notes']:
        if 'pitch' not in note:
            continue
        ln = note.get('len', 1.0)
        if note['at'] <= t + 1e-6 < note['at'] + ln:
            for p in ([note['pitch']] if isinstance(note['pitch'], str) else note['pitch']):
                yield num(p)

def harmony_at(t):
    for a, b, ch in reversed(HARM):
        if a <= t + 1e-6 < b:
            return ch
    return None

def check():
    """旋律の拍の頭の音・長い音について、アヴォイド・ノートと半音のぶつかりを数える"""
    problems = []
    for note in tracks['melody']['notes']:
        t, ln = note['at'], note.get('len', 1.0)
        strong = abs(t - round(t)) < 1e-6 or ln >= .8
        if not strong or t < 7:
            continue
        mel = [num(p) for p in ([note['pitch']] if isinstance(note['pitch'], str) else note['pitch'])]
        top = max(mel)
        ch = harmony_at(t)
        if ch:
            root, kind = NOTE_NUM[CH[ch][1]], CH[ch][2]
            for m in mel:
                if (m - root) % 12 not in SAFE[kind]:
                    problems.append(f'{t:6.2f} {nm(m)} は {ch} の上でぶつかる音')
        for tr in ('comp', 'bass', 'vibes', 'brass'):
            for o in sounding(tr, t):
                for m in mel:
                    d = m - o
                    if d % 12 == 1 or (d % 12 == 11 and d < 0):   # 旋律が半音上（短2度・短9度）、または半音下で上に乗られる
                        problems.append(f'{t:6.2f} 旋律 {nm(m)} と {tr} の {nm(o)} が半音でぶつかる')
        comp_top = max(sounding('comp', t), default=0)
        if comp_top and comp_top >= top:
            problems.append(f'{t:6.2f} 伴奏（{nm(comp_top)}）が旋律より高い')
    # 低い音域で近すぎる伴奏
    for ch, (notes, _, _) in CH.items():
        ns = sorted(num(p) for p in notes)
        for a, b in zip(ns, ns[1:]):
            if a < num('E3') and b - a < 5:
                problems.append(f'{ch}: {nm(a)}-{nm(b)} は低い音域で近すぎる')
    return problems


for name in ('melody', 'comp'):
    tracks[name]['pedal'] = [{'at': a, 'until': b} for a, b in [(0, 8), (136, 146)]]
for tr in tracks.values():
    tr['notes'].sort(key=lambda note: note['at'])

problems = check()
if problems:
    print('\n'.join(problems))
    sys.exit(f'響きの問題が {len(problems)} 件あります')

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
print(f'{OUT.relative_to(OUT.parent.parent)}: {sum(len(t["notes"]) for t in tracks.values())} notes、響きの問題 0 件')
