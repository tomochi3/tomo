"""リッチ版で生き物たちが歌う1節を、ずんだもんの声で作る（rich/audio/ に書き出す）。

パートごとに別のファイルにし、ページ側で並んだ仲間の数に応じて重ねる。
  song-melody.mp3  主旋律（リーダー）           … いつも
  song-harmony.mp3 ハモり（主旋律の3度下）      … いつも
  song-bass.mp3    低音（和音の根音を「ぼん」） … 仲間4匹から
  song-perc.mp3    ボイパ（録音した「ドゥ」「ツ」「パフ」） … 仲間6匹から
  song-top.mp3     上ハモり（主旋律の3度上）    … 仲間10匹から

メロディと歌詞はオリジナル。ハ長調、テンポ 140、8分音符 = 20 フレーム（93.75 フレーム/秒）。
低音は1オクターブ上で歌わせてから、声ごと1オクターブ下げて太い声にする。
ボイパは、本人が口で鳴らした録音（tools/beatbox/、tools/cut_beatbox.py で1打ずつ切り出したもの）を並べる。
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
BEATBOX = Path(__file__).resolve().parent / 'beatbox'


def hits(name):
    """tools/beatbox/ にある1打ずつの録音（tools/cut_beatbox.py で作る）"""
    files = sorted(BEATBOX.glob(f'{name}-*.wav'))
    if not files:
        sys.exit(f'{BEATBOX}/{name}-*.wav がありません。tools/cut_beatbox.py で作ってください')
    return [to_array(f.read_bytes()) for f in files]


def perc():
    sounds = {'K': hits('kick'), 'h': hits('hat'), 'S': hits('snare')}
    gain = {'K': 1, 'h': .5, 'S': .85}
    out = np.zeros(int(LENGTH * SR) + SR)
    # 16分音符ごとの並び（1小節 = 16）。K: キック / h: ハイハット / S: スネア。歌い出しの2拍前から入る
    bars = ['K.h.S.hhK.KhS.h.', 'K.h.S.hhK.KhS.hh']
    step = EIGHTH / 2
    turn = {k: 0 for k in sounds}
    for i in range(int(LENGTH / step)):
        c = bars[(i // 16) % 2][i % 16]
        if c not in sounds:
            continue
        # 同じ音でも録音した何打かを順番に使い、毎回少しずつ違う響きにする
        s = sounds[c][turn[c] % len(sounds[c])]
        turn[c] += 1
        at = int(i * step * SR)
        out[at:at + len(s)] += s[:len(out) - at] * gain[c]
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
