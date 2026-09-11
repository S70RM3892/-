const { chromium } = require('playwright-core');
const dir='/root/.claude/uploads/758c6425-18f6-53b4-87c2-064c127a0125/';
(async () => {
  const b = await chromium.launch({ executablePath:'/opt/pw-browsers/chromium', args:['--no-sandbox'] });
  const p = await b.newPage({ viewport:{width:1500,height:1900}, deviceScaleFactor:2 });
  await p.goto('file://'+dir+process.argv[2]+'#page=1&zoom=115');
  await p.waitForTimeout(5000);
  await p.screenshot({ path:process.argv[3], clip:{x:430,y:1180,width:1070,height:400} });
  await b.close(); console.log('ok');
})();
