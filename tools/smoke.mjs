// 各ページを実際のブラウザで開き、JavaScript のエラーと読み込み失敗がないかを確かめる。
// 使い方: python3 -m http.server 8000 を起動した状態で node tools/smoke.mjs
import { chromium } from 'playwright';

const base = process.env.BASE_URL || 'http://127.0.0.1:8000';
const pages = ['/', '/rich/', '/gpu/', '/mv/', '/404.html'];
const viewports = [{ width: 390, height: 844 }, { width: 1280, height: 800 }];

const browser = await chromium.launch();
let failed = 0;
for (const viewport of viewports) {
  for (const path of pages) {
    const page = await browser.newPage({ viewport });
    const errors = [];
    page.on('pageerror', (e) => errors.push(e.message));
    page.on('response', (r) => {
      if (r.status() >= 400 && r.url().startsWith(base)) errors.push(`${r.status()} ${r.url()}`);
    });
    // 404.html の中の /tomo/... は公開先のパスなので、手元ではリポジトリ直下に読み替える
    await page.route(`${base}/tomo/**`, (route) => route.continue({ url: route.request().url().replace('/tomo/', '/') }));
    await page.goto(base + path, { waitUntil: 'networkidle' });
    const height = await page.evaluate(() => document.body.scrollHeight);
    for (let y = 0; y < height; y += 600) {
      await page.evaluate((y) => window.scrollTo(0, y), y);
      await page.waitForTimeout(30);
    }
    await page.waitForLoadState('networkidle');
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    if (overflow > 0) errors.push(`横スクロールが ${overflow}px 出ています`);
    const label = `${path} (${viewport.width}px)`;
    if (errors.length) {
      failed++;
      console.log(`NG ${label}\n  ${errors.join('\n  ')}`);
      // GitHub Actions では注釈としても出し、コミットの ✗ から内容が見えるようにする
      if (process.env.GITHUB_ACTIONS) for (const e of errors) console.log(`::error title=${label}::${e}`);
    } else {
      console.log(`OK ${label}`);
    }
    await page.close();
  }
}
await browser.close();
process.exit(failed ? 1 : 0);
