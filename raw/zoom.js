const { chromium } = require('playwright-core');
(async () => {
  const [src,pg,out,x,y,w,h] = process.argv.slice(2);
  const b = await chromium.launch({ executablePath:'/opt/pw-browsers/chromium', args:['--no-sandbox'] });
  const p = await b.newPage({ viewport:{width:1700,height:1220}, deviceScaleFactor:+(process.argv[9]||2) });
  await p.goto('file://'+src+'#page='+pg+'&zoom=page-fit&toolbar=0');
  await p.waitForTimeout(5000);
  await p.screenshot({ path:out, clip:{x:+x,y:+y,width:+w,height:+h} });
  console.log('ok'); await b.close();
})();
