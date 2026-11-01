"""MV版のEDM版に重ねる「合いの手」の音（掛け声と効果音）を、1本の音にして書き出す（mv/edm-voices.mp3）。

ファイルの先頭が映像の0拍目。拍の長さは mv/edm.timing.json の beat（Suno の曲の拍）に合わせる。
ページは地図の fx の ['sample', 0, 'edm-voices.mp3', …] で、曲の上にそのまま重ねる。

掛け声：Suno の音声2本を、Suno の言葉の時刻（lyrics alignment）と音の大きさで切り分けて、拍に置く。
        熱くなりすぎないように、どれも落ち着いた声にしている。
          light  … 明るく軽め、落ち着いた言い方（https://suno.com/song/439cf612-6f5d-4614-aab8-fa99c384d6e2、tools/edm/calls-light.mp3）
                   運動部の「ファイトー」「オー」「いっち、にー、さん、しー」
          casual … リラックスした普通の話し方（https://suno.com/song/63e28949-e76c-4d33-abc3-289642840ce2、tools/edm/calls-casual.mp3）
                   「おじゃましまーす」「おじゃましましたー」「ナイスバルク」「キレてる」
効果音：JingleScript で、拍の位置に書いて鳴らす（ノックとシャッターと小銭は JingleScript に入っている録音、ほかは部品で作った音）。

  拍      映像                         合いの手
  10.5〜11 泊まる先は、友人の家。       ドアをコンコン →「おじゃましまーす！」
  28・30   家が32軒建つ                インターホン「ピンポーン」
  32〜37   11都府県のはんこ            はんこの「ポン！」を8分音符で
  40〜44   友人の家を、渡り歩いた。      足音 →「おじゃましましたー！」
  88〜95   15分 運動                   「ファイトー！」「オー！」×2、「いっち！にー！さん！しー！」
  100〜104 卓球戦績メモ                ピンポン玉の「カコン、カコン」
  104〜107 ワリカン                    小銭の「チャリン」
  108・110 Pumpkin                     「ナイスバルク！」「キレてる！」
  124〜128 写真が次々切り替わる          カメラのシャッター「カシャ」

使い方: pip install numpy、ffmpeg を用意して
        python3 tools/make_edm_voices.py      # npx で JingleScript 1.1.0 を使う
"""
import json
import subprocess
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'mv' / 'edm-voices.mp3'
TAKES = {name: ROOT / 'tools' / 'edm' / f'calls-{name}.mp3' for name in ('light', 'casual')}
SR = 44100
BEAT = json.loads((ROOT / 'mv' / 'edm.timing.json').read_text())['beat']
LENGTH = 146

# 掛け声を重ねるか（「おじゃましまーす」をもっと明るく録り直すまでは止めておく。True にすると下の VOICES を重ねる）
USE_VOICES = False

# 使う音声、Suno の言葉の時刻（秒）から切り出す部分と、置く拍、速さ（1 より大きいと速く、高さは変えない）、音量
VOICES = [
    ('casual', 'おじゃましまーす', 4.20, 5.70, 11.5, 1.0, 1.0),
    ('casual', 'おじゃましましたー', 7.95, 9.80, 44.6, 1.0, 1.0),
    ('light', 'ファイトー', 0.15, 1.00, 88.0, 1.0, 1.0),
    ('light', 'オー', 1.95, 2.65, 89.0, 1.0, 1.0),
    ('light', 'ファイトー', 3.95, 4.90, 90.0, 1.0, 1.0),
    ('light', 'オー', 5.60, 6.25, 91.0, 1.0, 1.0),
    ('light', 'いっち', 7.50, 8.40, 92.0, 1.1, 1.0),
    ('light', 'にー', 8.75, 9.55, 93.0, 1.1, 1.0),
    ('light', 'さん', 9.70, 10.55, 94.0, 1.1, 1.0),
    ('light', 'しー', 11.15, 12.05, 95.0, 1.1, 1.0),
    ('casual', 'ナイスバルク', 0.00, 1.15, 108.0, 1.0, 1.0),
    ('casual', 'キレてる', 2.10, 3.20, 110.0, 1.0, 1.0),
]

