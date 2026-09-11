const {chromium}=require('playwright-core');
(async()=>{
const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome'});
const pg=await b.newPage({viewport:{width:2200,height:1560},deviceScaleFactor:2});
const [file,page,out]=process.argv.slice(2);
await pg.goto('file://'+process.cwd()+'/'+file+'#page='+page+'&zoom=page-fit&toolbar=0&navpanes=0&view=Fit');
await pg.waitForTimeout(7000);
await pg.screenshot({path:out});
await b.close();})();
