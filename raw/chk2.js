const {chromium}=require('playwright-core');
(async()=>{
const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome'});
const pg=await b.newPage({viewport:{width:430,height:900}});
pg.on('pageerror',e=>console.log('ERR>',e.stack));
await pg.goto('file://'+process.cwd()+'/kyodai-score-sheet.html');
await pg.waitForTimeout(1500);
await b.close();})();
