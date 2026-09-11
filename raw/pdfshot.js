const { chromium } = require('playwright-core');
(async () => {
  const jobs = process.argv.slice(2).map(a=>a.split('::')); // path::out::page
  const b = await chromium.launch({ executablePath:'/opt/pw-browsers/chromium', args:['--no-sandbox'] });
  for (const [src,out,pg='1'] of jobs){
    const p = await b.newPage({ viewport:{width:1500,height:2050}, deviceScaleFactor:2 });
    await p.goto('file://'+src+'#page='+pg+'&view=Fit&toolbar=0');
    await p.waitForTimeout(5000);
    await p.screenshot({ path:out });
    console.log('ok', out);
    await p.close();
  }
  await b.close();
})();