SFX = {
    'format': 'jinglescript/1',
    'tempo': round(60 / BEAT, 3),
    'length': {'beats': LENGTH},
    'instruments': {
        # インターホン「ピンポーン」：鉄琴のような2音
        'chime': {'description': 'Door chime', 'blocks': [
            {'modes': [{'ratio': 1, 'level': 1, 'decay': 1.6}, {'ratio': 2.76, 'level': .3, 'decay': .6}, {'ratio': 5.4, 'level': .1, 'decay': .3}]}]},
        # はんこ「ポン！」：低い胴鳴りと、紙に当たる音
        'stamp': {'kind': 'sfx', 'pitch': 'C3', 'description': 'Rubber stamp thump', 'blocks': [
            {'osc': 'sine', 'level': 1}, {'pitchEnv': {'from': 7, 'to': 0, 'time': .05}}, {'env': {'attack': .001, 'decay': .16}},
            {'noise': 'pink', 'level': .5, 'decay': .04, 'filter': {'type': 'bandpass', 'cutoff': 1800, 'q': 1}}]},
        # ピンポン玉「カコン」：硬く短い音
        'pingpong': {'kind': 'sfx', 'pitch': 'E6', 'description': 'Ping-pong ball tock', 'blocks': [
            {'modes': [{'ratio': 1, 'level': 1, 'decay': .07}, {'ratio': 2.3, 'level': .4, 'decay': .04}]},
            {'noise': 'white', 'level': .3, 'decay': .01, 'filter': {'type': 'highpass', 'cutoff': 3000}}]},
    },
    'tracks': [
        {'instrument': 'knock', 'name': 'knock', 'gain': -2, 'reverb': False, 'notes': [
            {'at': 10.5, 'variant': 'door', 'vel': .95}, {'at': 11, 'variant': 'door', 'vel': .95}]},
        {'instrument': 'chime', 'name': 'chime', 'gain': -6, 'notes': [
            {'at': 28, 'pitch': 'E5', 'vel': .85}, {'at': 28.5, 'pitch': 'C5', 'vel': .8},
            {'at': 30, 'pitch': 'E5', 'vel': .85}, {'at': 30.5, 'pitch': 'C5', 'vel': .8}]},
        {'instrument': 'stamp', 'name': 'stamp', 'gain': -1, 'reverb': False, 'notes': [
            {'at': 32 + i * .5, 'vel': round(.85 + i * .01, 2)} for i in range(11)]},
        {'instrument': 'footsteps', 'name': 'steps', 'gain': -2, 'reverb': False, 'notes': [
            {'at': 40, 'variant': ['left', 'right'], 'vel': .9, 'repeat': {'every': .5, 'count': 8}}]},
        {'instrument': 'pingpong', 'name': 'pingpong', 'gain': -4, 'reverb': False, 'notes': [
            {'at': 100 + i * .5, 'pitch': 'E6' if i % 2 == 0 else 'B5', 'vel': .9} for i in range(8)]},
        {'instrument': 'coin', 'name': 'coin', 'gain': -3, 'notes': [{'at': 104 + i, 'vel': .9} for i in range(4)]},
        {'instrument': 'shutter', 'name': 'shutter', 'gain': -2, 'reverb': False, 'notes': [{'at': 124 + i * .5, 'vel': .95} for i in range(8)]},
    ],
}


def decode(path, start=None, end=None, tempo=1.0):
    args = ['ffmpeg', '-v', 'error']
    if start is not None:
        args += ['-ss', str(start), '-to', str(end)]
    args += ['-i', str(path), '-ac', '2', '-ar', str(SR)]
    if tempo != 1.0:
        args += ['-af', f'atempo={tempo}']
    args += ['-f', 's16le', '-']
    raw = subprocess.run(args, capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype='<i2').reshape(-1, 2).astype(np.float32) / 32768


def main():
    out = np.zeros((int((LENGTH * BEAT + 2) * SR), 2), np.float32)
    with tempfile.TemporaryDirectory() as tmp:
        score = Path(tmp) / 'sfx.json'
        score.write_text(json.dumps(SFX, ensure_ascii=False))
        subprocess.run(['npx', '-y', 'jinglescript@1.1.0', 'render', str(score), '-o', str(Path(tmp) / 'sfx.wav')], check=True, capture_output=True)
        sfx = decode(Path(tmp) / 'sfx.wav')
    n = min(len(sfx), len(out))
    out[:n] += sfx[:n] * .8
    for take, text, a, b, beat, tempo, gain in (VOICES if USE_VOICES else []):
        v = decode(TAKES[take], a, b, tempo)
        # 切り出しの頭の息や無音を落として、声が立ち上がる所を拍に合わせる
        level = np.abs(v).max(axis=1)
        smooth = np.convolve(level, np.ones(220) / 220, mode='same')
        first = int(np.argmax(smooth > smooth.max() * .12))
        v = v[max(0, first - int(.012 * SR)):]
        fade = int(.012 * SR)
        v[:fade] *= np.linspace(0, 1, fade)[:, None]
        v[-fade:] *= np.linspace(1, 0, fade)[:, None]
        at = int((beat * BEAT - .012) * SR)   # 声の立ち上がりの少し前（切り出しで残した分）から
        out[at:at + len(v)] += v[:len(out) - at] * gain
    out *= .9 / max(1.0, np.abs(out).max())   # 割れないときは音量を変えない（掛け声の有無で効果音の大きさが変わらないように）
    raw = (out * 32767).astype('<i2').tobytes()
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 's16le', '-ar', str(SR), '-ac', '2', '-i', '-', '-b:a', '128k', str(OUT)], input=raw, check=True)
    print(f'{OUT.relative_to(ROOT)}: {len(out) / SR:.1f} 秒')


if __name__ == '__main__':
    main()
