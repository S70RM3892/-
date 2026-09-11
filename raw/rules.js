const {chromium}=require('playwright-core');
(async()=>{
const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome'});
const pg=await b.newPage({viewport:{width:430,height:900}});
await pg.goto('file://'+process.cwd()+'/kyodai-score-sheet.html');await pg.waitForTimeout(800);
console.log(JSON.stringify(await pg.evaluate(()=>{
 const el=document.querySelector('.chip.ct'), hits=[];
 for(const sh of document.styleSheets){let rs;try{rs=sh.cssRules}catch(e){continue}
  const walk=list=>{for(const r of list){
    if(r.cssRules){walk(r.cssRules);continue}
    if(!r.selectorText)continue;
    try{ if(el.matches(r.selectorText)) hits.push(r.selectorText+' {'+r.style.cssText.slice(0,90)+'}');}catch(e){}
  }};
  walk(rs);}
 let n=0;for(const sh of document.styleSheets){try{n+=sh.cssRules.length}catch(e){}}
 return {sheets:document.styleSheets.length,rules:n,hits,styleTags:document.querySelectorAll("style").length};}),null,1));
await b.close();})();
