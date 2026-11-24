"""リッチ版2（rich2/）の案で使う和文フォントを、ページで使っている文字だけに絞って rich2/fonts/ に書き出す。

  案A（rich2/a/）の発車標  … DotGothic16（LED のドット文字）
  案C（rich2/c/）の本文と見出し … しっぽり明朝 Regular / Bold

rich2/a/index.html か rich2/c/index.html の文章を変えたら実行し直す（使っていない文字は端末のフォントで表示される）。
元のフォントは Google Fonts のリポジトリから取得する（どれも SIL OFL 1.1）。
  https://raw.githubusercontent.com/google/fonts/main/ofl/dotgothic16/DotGothic16-Regular.ttf
  https://raw.githubusercontent.com/google/fonts/main/ofl/shipporimincho/ShipporiMincho-Regular.ttf
  https://raw.githubusercontent.com/google/fonts/main/ofl/shipporimincho/ShipporiMincho-Bold.ttf

使い方: pip install fonttools brotli
        python3 tools/subset_rich2_fonts.py <DotGothic16-Regular.ttf> <ShipporiMincho-Regular.ttf> <ShipporiMincho-Bold.ttf>
"""
import html
import re
import sys
from pathlib import Path

from fontTools import subset

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'rich2' / 'fonts'


def page_text(page):
    src = page.read_text(encoding='utf-8')
    body = src[src.index('<body'):]
    # スクリプトの中で表示する言葉も入れる
    scripts = ''.join(re.findall(r'<script>(.*?)</script>', body, flags=re.S))
    shown = ''.join(re.findall(r"'([^'\n]*[^\x00-\x7f][^'\n]*)'", scripts))
    body = re.sub(r'<script.*?</script>', '', body, flags=re.S)
    body = re.sub(r'<!--.*?-->', '', body, flags=re.S)
    text = html.unescape(re.sub(r'<[^>]+>', '', body)) + shown
    text += ''.join(re.findall(r'content: "([^"]+)"', src))
    ascii_ = ''.join(chr(c) for c in range(0x20, 0x7f))
    return ''.join(sorted(set(text + ascii_ + '０１２３４５６７８９') - set('\n\r\t')))


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
    print(f'{out.relative_to(ROOT)}: {len(text)} 文字, {out.stat().st_size // 1024} KB')


if __name__ == '__main__':
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    OUT.mkdir(parents=True, exist_ok=True)
    a = page_text(ROOT / 'rich2' / 'a' / 'index.html')
    c = page_text(ROOT / 'rich2' / 'c' / 'index.html')
    build(sys.argv[1], OUT / 'dotgothic16.woff2', a)
    build(sys.argv[2], OUT / 'shippori-mincho.woff2', c)
    build(sys.argv[3], OUT / 'shippori-mincho-bold.woff2', c)
