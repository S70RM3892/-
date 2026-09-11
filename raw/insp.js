const {chromium}=require('playwright-core');
(async()=>{
const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome'});
const pg=await b.newPage({viewport:{width:760,height:1200}});
await pg.goto('file://'+process.cwd()+'/kyodai-math-map.html');await pg.waitForTimeout(800);
console.log(JSON.stringify(await pg.evaluate(()=>{
 const o=[];
 document.querySelectorAll('section').forEach(s=>{
   const r=s.getBoundingClientRect();
   o.push({id:s.id,w:Math.round(r.width),h:Math.round(r.height)});
 });
 const li=document.querySelector('.steps li');
 const p=document.querySelector('#s-junjo p');
 return {sections:o, wrapW:Math.round(document.querySelector('.wrap').getBoundingClientRect().width),
   liW:li?Math.round(li.getBoundingClientRect().width):null,
   pW:p?Math.round(p.getBoundingClientRect().width):null,
   bodyW:Math.round(document.body.getBoundingClientRect().width)};
}),null,1));
await b.close();})();
