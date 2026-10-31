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

# 単調にならないように、DJ のように曲に手を加える（どれも映像の拍で書く。ページがその場でかける）
#   ['hp'|'lp', 始め, 終わり, 始めの周波数, 終わりの周波数]  … 高い音だけ／低い音だけにしていくフィルター
#   ['cut', 始め, 終わり]          … 音を止める（ドロップ前のため）
#   ['gate', 始め, 終わり, 'x.x.', 刻み] … 刻みごとに音を出す・止める（x が出す）
#   ['stutter', 始め, 長さ, 分割]  … 短い一切れを、分割の数だけくり返す
#   ['tape', 始め, 終わり]         … テープを止めたように、音が下がりながら止まる
#   ['riser', 始め, 長さ] / ['impact', 拍] / ['roll', 始め, 終わり] … 上に重ねる効果音
#   ['sample', 拍, ファイル, 早める秒] … 録った音を重ねる（tools/make_edm_chant.py の運動部の掛け声など）
FX = [
    # イントロ：高い音だけの細い音から、だんだん開いていく。ドロップの直前で半拍だけ止める
    ['hp', 0, 14, 900, 30], ['riser', 8, 7.5], ['cut', 15.5, 16], ['impact', 16],
    ['stutter', 31, 1, 8],
    # はんこ：8分音符で刻んで、はんこを押す音に合わせる
    ['gate', 32, 38, 'x.', .5],
    # 「友人の家を、渡り歩いた。」：こもっていって、ドロップで一気に開く
    ['lp', 40, 47.5, 18000, 600], ['cut', 47.5, 48], ['lp', 48, 48.05, 600, 20000], ['impact', 48],
    ['stutter', 63, 1, 8],
    # 4つのテーマ：拍の頭だけ鳴らして止める（ストップタイム）
    ['gate', 68, 72, 'x...', .25],
    ['stutter', 75, 1, 4],
    # 運動×勉強会の前で、テープを止めたように落とす。ブレイクは少しこもらせる
    ['tape', 79, 80], ['lp', 80, 80.05, 20000, 1400], ['lp', 87.5, 88, 1400, 20000],
    # 最後のドロップへ：低い音を抜いていきながら、ライザーとスネアのロール。直前で止めて、ドカン
    # 「15分 運動」：運動部の掛け声（ファイトー！オー！×2、いっち・に・さん・し）
    ['sample', 88, 'edm-chant.mp3', .055],
    ['hp', 88, 95.5, 30, 1800], ['riser', 88, 7.5], ['roll', 92, 95.5], ['cut', 95.5, 96], ['hp', 96, 96.05, 1800, 30], ['impact', 96],
    ['stutter', 103, 1, 8], ['stutter', 111, 1, 8],
    # 小さな作品4つ：ストップタイム
    ['gate', 112, 116, 'x...', .25],
    # 「ほかにも、いろいろ。」：16分音符で刻むノリに変える
    ['gate', 116, 120, 'x.xxx.x.x.xxx.xx', .25],
    # 「身近な不便を、小さなアプリで。」：こもらせてから、写真のところで開く
    ['lp', 120, 123.5, 18000, 900], ['cut', 123.5, 124], ['lp', 124, 124.05, 900, 20000], ['impact', 124],
    ['stutter', 127, 1, 8], ['impact', 128],
    # 締め：ロゴで一撃、そのあとは高い音だけにして消えていく
    ['impact', 136], ['hp', 138, 145, 30, 2500],
]
STOP = [68, 69, 70, 71, 112, 113, 114, 115]   # ストップタイムの一撃（映像も揺らす）


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
    # 音を止めている間・刻んで消している間は、映像も揺らさない
    def heard(v):
        for f in FX:
            if f[0] == 'cut' and f[1] <= v < f[2]:
                return False
            if f[0] == 'gate' and f[1] <= v < f[2] and f[3][int(round((v - f[1]) / f[4])) % len(f[3])] != 'x':
                return False
        return True
    k = [v for v, x in zip(steps, lo) if x > np.percentile(lo, 82) and x > 0 and heard(v)]
    s = [v for v, x in zip(steps, hi) if x > np.percentile(hi, 85) and x > 0 and v not in k and heard(v)]
    k = sorted(set(k + STOP))
    beat = (ANCHORS[-1][1] - ANCHORS[0][1]) / (ANCHORS[-1][0] - ANCHORS[0][0])
    data = {
        'format': 'tomochi-mv-edm/1',
        'source': 'https://suno.com/song/42d3ab13-9956-4ca3-9793-486df35198c5',
        'bpm': round(60 / beat, 2),
        'beat': round(beat, 6),
        'anchors': ANCHORS,
        'segments': SEGMENTS,
        'k': k, 's': s, 'h': sorted(set(BIG + STOP)),
        'fx': FX,
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'{OUT.relative_to(ROOT)}: {data["bpm"]} BPM, kick {len(k)}, snare {len(s)}')


if __name__ == '__main__':
    main()
