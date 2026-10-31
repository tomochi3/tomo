"""MV版のEDM版で、「15分 運動」が出るところに入れる、運動部の合いの手（掛け声）を作る（mv/edm-chant.mp3）。

  88拍目 「ファイトー！」（リーダー）→ 89拍目 「オー！」（みんな）
  90拍目 「ファイトー！」            → 91拍目 「オー！」
  92〜95拍目 「いっち！ に！ さん！ し！」（みんな。最後のドロップへの盛り上げに重ねる）
ファイルの先頭が88拍目。拍の長さは mv/edm.timing.json の beat（Suno の曲の拍）に合わせる。
「みんな」は VOICEVOX の何人かの声を、少しずつ時間と高さをずらして重ねて、部活の集団の声にする。
声：VOICEVOX:青山龍星（リーダー・熱血）、玄野武宏、白上虎太郎、剣崎雌雄、雀松朱司、九州そら、春日部つむぎ

使い方: pip install numpy、ffmpeg を用意し、VOICEVOX エンジン（0.26 以降）を http://127.0.0.1:50021 で起動しておき、
        python3 tools/make_edm_chant.py
"""
import io
import json
import random
import subprocess
import urllib.parse
import urllib.request
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'mv' / 'edm-chant.mp3'
BASE = 'http://127.0.0.1:50021'
SR = 24000
BEAT = json.loads((ROOT / 'mv' / 'edm.timing.json').read_text())['beat']

LEADER = 81                                  # 青山龍星（熱血）
TEAM = [39, 32, 21, 52, 16, 8, 11]           # 玄野武宏（喜び）・白上虎太郎（わーい）・剣崎雌雄・雀松朱司・九州そら・春日部つむぎ・玄野武宏
# (拍, 言葉, 誰が, 声の高さの上げ幅)
CALLS = [(0, 'ファイトー', 'leader', .06), (1, 'オー', 'team', .04),
         (2, 'ファイトー', 'leader', .08), (3, 'オー', 'team', .06),
         (4, 'イッチ', 'team', .02), (5, 'ニッ', 'team', .03), (6, 'サン', 'team', .04), (7, 'シッ', 'team', .07)]


def post(path, query, body=None):
    url = BASE + path + '?' + urllib.parse.urlencode(query)
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else b'', method='POST',
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as r:
        return r.read()


def say(text, speaker, pitch):
    q = json.loads(post('/audio_query', {'text': text, 'speaker': speaker}))
    # 短く、強く、張り上げる。前の無音はなくして、拍の頭から声が出るようにする
    q.update(speedScale=1.25, pitchScale=pitch, intonationScale=1.6, volumeScale=1.3, prePhonemeLength=0, postPhonemeLength=.04)
    wav = post('/synthesis', {'speaker': speaker}, q)
    with wave.open(io.BytesIO(wav)) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype='<i2').astype(np.float32) / 32768
        rate = w.getframerate()
    if rate != SR:
        a = np.interp(np.arange(0, len(a), rate / SR), np.arange(len(a)), a)
    # 鳴り始めを、声の大きさが立ち上がった所にそろえる（「フ」の息の分だけ前に出す）
    loud = np.where(np.abs(a) > .05)[0]
    return a[max(0, (loud[0] if len(loud) else 0) - int(.03 * SR)):]


def main():
    random.seed(15)
    out = np.zeros((int((8 * BEAT + 1) * SR), 2), np.float32)
    for beat, text, who, lift in CALLS:
        voices = [(LEADER, 0, 0, 1.0)] if who == 'leader' else [(sp, random.uniform(-.018, .018), random.uniform(-.03, .03), .55) for sp in TEAM]
        for i, (sp, shift, pitch, gain) in enumerate(voices):
            a = say(text, sp, lift + pitch)
            at = int((beat * BEAT + .03 + shift) * SR)   # 先頭に少し余白（ページ側で 0.03 秒早めて鳴らす。mp3 の頭の遅れもここで吸収）
            pan = 0 if who == 'leader' else (i / (len(voices) - 1) - .5) * 1.4
            left, right = gain * min(1, 1 - pan), gain * min(1, 1 + pan)
            end = min(len(out), at + len(a))
            out[at:end, 0] += a[:end - at] * left
            out[at:end, 1] += a[:end - at] * right
    out /= max(1e-6, np.abs(out).max()) / .9
    raw = (out * 32767).astype('<i2').tobytes()
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 's16le', '-ar', str(SR), '-ac', '2', '-i', '-',
                    '-ar', '44100', '-b:a', '128k', str(OUT)], input=raw, check=True)
    print(f'{OUT.relative_to(ROOT)}: {len(out) / SR:.2f} 秒')


if __name__ == '__main__':
    main()
