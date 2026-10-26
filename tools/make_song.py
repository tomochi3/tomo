"""リッチ版で生き物たちが歌う1節を、ずんだもんの声で作る（rich/audio/ に書き出す）。

パートごとに別のファイルにし、ページ側で並んだ仲間の数に応じて重ねる。
  song-melody.mp3  主旋律（リーダー）           … いつも
  song-harmony.mp3 ハモり（主旋律の3度下）      … いつも
  song-bass.mp3    低音（和音の根音を「ぼん」） … 仲間4匹から
  song-perc.mp3    ボイパ（キック・ハイハット・スネア） … 仲間6匹から
  song-top.mp3     上ハモり（主旋律の3度上）    … 仲間10匹から

メロディと歌詞はオリジナル。ハ長調、テンポ 140、8分音符 = 20 フレーム（93.75 フレーム/秒）。
低音は1オクターブ上で歌わせてから、声ごと1オクターブ下げて太い声にする。
ボイパは声ではなく、口で鳴らす音（唇の破裂・息・歯の摩擦）をノイズと音程から合成する。
歌声を使うときは「VOICEVOX:ずんだもん」のクレジットが必要（ページのフッターに記載済み）。

使い方: pip install numpy、ffmpeg を用意し、VOICEVOX エンジン（0.26 以降）を http://127.0.0.1:50021 で起動しておき、
        python3 tools/make_song.py         # 全パート
        python3 tools/make_song.py perc    # ボイパだけ作り直す（エンジン不要）
"""
import io, json, subprocess, sys, urllib.parse, urllib.request, wave
from pathlib import Path

import numpy as np

BASE = 'http://127.0.0.1:50021'
OUT = Path(__file__).resolve().parent.parent / 'rich' / 'audio'
SR = 24000
E = 20                      # 8分音符（フレーム）
EIGHTH = 60 / 140 / 2       # 8分音符（秒）
LENGTH = 6.4                # 1節の長さ（秒）
NORMAL, AMAAMA, TSUNTSUN = 3003, 3001, 3007   # ずんだもんの歌声

C3, D3, E3, F3, G3, A3, B3 = 48, 50, 52, 53, 55, 57, 59
C4, D4, E4, F4, G4, A4, B4, C5, D5, E5, F5, G5 = 60, 62, 64, 65, 67, 69, 71, 72, 74, 76, 77, 79
# (歌詞, 主旋律, 下ハモり, 上ハモり, 長さ)。歌詞が空なら休符
SONG = [('', None, None, None, E * 2),
        ('か', G4, E4, B4, E), ('た', A4, F4, C5, E), ('づ', G4, E4, B4, E), ('け', E4, C4, G4, E),
        ('で', G4, E4, B4, E), ('き', A4, F4, C5, E), ('た', C5, A4, E5, E), ('の', D5, B4, F5, E), ('だ', C5, E4, E5, E * 3), ('', None, None, None, E),
        ('ぴ', E5, C5, G5, E), ('か', D5, B4, F5, E), ('ぴ', C5, A4, E5, E), ('か', A4, F4, C5, E),
        ('き', G4, E4, B4, E), ('れ', A4, F4, C5, E), ('い', C5, A4, E5, E), ('な', D5, B4, F5, E), ('の', E5, C5, G5, E), ('だ', C5, G4, E5, E * 5),
        ('', None, None, None, E * 2)]
# 低音：4分音符ごとの根音（1オクターブ上の高さで書く）。C → C → G → C | Am → F → G → C
BASS = [None, C4, C4, C4, G3, C4, C4, A3, A3, F3, G3, C4, C4, C4, None]


def post(path, body=None, query=None):
    url = BASE + path + ('?' + urllib.parse.urlencode(query) if query else '')
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else b'', headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req) as r:
        return r.read()


def to_array(wav_bytes):
    with wave.open(io.BytesIO(wav_bytes)) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype='<i2').astype(np.float32) / 32768
        if w.getframerate() != SR:
            a = np.interp(np.arange(0, len(a), w.getframerate() / SR), np.arange(len(a)), a)
        return a


def sing(notes, singer):
    score = {'notes': [{'key': k, 'frame_length': n, 'lyric': l} for l, k, n in notes]}
    query = json.loads(post('/sing_frame_audio_query', score, {'speaker': 6000}))
    return to_array(post('/frame_synthesis', query, {'speaker': singer}))


def part(index, singer):
    return sing([(n[0], n[index], n[4]) for n in SONG], singer)


def bass():
    notes = [('', None, E * 2) if k is None else ('ぼ', k, E * 2) for k in BASS]
    a = sing(notes, NORMAL)
    # 1オクターブ下げて（声も太くなる）、長さは元に戻す
    raw = (np.clip(a, -1, 1) * 32767).astype('<i2').tobytes()
    low = subprocess.run(['ffmpeg', '-v', 'error', '-f', 's16le', '-ar', str(SR), '-ac', '1', '-i', '-',
                          '-af', f'asetrate={SR // 2},aresample={SR},atempo=2.0', '-f', 's16le', '-'],
                         input=raw, capture_output=True, check=True).stdout
    return np.frombuffer(low, dtype='<i2').astype(np.float32) / 32768


