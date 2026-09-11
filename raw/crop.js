const {chromium}=require('playwright-core');
(async()=>{
const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome'});
const pg=await b.newPage({viewport:{width:700,height:1000},deviceScaleFactor:2});
await pg.goto('file://'+process.cwd()+'/kyodai-kyoten.html');await pg.waitForTimeout(1200);
const el=await pg.$('#s-senbatsu');
await el.screenshot({path:'senbatsu.png'});
await b.close();})();
