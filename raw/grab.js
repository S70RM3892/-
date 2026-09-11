const { chromium } = require('playwright-core');
const fs = require('fs');

(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium', args: ['--no-sandbox'] });
  const ctx = await b.newContext({ acceptDownloads: true });
  const p = await ctx.newPage();
  await p.goto('https://www.toshin-moshi.com/kyodai_level/', { waitUntil: 'networkidle', timeout: 60000 });
  await p.waitForTimeout(2000);

  const targets = ['基礎データ', '採点基準(理系)', '採点基準（IAIIBIIIC）', '物理 採点基準', '化学 採点基準'];
  for (const label of targets) {
    const link = p.locator(`a:has-text("${label}")`).first();
    if (await link.count() === 0) { console.log('NOLINK', label); continue; }
    try {
      const [dl] = await Promise.all([
        p.waitForEvent('download', { timeout: 25000 }),
        link.click({ modifiers: [] })
      ]);
      const name = 'ts_' + label.replace(/[^\wぁ-んァ-ン一-龥]/g, '') + '.pdf';
      await dl.saveAs(name);
      console.log('OK', label, '->', name, fs.statSync(name).size + 'B');
    } catch (e) {
      // ダウンロードにならずナビゲートした場合
      const url = p.url();
      console.log('NAV?', label, url.slice(0, 110), '|', e.message.slice(0, 50));
      await p.goto('https://www.toshin-moshi.com/kyodai_level/', { waitUntil: 'domcontentloaded' });
      await p.waitForTimeout(1200);
    }
  }
  await b.close();
})();
