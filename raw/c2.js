const {chromium}=require('playwright-core');
(async()=>{
const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome'});
const pg=await b.newPage({viewport:{width:430,height:900}});
await pg.goto('file://'+process.cwd()+'/kyodai-score-sheet.html');await pg.waitForTimeout(1200);
console.log(JSON.stringify(await pg.evaluate(()=>{
 return [...document.querySelectorAll('.chip')].slice(0,3).map(c=>({
   html:c.outerHTML.slice(0,120), w:Math.round(c.getBoundingClientRect().width),
   disp:getComputedStyle(c).display, ws:getComputedStyle(c).whiteSpace,
   parentHTML:c.parentElement.outerHTML.slice(0,180)}));}),null,1));
await b.close();})();
