const {chromium}=require('playwright-core');
(async()=>{
const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome'});
const pg=await b.newPage({viewport:{width:430,height:1000},deviceScaleFactor:2});
const errs=[];pg.on('pageerror',e=>errs.push(e.message));
await pg.goto('file://'+process.cwd()+'/kyodai-score-sheet.html');await pg.waitForTimeout(1200);
await pg.click('#t-drill');await pg.waitForTimeout(400);
// 入力してみる
await pg.evaluate(()=>{
  const rows=document.querySelectorAll('.dg[data-q]');
  const sc=[30,28,10,22,25,0], tm=[18,22,30,25,28,12];
  rows.forEach((r,i)=>{
    const s=r.querySelector('input[data-f="s"]'), t=r.querySelector('input[data-f="t"]');
    s.value=sc[i]; s.dispatchEvent(new Event('input',{bubbles:true}));
    t.value=tm[i]; t.dispatchEvent(new Event('input',{bubbles:true}));
  });
  const sk=rows[5].querySelector('input[data-f="skip"]'); sk.checked=true; sk.dispatchEvent(new Event('change',{bubbles:true}));
});
await pg.waitForTimeout(500);
console.log(JSON.stringify({
 ow:await pg.evaluate(()=>document.documentElement.scrollWidth>document.documentElement.clientWidth),
 rate:await pg.textContent('#dr-rate'), n:await pg.textContent('#dr-n'),
 eff:await pg.textContent('#dr-eff'), skip:await pg.textContent('#dr-skip'),
 skipn:await pg.textContent('#dr-skipn'),
 bands:await pg.evaluate(()=>[...document.querySelectorAll('#dr-band .r')].map(x=>x.textContent.trim())),
 fields:await pg.evaluate(()=>[...document.querySelectorAll('#dr-field tr')].slice(0,4).map(x=>x.textContent.trim())),
 errs}));
await pg.screenshot({path:'drill.png',fullPage:true});
await b.close();})();
