"""ボイパの録音から1打ずつ切り出して tools/beatbox/ に保存する（tools/make_song.py が使う）。

録音は「ドゥ」（キック）「ツ」（ハイハット）「パフ」（スネア）をそれぞれ数回ずつ鳴らしたもの。
使い方: python3 tools/cut_beatbox.py キックの録音 ハイハットの録音 スネアの録音
（m4a などは ffmpeg で読み込む）
"""
import subprocess, sys
from pathlib import Path

import numpy as np

SR = 24000
DIR = Path(__file__).resolve().parent / 'beatbox'
# 切り出す長さ（秒）
LENGTHS = {'kick': .26, 'hat': .12, 'snare': .32}


def load(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype='<i2').astype(np.float32) / 32768


def hits(a, length):
    """音量が急に上がったところを1打とみなし、少し手前から切り出す"""
    hop = 64
    e = np.sqrt(np.convolve(a ** 2, np.ones(hop) / hop, 'same'))
    thr = max(e.max() * .2, np.median(e) * 6)
    out, i, n = [], 0, int(length * SR)
    while i < len(a):
        if e[i] > thr:
            start = max(0, i - int(.008 * SR))
            seg = a[start:start + n].copy()
            if len(seg) == n:
                out.append(seg)
            i = start + n
        else:
            i += hop
    return out


def tidy(seg):
    seg = seg - seg.mean()
    fade = len(seg) // 3
    seg[-fade:] *= np.linspace(1, 0, fade) ** 2
    seg[:48] *= np.linspace(0, 1, 48)
    return seg / (np.max(np.abs(seg)) or 1) * .95


def centroid(seg):
    f = np.abs(np.fft.rfft(seg * np.hanning(len(seg))))
    fr = np.fft.rfftfreq(len(seg), 1 / SR)
    return (f * fr).sum() / f.sum()


def save(path, seg):
    raw = (seg * 32767).astype('<i2').tobytes()
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 's16le', '-ar', str(SR), '-ac', '1', '-i', '-', str(path)], input=raw, check=True)


if __name__ == '__main__':
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    DIR.mkdir(exist_ok=True)
    for old in DIR.glob('*.wav'):
        old.unlink()
    for name, path in zip(['kick', 'hat', 'snare'], sys.argv[1:]):
        segs = hits(load(path), LENGTHS[name])
        # 音の高さが他と大きく違う打（息や物音）は外す
        c = np.array([centroid(s) for s in segs])
        keep = [s for s, x in zip(segs, c) if abs(x - np.median(c)) < np.median(c) * .5]
        for i, s in enumerate(keep, 1):
            save(DIR / f'{name}-{i}.wav', tidy(s))
        print(name, len(segs), '打のうち', len(keep), '打を保存')
