const { chromium } = require('playwright-core');
const dir='/root/.claude/uploads/758c6425-18f6-53b4-87c2-064c127a0125/';
const f=process.argv[2], out=process.argv[3], z=process.argv[4]||'50';
(async () => {
  const b = await chromium.launch({ executablePath:'/opt/pw-browsers/chromium', args:['--no-sandbox'] });
  const p = await b.newPage({ viewport:{width:1400,height:1900}, deviceScaleFactor:1.5 });
  await p.goto('file://'+dir+f+'#page=1&zoom='+z);
  await p.waitForTimeout(5000);
  await p.screenshot({ path:out });
  await b.close(); console.log('ok',out);
})();
