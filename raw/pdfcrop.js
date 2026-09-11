const { chromium } = require('playwright-core');
(async () => {
  const [src,pg,out,x,y,w,h,dsf] = process.argv.slice(2);
  const b = await chromium.launch({ executablePath:'/opt/pw-browsers/chromium', args:['--no-sandbox'] });
  const p = await b.newPage({ viewport:{width:1400,height:1000}, deviceScaleFactor:+(dsf||3) });
  await p.goto('file://'+src+'#page='+pg+'&view=Fit&toolbar=0');
  await p.waitForTimeout(5000);
  await p.screenshot({ path:out, clip:{x:+x,y:+y,width:+w,height:+h} });
  console.log('ok',out); await b.close();
})();
