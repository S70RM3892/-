const {chromium}=require('playwright-core');
(async()=>{
const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome'});const pg=await b.newPage({viewport:{width:430,height:900}});
const errs=[];pg.on('pageerror',e=>errs.push(String(e)));pg.on('console',m=>{if(m.type()==='error')errs.push(m.text())});
await pg.goto('file://'+process.cwd()+'/kyodai-score-sheet.html');
await pg.waitForTimeout(1200);
const r=await pg.evaluate(()=>{
  const tabs=[...document.querySelectorAll('.tab')].map(t=>t.textContent);
  return {tabs,
   det:!!document.querySelector('details'),
   detTxt:document.querySelector('details summary')?.textContent.slice(0,30),
   why:!!document.getElementById('p-why'),
   ow:document.documentElement.scrollWidth>document.documentElement.clientWidth,
   sw:document.documentElement.scrollWidth,
   need:document.getElementById('ro-need')?.textContent,
   p:document.getElementById('ro-p')?.textContent};
});
// tab switch
await pg.click('#t-log');await pg.waitForTimeout(300);
const t2=await pg.evaluate(()=>({logVis:!document.getElementById('p-log').hidden,desHid:document.getElementById('p-design').hidden,
  ow:document.documentElement.scrollWidth>document.documentElement.clientWidth}));
console.log(JSON.stringify({...r,...t2,errs},null,1));
await b.close();})();
