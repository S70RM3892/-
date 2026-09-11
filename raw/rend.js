const {chromium}=require('playwright-core');
(async()=>{
const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome'});
const pg=await b.newPage({viewport:{width:1500,height:2000},deviceScaleFactor:2});
const [file,page,out]=process.argv.slice(2);
await pg.goto('file://'+process.cwd()+'/'+file+'#page='+page+'&zoom=page-fit&toolbar=0&navpanes=0');
await pg.waitForTimeout(6000);
await pg.screenshot({path:out});
await b.close();})();
