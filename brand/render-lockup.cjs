// Renders brand/logo-lockup.html to PNGs with Chromium (proper Arabic shaping + web fonts).
// Run from C:\Users\HP\boise\septic-pumping-maine (where puppeteer is installed):
//   node ../shams-elwadi-egypt/brand/render-lockup.js
const path = require('path');
const puppeteer = require('puppeteer');
(async () => {
  const here = path.resolve(__dirname);
  const browser = await puppeteer.launch({ headless: 'new' });
  const page = await browser.newPage();
  await page.setViewport({ width: 1600, height: 1400, deviceScaleFactor: 2 });
  await page.goto('file:///' + path.join(here, 'logo-lockup.html').replace(/\\/g, '/'), { waitUntil: 'networkidle0' });
  await page.evaluate(() => document.fonts.ready);
  await new Promise(r => setTimeout(r, 800));
  for (const id of ['horizontal', 'horizontal-dark', 'stacked']) {
    const el = await page.$('#' + id);
    const out = path.join(here, `logo-${id}.png`);
    await el.screenshot({ path: out, omitBackground: false });
    console.log('wrote', out);
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
