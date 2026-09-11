const {chromium}=require('playwright-core');
(async()=>{
const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome'});
const pg=await b.newPage({viewport:{width:430,height:900}});
await pg.goto('file://'+process.cwd()+'/kyodai-score-sheet.html');await pg.waitForTimeout(1000);
console.log(JSON.stringify(await pg.evaluate(()=>{
 const c=document.querySelector('.chip.ct');
 const cs=getComputedStyle(c), p=c.parentElement, ps=getComputedStyle(p);
 return {chip:{w:c.getBoundingClientRect().width,display:cs.display,flex:cs.flex,pos:cs.position},
   parent:{cls:p.className+'',display:ps.display,w:p.getBoundingClientRect().width,
           gtc:ps.gridTemplateColumns, ga:ps.gridArea},
   grand:{cls:p.parentElement.className+'',display:getComputedStyle(p.parentElement).display,
          gtc:getComputedStyle(p.parentElement).gridTemplateColumns,
          w:p.parentElement.getBoundingClientRect().width}};}),null,1));
await b.close();})();
