"""MVでボールが弾けたときに鳴らす音を書き出す（mv/audio/）。

今はセリフは入れず、友人の家に着く場面のドアのノック（knock.mp3。ページが2回、半拍あけて鳴らす）だけ。
セリフを足すときは LINES に書き、VOICEVOXエンジン（VOICEVOX:ずんだもん、speaker 3）を http://127.0.0.1:50021 で起動しておく。
python3 tools/make_mv_voices.py を実行する。Python標準ライブラリとffmpegが必要（ノックは npx で JingleScript 1.1.0 を使う）。
"""
import io
import json
from pathlib import Path
import subprocess
import tempfile
import urllib.parse
import urllib.request
import wave

BASE = 'http://127.0.0.1:50021'
OUT = Path(__file__).resolve().parent.parent / 'mv' / 'audio'
LINES = []   # (ファイル名, セリフ, 最長の秒数)


def post(path, params, body=None):
    request = urllib.request.Request(
        BASE + path + '?' + urllib.parse.urlencode(params),
        data=json.dumps(body).encode() if body is not None else b'',
        headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def make_knock():
    # JingleScript に入っているドアのノックの録音（CC0）を1回だけ鳴らして、頭から0.32秒を使う
    score = {'format': 'jinglescript/1', 'tempo': 120, 'length': {'beats': 1}, 'tracks': [
        {'instrument': 'knock', 'name': 'knock', 'reverb': False, 'notes': [{'at': 0, 'variant': 'door', 'vel': .95}]}]}
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / 'knock.json'
        path.write_text(json.dumps(score))
        subprocess.run(['npx', '-y', 'jinglescript@1.1.0', 'render', str(path), '-o', str(Path(tmp) / 'knock.wav')],
                       check=True, capture_output=True)
        subprocess.run([
            'ffmpeg', '-y', '-v', 'error', '-i', str(Path(tmp) / 'knock.wav'),
            '-af', 'atrim=0:0.32,afade=t=out:st=0.27:d=0.05,volume=-3dB',
            '-ar', '44100', '-ac', '1', '-b:a', '96k', str(OUT / 'knock.mp3')], check=True)
    print('knock: ドアのノック')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    make_knock()
    for name, text, maximum in LINES:
        query = json.loads(post('/audio_query', {'text': text, 'speaker': 3}))
        query.update(speedScale=1.3, pitchScale=.03, intonationScale=1.25,
                     prePhonemeLength=.02, postPhonemeLength=.06)
        data = post('/synthesis', {'speaker': 3}, query)
        with wave.open(io.BytesIO(data)) as audio:
            duration = audio.getnframes() / audio.getframerate()
        tempo = max(1, duration / maximum)
        subprocess.run([
            'ffmpeg', '-y', '-v', 'error', '-i', 'pipe:0',
            '-af', f'atempo={tempo:.6f},loudnorm=I=-18:TP=-3:LRA=7',
            '-ar', '44100', '-ac', '1', '-b:a', '96k', str(OUT / f'{name}.mp3')
        ], input=data, check=True)
        print(f'{name}: {text} ({duration / tempo:.2f}s)')


if __name__ == '__main__':
    main()
