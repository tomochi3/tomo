"""リッチ版の見出し・手書き用フォントを、ページで使っている文字だけに絞って rich/fonts/ に書き出す。

rich/index.html の文章を変えたら実行し直す（使っていない文字は端末のフォントで表示される）。
元のフォントは Google Fonts のリポジトリから取得する（どちらも SIL OFL 1.1）。
  https://raw.githubusercontent.com/google/fonts/main/ofl/delagothicone/DelaGothicOne-Regular.ttf
  https://raw.githubusercontent.com/google/fonts/main/ofl/yomogi/Yomogi-Regular.ttf

使い方: pip install fonttools brotli
        python3 tools/subset_fonts.py <DelaGothicOne-Regular.ttf> <Yomogi-Regular.ttf>
"""
import html
import re
import sys
from pathlib import Path

from fontTools import subset

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / 'rich' / 'index.html'


def page_text():
    src = PAGE.read_text(encoding='utf-8')
    body = src[src.index('<body'):]
    body = re.sub(r'<script.*?</script>', '', body, flags=re.S)
    body = re.sub(r'<!--.*?-->', '', body, flags=re.S)
    text = html.unescape(re.sub(r'<[^>]+>', '', body))
    # CSS の content で出している文字も入れる
    text += ''.join(re.findall(r'content: "([^"]+)"', src))
    ascii_ = ''.join(chr(c) for c in range(0x20, 0x7f))
    return ''.join(sorted(set(text + ascii_) - set('\n\r\t')))


def build(source, out, text):
    options = subset.Options()
    options.flavor = 'woff2'
    options.layout_features = ['*']
    options.name_IDs = ['*']
    font = subset.load_font(source, options)
    sub = subset.Subsetter(options)
    sub.populate(text=text)
    sub.subset(font)
    subset.save_font(font, str(out), options)
    print(f'{out.relative_to(ROOT)}: {out.stat().st_size // 1024} KB')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    text = page_text()
    print(f'{len(text)} 文字')
    build(sys.argv[1], ROOT / 'rich' / 'fonts' / 'dela-gothic-one.woff2', text)
    build(sys.argv[2], ROOT / 'rich' / 'fonts' / 'yomogi.woff2', text)
