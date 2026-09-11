const {chromium}=require('playwright-core');
(async()=>{
const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome'});
const pg=await b.newPage({viewport:{width:430,height:900}});
await pg.goto('file://'+process.cwd()+'/kyodai-score-sheet.html');await pg.waitForTimeout(600);
const sels=await pg.evaluate(()=>{const o=[];
 for(const sh of document.styleSheets){let rs;try{rs=sh.cssRules}catch(e){continue}
   for(const r of rs) o.push(r.selectorText||('@'+(r.conditionText||r.name||r.cssText.slice(0,30))));}
 return o;});
console.log(sels.length); console.log(sels.slice(0,200).join('\n'));
await b.close();})();
