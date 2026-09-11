const { chromium } = require('playwright-core');
const dir='/root/.claude/uploads/758c6425-18f6-53b4-87c2-064c127a0125/';
(async () => {
  const b = await chromium.launch({ executablePath:'/opt/pw-browsers/chromium', args:['--no-sandbox'] });
  const p = await b.newPage({ viewport:{width:1400,height:1900}, deviceScaleFactor:1.5 });
  await p.goto('file://'+dir+process.argv[2]+'#page=1&zoom=55');
  await p.waitForTimeout(9000);
  await p.screenshot({ path:process.argv[3] });
  await b.close(); console.log('ok',process.argv[3]);
})();
