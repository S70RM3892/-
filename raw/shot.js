const {chromium}=require('playwright-core');
(async()=>{
const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome'});
const f=process.argv[2], w=+(process.argv[3]||760);
const pg=await b.newPage({viewport:{width:w,height:1200},deviceScaleFactor:2});
const errs=[];pg.on('pageerror',e=>errs.push(e.message));
await pg.goto('file://'+process.cwd()+'/'+f);await pg.waitForTimeout(1500);
const r=await pg.evaluate(()=>({ow:document.documentElement.scrollWidth>document.documentElement.clientWidth,
  sw:document.documentElement.scrollWidth, rows:document.querySelectorAll('#map-b tr').length,
  prof:document.querySelectorAll('#prof .r').length, mx:document.querySelectorAll('#mx-b tr').length}));
console.log(JSON.stringify({...r,errs}));
await pg.screenshot({path:f.replace('.html','.png'),fullPage:true});
await b.close();})();
