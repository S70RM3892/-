const {chromium}=require('playwright-core');
(async()=>{
const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome'});
const pg=await b.newPage({viewport:{width:430,height:900}});
await pg.goto('file://'+process.cwd()+'/kyodai-score-sheet.html');await pg.waitForTimeout(1200);
console.log(JSON.stringify(await pg.evaluate(()=>{
 const path=e=>{const p=[];for(;e&&e!==document.body;e=e.parentElement)p.unshift(e.tagName+'.'+((e.className||'')+'').trim().replace(/\s+/g,'.'));return p.join(' > ');};
 return [...document.querySelectorAll('.chip.ct')].slice(0,2).map(c=>({
   w:Math.round(c.getBoundingClientRect().width),disp:getComputedStyle(c).display,
   path:path(c), html:c.outerHTML.slice(0,100),
   parentDisp:getComputedStyle(c.parentElement).display,
   parentW:Math.round(c.parentElement.getBoundingClientRect().width)}));}),null,1));
await b.close();})();
