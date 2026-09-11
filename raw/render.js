const { chromium } = require('playwright-core');
const dir='/root/.claude/uploads/758c6425-18f6-53b4-87c2-064c127a0125/';
const files=require('fs').readdirSync(dir).filter(f=>f.endsWith('_0_0.pdf')).sort();
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium', args: ['--no-sandbox'] });
  for (let i=0;i<files.length;i++){
    const p = await b.newPage({ viewport:{width:1100,height:1560}, deviceScaleFactor:2 });
    await p.goto('file://'+dir+files[i]+'#page=1&view=Fit');
    await p.waitForTimeout(4500);
    // ページ全体のうち下半分＝科目別基本情報のあたり
    await p.screenshot({ path:`t_${i}.png`, clip:{x:270,y:120,width:830,height:700} });
    console.log('ok',i,files[i]);
    await p.close();
  }
  await b.close();
})();
