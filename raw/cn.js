const { chromium } = require('playwright-core');
(async () => {
  const b = await chromium.launch({ executablePath:'/opt/pw-browsers/chromium', args:['--no-sandbox'] });
  const p = await b.newPage();
  const seen=[];
  p.on('response', r => seen.push([r.status(), r.url()]));
  await p.goto('https://copynight.net/sites/CheckScore', { waitUntil:'networkidle', timeout:70000 });
  await p.waitForTimeout(3000);
  console.log('--- requests ---');
  for (const [s,u] of seen) if(!/\.(png|jpg|jpeg|woff2?|ico|css)$/i.test(u)) console.log(s,u);
  const txt = await p.evaluate(()=>document.body.innerText);
  console.log('--- visible text ---'); console.log(txt.slice(0,3000));
  require('fs').writeFileSync('cn/checkscore.html', await p.content());
  await p.screenshot({path:'cn/cs.png', fullPage:true});
  await b.close();
})();
