const {chromium}=require('playwright-core');
(async()=>{
const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome'});
const pg=await b.newPage({viewport:{width:430,height:900}});
await pg.goto('file://'+process.cwd()+'/kyodai-score-sheet.html');await pg.waitForTimeout(1000);
console.log(JSON.stringify(await pg.evaluate(()=>{
 const W=document.documentElement.clientWidth,out=[];
 const scrollable=e=>{for(let p=e.parentElement;p;p=p.parentElement){
   const o=getComputedStyle(p).overflowX; if(o==='auto'||o==='scroll'||o==='hidden')return true;} return false;};
 document.querySelectorAll('*').forEach(e=>{
   const r=e.getBoundingClientRect();
   if(r.right>W+1&&r.width>0&&e.offsetParent!==null&&!scrollable(e))
     out.push({t:e.tagName,c:(e.className||'')+'',w:Math.round(r.width),right:Math.round(r.right),txt:(e.textContent||'').trim().slice(0,40)});});
 return out.slice(0,6);}),null,1));
await b.close();})();
