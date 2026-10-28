"""ページ内リンク（#id）と、画像・CSSなどローカルファイルへの参照が切れていないか調べる。

/tomo/ で始まる絶対パスは、このリポジトリの直下として扱う（GitHub Pages の公開先が /tomo/ のため）。
"""
import os
import re
import sys

PAGES = ['index.html', 'rich/index.html', 'gpu/index.html', '404.html']
SITE_ROOT = '/tomo/'


def resolve(page, ref):
    path = ref.split('#')[0].split('?')[0]
    if path.startswith(SITE_ROOT):
        path = path[len(SITE_ROOT):]
    else:
        path = os.path.normpath(os.path.join(os.path.dirname(page), path))
    if path in ('', '.') or ref.split('?')[0].endswith('/'):
        path = os.path.join(path, 'index.html')
    return path


def main():
    problems = []
    for page in PAGES:
        html = open(page, encoding='utf-8').read()
        ids = set(re.findall(r'\bid="([^"]+)"', html))
        for ref in re.findall(r'\b(?:src|href|srcset)="([^" ]+)', html):
            if ref.startswith(('http://', 'https://', 'mailto:', 'data:')):
                continue
            if ref.startswith('#'):
                if ref != '#' and ref[1:] not in ids:
                    problems.append(f'{page}: ページ内リンク {ref} の行き先がありません')
                continue
            if not os.path.exists(resolve(page, ref)):
                problems.append(f'{page}: {ref} が見つかりません')
    for p in problems:
        print(p)
    print(f'{len(PAGES)} ページを確認: 問題 {len(problems)} 件')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
