// HTML -> PNG/JPG/PDF renderer (Playwright + Chromium).
// Usage: node render.js <in.html> <out.(png|jpg|pdf)> <W> <H> <scale>
const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const [inp, out, w, h, scale] = process.argv.slice(2);
  const W = parseInt(w, 10), H = parseInt(h, 10), S = parseFloat(scale || '1');
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: S });
  await page.goto('file://' + path.resolve(inp), { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(150);
  const ext = path.extname(out).toLowerCase();
  if (ext === '.pdf') {
    await page.pdf({ path: out, width: W + 'px', height: H + 'px', printBackground: true });
  } else {
    await page.screenshot({
      path: out, type: ext === '.jpg' || ext === '.jpeg' ? 'jpeg' : 'png',
      quality: ext === '.png' ? undefined : 95,
      clip: { x: 0, y: 0, width: W, height: H },
    });
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
