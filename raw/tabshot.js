const {chromium}=require('playwright-core');
(async()=>{
const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome'});
const pg=await b.newPage({viewport:{width:430,height:1100},deviceScaleFactor:2});
const errs=[];pg.on('pageerror',e=>errs.push(e.message));
await pg.goto('file://'+process.cwd()+'/kyodai-map.html');await pg.waitForTimeout(1200);
for(const [t,f] of [['t-p','pan-p'],['t-e','pan-e'],['t-k','pan-k'],['t-c','pan-c']]){
  await pg.click('#'+t); await pg.waitForTimeout(300);
  const r=await pg.evaluate(f=>({vis:!document.getElementById(f).hidden,
    ow:document.documentElement.scrollWidth>document.documentElement.clientWidth,
    sw:document.documentElement.scrollWidth,
    h:Math.round(document.getElementById(f).getBoundingClientRect().height)}),f);
  console.log(t,JSON.stringify(r));
  await pg.screenshot({path:'tab-'+t+'.png',fullPage:true});
}
console.log('errs',JSON.stringify(errs));
await b.close();})();
