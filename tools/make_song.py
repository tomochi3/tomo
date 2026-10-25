"""リッチ版で生き物が歌う1節（rich/audio/zunda-song.mp3）を、ずんだもんの歌声で作る。

メロディと歌詞はオリジナル。テンポ 140、8分音符 = 20 フレーム（93.75 フレーム/秒）。
使うときは「VOICEVOX:ずんだもん」のクレジットが必要（ページのフッターに記載済み）。

使い方: VOICEVOX エンジン（0.26 以降）を http://127.0.0.1:50021 で起動しておき、
        python3 tools/make_song.py 3003 zunda.wav     # 3003 = ずんだもん（ノーマル）の歌声
        ffmpeg -i zunda.wav -af "loudnorm=I=-16:TP=-1.5,afade=t=out:st=5.6:d=0.4" -ac 1 -b:a 80k rich/audio/zunda-song.mp3
"""
import json, sys, urllib.request

BASE = 'http://127.0.0.1:50021'
E = 20  # 8分音符

def call(path, body=None):
    req = urllib.request.Request(BASE + path, data=None if body is None else json.dumps(body).encode(), headers={'Content-Type': 'application/json'}, method='POST' if body is not None else 'GET')
    with urllib.request.urlopen(req) as r:
        return r.read()

# (歌詞, MIDI番号, 長さ) ・ 歌詞が空なら休符
C4, D4, E4, F4, G4, A4, B4, C5, D5, E5 = 60, 62, 64, 65, 67, 69, 71, 72, 74, 76
notes = [('', None, E * 2),
         ('か', G4, E), ('た', A4, E), ('づ', G4, E), ('け', E4, E),
         ('で', G4, E), ('き', A4, E), ('た', C5, E), ('の', D5, E), ('だ', C5, E * 3), ('', None, E),
         ('ぴ', E5, E), ('か', D5, E), ('ぴ', C5, E), ('か', A4, E),
         ('き', G4, E), ('れ', A4, E), ('い', C5, E), ('な', D5, E), ('の', E5, E), ('だ', C5, E * 5),
         ('', None, E * 2)]
score = {'notes': [{'key': k, 'frame_length': n, 'lyric': l} for l, k, n in notes]}

singer = int(sys.argv[1])
query = json.loads(call('/sing_frame_audio_query?speaker=6000', score))
wav = call(f'/frame_synthesis?speaker={singer}', query)
open(sys.argv[2], 'wb').write(wav)
print('frames', sum(n for _, _, n in notes), 'seconds', round(sum(n for _, _, n in notes) / 93.75, 2))
