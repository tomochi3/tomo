# tomochi3 Portfolio

tomochi3 のポートフォリオサイトです。ビルド不要の静的サイト（HTML / CSS）で、GitHub Pages で公開しています。

https://tomochi3.github.io/tomo/

## 構成

```
index.html      ページ本体（作品一覧はここに直接書いています）
css/style.css   スタイル（ライト / ダークはOSの設定に追従）
img/            作品のサムネイル（1600×1000 の WebP）
favicon.svg     ファビコン
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

一覧は2列で並ぶので、偶数件にすると端が揃います。
