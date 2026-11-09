// SVG sahifa -> PNG (+PDF) va har bir qatlam alohida shaffof PNG (PSD uchun).
// Usage: node export.js '{"html":..,"w":..,"h":..,"png":..,"pdf":..|null,"layers":[..],"layerdir":..}'
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const j = JSON.parse(process.argv[2]);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: j.w, height: j.h } });
  await page.goto('file://' + j.html, { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(200);
  await page.screenshot({ path: j.png });
  if (j.pdf) await page.pdf({ path: j.pdf, width: j.w + 'px', height: j.h + 'px', printBackground: true, pageRanges: '1' });
  for (const L of j.layers) {
    await page.evaluate((L) => document.querySelectorAll('svg > g[id]').forEach(g => g.style.display = g.id === L ? '' : 'none'), L);
    await page.screenshot({ path: path.join(j.layerdir, L + '.png'), omitBackground: true });
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
