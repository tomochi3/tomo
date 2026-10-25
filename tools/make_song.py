"""リッチ版で生き物たちが歌う1節（rich/audio/zunda-song.mp3）を、ずんだもんの歌声で作る。

主旋律（リーダー）とハモり（仲間たち）を別々に合成して、重ねた1つの音声にする。
メロディと歌詞はオリジナル。ハ長調、テンポ 140、8分音符 = 20 フレーム（93.75 フレーム/秒）。
ハモりは基本的に主旋律の3度下。長く伸ばす「ド」の下は、ドの和音の「ミ」や「ソ」で支える。
使うときは「VOICEVOX:ずんだもん」のクレジットが必要（ページのフッターに記載済み）。

使い方: VOICEVOX エンジン（0.26 以降）を http://127.0.0.1:50021 で起動しておき、
        python3 tools/make_song.py out_dir
        ffmpeg -i out_dir/melody.wav -i out_dir/harmony.wav \\
          -filter_complex "[1]volume=0.7[h];[0][h]amix=inputs=2:normalize=0,loudnorm=I=-16:TP=-1.5,afade=t=out:st=5.6:d=0.4" \\
          -ac 1 -b:a 80k rich/audio/zunda-song.mp3
"""
import json, sys, urllib.request
from pathlib import Path

BASE = 'http://127.0.0.1:50021'
E = 20  # 8分音符
MELODY_SINGER, HARMONY_SINGER = 3003, 3001  # ずんだもん（ノーマル） / ずんだもん（あまあま）

C4, D4, E4, F4, G4, A4, B4, C5, D5, E5 = 60, 62, 64, 65, 67, 69, 71, 72, 74, 76
# (歌詞, 主旋律, ハモり, 長さ)。歌詞が空なら休符
SONG = [('', None, None, E * 2),
        ('か', G4, E4, E), ('た', A4, F4, E), ('づ', G4, E4, E), ('け', E4, C4, E),
        ('で', G4, E4, E), ('き', A4, F4, E), ('た', C5, A4, E), ('の', D5, B4, E), ('だ', C5, E4, E * 3), ('', None, None, E),
        ('ぴ', E5, C5, E), ('か', D5, B4, E), ('ぴ', C5, A4, E), ('か', A4, F4, E),
        ('き', G4, E4, E), ('れ', A4, F4, E), ('い', C5, A4, E), ('な', D5, B4, E), ('の', E5, C5, E), ('だ', C5, G4, E * 5),
        ('', None, None, E * 2)]


def call(path, body):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req) as r:
        return r.read()


def sing(part, singer, out):
    score = {'notes': [{'key': n[part], 'frame_length': n[3], 'lyric': n[0]} for n in SONG]}
    query = json.loads(call('/sing_frame_audio_query?speaker=6000', score))
    out.write_bytes(call(f'/frame_synthesis?speaker={singer}', query))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    d = Path(sys.argv[1]); d.mkdir(parents=True, exist_ok=True)
    sing(1, MELODY_SINGER, d / 'melody.wav')
    sing(2, HARMONY_SINGER, d / 'harmony.wav')
    print('seconds', round(sum(n[3] for n in SONG) / 93.75, 2))
