# tomochi3 Portfolio

tomochi3 のポートフォリオサイトです。ビルド不要の静的サイト（HTML / CSS / JavaScript）で、GitHub Pages でそのまま公開できます。

## 構成

```
index.html      ページ本体（作品・自己紹介・スキルはここに直接書いています）
css/style.css   スタイル（ライト / ダークモード対応）
js/main.js      テーマ切り替え、作品の絞り込み、スクロール演出
favicon.svg     ファビコン
```

## ローカルで見る

```sh
python3 -m http.server 8000
# http://localhost:8000/ を開く
```

## 作品を追加する

`index.html` の `<div class="works">` の中に `<article class="work">` を1つ追加します。

- `data-cat` … 絞り込みのカテゴリ。`app`（Webアプリ・ツール）/ `site`（サイト）/ `game`（ゲーム）/ `ext`（ブラウザ拡張）。スペース区切りで複数指定できます
- `--cover` … カバーの色。`var(--c-app)` / `var(--c-site)` / `var(--c-game)` / `var(--c-ext)` / `var(--c-note)`
- `.work__glyph` … カバーに表示する絵文字

## 公開（GitHub Pages）

リポジトリの **Settings → Pages** で、Source を「Deploy from a branch」、Branch を `main` / `/ (root)` にして保存します。
