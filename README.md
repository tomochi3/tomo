# tomochi Portfolio

tomochi のポートフォリオサイトです。ビルド不要の静的サイト（HTML / CSS）で、GitHub Pages で公開しています。

https://tomochi3.github.io/tomo/

## 構成

```
index.html      ページ本体（作品一覧はここに直接書いています）
404.html        存在しないURLを開いたときのページ（中の参照は /tomo/ から始まる絶対パス）
rich/           リッチ版（https://tomochi3.github.io/tomo/rich/）。index.html に CSS と JS を内包。画像は rich/img/ にまとめ、シンプル版の img/ には依存しない
rich/fonts/     リッチ版の見出し（Dela Gothic One）と手書き（Yomogi）。ページで使う文字だけに絞ったもの。ライセンスは OFL-*.txt（SIL OFL 1.1）
css/style.css   スタイル（ライト / ダークはOSの設定に追従）
img/            作品のサムネイル（WebP。小カード用は 800×500 で名前が -sm）
fonts/          Inter（英字用、可変ウェイト）。Google Fonts は使わず、ここから読み込む。ライセンスは LICENSE-Inter.txt（SIL OFL 1.1）
icon.svg        ファビコン（青地に白の T）。favicon.ico と icon-32.png は SVG 非対応のブラウザ向け
apple-touch-icon.png  iPhone のホーム画面用アイコン
img/og.jpg      XやLINEで共有したときのプレビュー画像（1200×630）
```

## 自動チェック

push すると GitHub Actions（`.github/workflows/check.yml`）で次を確認します。結果は GitHub のコミット一覧に ✓ / ✗ で出ます。

- HTML の検査（html-validate。設定は `.htmlvalidate.json`）
- ページ内リンクと画像などのファイル参照の切れ（`tools/check_links.py`）
- 3 ページをブラウザで開いて、JavaScript のエラー・読み込み失敗・横スクロールがないか（`tools/smoke.mjs`、スマホ幅と PC 幅）

手元で試すとき:

```sh
python3 tools/check_links.py
npx html-validate@8.29.0 index.html rich/index.html 404.html
```

## ローカルで見る

```sh
python3 -m http.server 8000
# http://localhost:8000/ を開く
```

## 作品を追加する

1. サムネイルを 16:10（1600×1000 推奨）の画像にして `img/` に置きます
2. `index.html` の `<ul class="works">` の中に、既存の `<li>` を1つコピーして書き換えます
   - `href` … カードを押したときに開くサイトのURL
   - `img` の `src` と `alt` … サムネイルと、その説明
   - タイトル・1行の説明・種類・リンク名（「サイトを開く」など）

カードの大きさは `<li>` の class で決まります（PCでは4列の格子に並びます）。

| class | 大きさ |
| --- | --- |
| なし | 通常（2列ぶん。2枚で1段） |
| `is-small` | 半分（1列ぶん。4枚で1段、スマホでは2枚で1段）。種類ラベルは表示されません。画面全体だと細かすぎるので、特徴的な部分を拡大した 800×500 の画像を使います |
| `is-featured` | 全幅の横長カード（先頭の注目作品用） |

段の端が揃うように、通常カードは2枚ずつ、小カードは4枚ずつ並べてください。

## リッチ版の文章を変えたとき

見出し・手書き用のフォントは、ページで使っている文字だけを入れています。`rich/index.html` に新しい文字を足したら、フォントを作り直してください（作り直さなくても、その文字だけ端末のフォントで表示されます）。

```sh
pip install fonttools brotli
python3 tools/subset_fonts.py DelaGothicOne-Regular.ttf Yomogi-Regular.ttf
```

元のフォントの入手先は `tools/subset_fonts.py` の先頭に書いてあります。