RNG = np.random.default_rng(140)


def lowpass(x, cutoff):
    """1次のローパス（息や破裂音の明るさを調整する）"""
    k = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x); acc = 0.0
    for i, v in enumerate(x):
        acc = (1 - k) * v + k * acc
        y[i] = acc
    return y


def highpass(x, cutoff):
    return x - lowpass(x, cutoff)


def bandpass(x, lo, hi):
    return lowpass(highpass(x, lo), hi)


def env(n, attack, decay):
    """立ち上がり attack 秒、そのあと decay 秒で指数的に消える音量の形"""
    t = np.arange(n) / SR
    return np.minimum(1, t / max(attack, 1e-4)) * np.exp(-np.maximum(0, t - attack) / decay)


def noise(sec):
    return RNG.uniform(-1, 1, int(sec * SR))


def kick():
    """唇で鳴らす「B」：低く沈む音程と、唇が開く瞬間の小さな破裂"""
    n = int(.22 * SR); t = np.arange(n) / SR
    freq = 50 + 75 * np.exp(-t / .03)
    body = np.sin(2 * np.pi * np.cumsum(freq) / SR) * env(n, .003, .07)
    pop = lowpass(noise(.22), 900) * env(n, .0008, .006) * 2.2
    return np.tanh((body + pop) * 1.8) * .9


def hat(open_=False):
    """歯のすき間から出す「ts」／長めの「tsss」"""
    sec = .18 if open_ else .06
    n = int(sec * SR)
    hiss = highpass(noise(sec), 5200) * env(n, .002, .07 if open_ else .018)
    tick = highpass(noise(sec), 2500) * env(n, .0005, .003) * .8   # 舌先の「t」
    return (hiss + tick) * .55


def snare():
    """唇の破裂「P」のあとに息の「fff」を続ける、ボイパの定番スネア"""
    n = int(.2 * SR); t = np.arange(n) / SR
    pop = (lowpass(noise(.2), 1500) * 1.6 + np.sin(2 * np.pi * 190 * t) * .5) * env(n, .0008, .01)
    breath = bandpass(noise(.2), 1300, 6500) * env(n, .006, .06)
    return np.tanh((pop + breath * 1.3) * 1.4) * .8


def perc():
    sounds = {'K': kick(), 'h': hat(), 'H': hat(True), 'S': snare()}
    out = np.zeros(int(LENGTH * SR) + SR)
    # 16分音符ごとの並び（1小節 = 16）。K: キック / h: ハイハット / H: 長いハイハット / S: スネア。歌い出しの2拍前から入る
    bars = ['K.h.S.hhK.KhS.h.', 'K.h.S.hhK.KhS.H.']
    step = EIGHTH / 2
    for i in range(int(LENGTH / step)):
        s = sounds.get(bars[(i // 16) % 2][i % 16])
        if s is None:
            continue
        at = int(i * step * SR)
        # 人が鳴らすので、強さとタイミングを少しだけ揺らす
        at = max(0, at + int(RNG.normal(0, .003) * SR))
        out[at:at + len(s)] += s[:len(out) - at] * RNG.uniform(.85, 1)
    return out


def save(name, a, gain):
    a = np.asarray(a, dtype=np.float32)[: int(LENGTH * SR)]
    a = np.pad(a, (0, int(LENGTH * SR) - len(a)))
    a = a / (np.max(np.abs(a)) or 1) * gain
    # 終わりを0.4秒かけて消す
    fade = int(.4 * SR)
    a[-fade:] *= np.linspace(1, 0, fade)
    raw = (a * 32767).astype('<i2').tobytes()
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 's16le', '-ar', str(SR), '-ac', '1', '-i', '-',
                    '-ar', '44100', '-b:a', '64k', str(OUT / f'song-{name}.mp3')], input=raw, check=True)
    print(f'song-{name}.mp3')


if __name__ == '__main__':
    if len(sys.argv) > 2 or (len(sys.argv) == 2 and sys.argv[1] != 'perc'):
        sys.exit(__doc__)
    OUT.mkdir(parents=True, exist_ok=True)
    if sys.argv[1:] == ['perc']:
        save('perc', perc(), .7)
        sys.exit()
    # 音量のつり合いはここで決める（ページ側では全体の音量だけを変える）
    save('melody', part(1, NORMAL), .9)
    save('harmony', part(2, AMAAMA), .6)
    save('bass', bass(), .75)
    save('perc', perc(), .7)
    save('top', part(3, TSUNTSUN), .45)
