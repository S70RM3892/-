const { chromium } = require('playwright-core');
(async () => {
  const [src,pg,out] = process.argv.slice(2);
  const b = await chromium.launch({ executablePath:'/opt/pw-browsers/chromium', args:['--no-sandbox'] });
  const p = await b.newPage({ viewport:{width:1700,height:1220}, deviceScaleFactor:1 });
  await p.goto('file://'+src+'#page='+pg+'&zoom=page-fit&toolbar=0');
  await p.waitForTimeout(5000);
  await p.screenshot({ path:out });
  console.log('ok'); await b.close();
})();
