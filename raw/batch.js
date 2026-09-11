const { chromium } = require('playwright-core');
const dir='/root/.claude/uploads/758c6425-18f6-53b4-87c2-064c127a0125/';
const files=require('fs').readdirSync(dir).filter(f=>f.endsWith('_0_0.pdf')).sort();
(async () => {
  const b = await chromium.launch({ executablePath:'/opt/pw-browsers/chromium', args:['--no-sandbox'] });
  for(let i=0;i<files.length;i++){
    const p = await b.newPage({ viewport:{width:1400,height:1900}, deviceScaleFactor:1.5 });
    await p.goto('file://'+dir+files[i]+'#page=1&zoom=55');
    await p.waitForTimeout(5000);
    await p.screenshot({ path:`f_${i}.png` });
    await p.close(); console.log('rendered',i,files[i]);
  }
  await b.close();
})();
