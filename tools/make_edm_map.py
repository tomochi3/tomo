"""MV版のEDM版の曲（Suno で作ったもの）を、映像の拍の表に合わせるための地図を書き出す（mv/edm.timing.json）。

曲は Suno で作った「tomochi MV (2026 club edit)」（https://suno.com/song/42d3ab13-9956-4ca3-9793-486df35198c5）。
ジャージークラブ × UKガラージ × フューチャーベースのインスト、約129.6 BPM、ト短調、75.6秒。

映像は146拍で、16・48・96・128拍目に盛り上がりがあり、80〜96拍目は静かな場面。
曲の盛り上がりの位置はそれと違うので、小節の切れ目で曲をつなぎ替えて（DJの編集のように）合わせる。
  映像  0〜16  ← 曲 16〜32   イントロの盛り上げ
  映像 16〜80  ← 曲 32〜96   ドロップ・ブレイク・2回目のドロップ
  映像 80〜88  ← 曲 52〜60   静かなブレイク（運動×勉強会）
  映像 88〜96  ← 曲 120〜128 最後のドロップへ向けた盛り上げ
  映像 96〜128 ← 曲 128〜160 最後のドロップ（作品）
  映像 128〜146 ← 曲 96〜114 大きな場面のまま、最後の数拍で消していく
曲の拍の時刻は Suno の解析（audio-analysis）の拍から、いくつかの拍を目印にして直線でつなぐ（ずれは 20ms 以内）。

映像を揺らすきっかけ（キック・スネア）も、曲の音から拾う：低い音の立ち上がりをキック、中高音の立ち上がりをスネアとする。

使い方: pip install numpy、ffmpeg を用意して
        python3 tools/make_edm_map.py           # mv/edm.mp3 を読んで mv/edm.timing.json を書く
"""
import json
import subprocess
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
MP3 = ROOT / 'mv' / 'edm.mp3'
OUT = ROOT / 'mv' / 'edm.timing.json'
SR = 22050

# Suno の解析から：曲の拍の番号 → 秒（この間は直線でつなぐ）
ANCHORS = [(0, .23396), (32, 15.05312), (64, 29.87053), (96, 44.68081), (128, 59.48779), (162, 75.2095)]
# [映像の始まりの拍, 映像の終わりの拍, 曲の始まりの拍]
SEGMENTS = [(0, 16, 16), (16, 80, 32), (80, 88, 52), (88, 96, 120), (96, 128, 128), (128, 146, 96)]
BIG = [16, 48, 80, 96, 128, 136]   # 映像の大きな場面（ドロップや章の頭）


def song_t(b):
    for (b0, t0), (b1, t1) in zip(ANCHORS, ANCHORS[1:]):
        if b <= b1:
            return t0 + (b - b0) * (t1 - t0) / (b1 - b0)
    (b0, t0), (b1, t1) = ANCHORS[-2:]
    return t1 + (b - b1) * (t1 - t0) / (b1 - b0)


def song_beat(v):
    for v0, v1, s0 in SEGMENTS:
        if v0 <= v < v1:
            return s0 + (v - v0)
    return None


def main():
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(MP3), '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, dtype='<i2').astype(np.float32) / 32768
    # 低い音（キック・808）と、中高音（スネア・クラップ）の大きさ
    low = np.convolve(a, np.ones(48) / 48, mode='same')
    high = a - np.convolve(a, np.ones(6) / 6, mode='same')

    def level(x, t):
        i = int(t * SR)
        return float(np.sqrt(np.mean(x[i:i + int(.05 * SR)] ** 2) + 1e-12))

    def onset(x, t):
        return level(x, t) - level(x, t - .06)

    steps = [v / 4 for v in range(0, 146 * 4)]   # 16分音符ごとに調べる
    lo = np.array([onset(low, song_t(song_beat(v))) for v in steps])
    hi = np.array([onset(high, song_t(song_beat(v))) for v in steps])
    k = [v for v, x in zip(steps, lo) if x > np.percentile(lo, 82) and x > 0]
    s = [v for v, x in zip(steps, hi) if x > np.percentile(hi, 85) and x > 0 and v not in k]
    beat = (ANCHORS[-1][1] - ANCHORS[0][1]) / (ANCHORS[-1][0] - ANCHORS[0][0])
    data = {
        'format': 'tomochi-mv-edm/1',
        'source': 'https://suno.com/song/42d3ab13-9956-4ca3-9793-486df35198c5',
        'bpm': round(60 / beat, 2),
        'beat': round(beat, 6),
        'anchors': ANCHORS,
        'segments': SEGMENTS,
        'k': k, 's': s, 'h': BIG,
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'{OUT.relative_to(ROOT)}: {data["bpm"]} BPM, kick {len(k)}, snare {len(s)}')


if __name__ == '__main__':
    main()
