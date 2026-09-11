const {chromium}=require('playwright-core');
(async()=>{
const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome'});
const pg=await b.newPage({viewport:{width:430,height:900}});
await pg.goto('file://'+process.cwd()+'/kyodai-score-sheet.html');await pg.waitForTimeout(1000);
console.log(JSON.stringify(await pg.evaluate(()=>{
 const out=[];const W=document.documentElement.clientWidth;
 document.querySelectorAll('*').forEach(e=>{
   const r=e.getBoundingClientRect();
   if(r.right>W+1&&r.width>0&&e.offsetParent!==null)
     out.push({t:e.tagName,c:(e.className||'').toString().slice(0,30),w:Math.round(r.width),right:Math.round(r.right)});});
 return [...document.querySelectorAll("table")].map(e=>({w:Math.round(e.getBoundingClientRect().width),parent:(e.parentElement.className||"none")+"",head:(e.querySelector("th")||{}).textContent}));}),null,1));
await b.close();})();
