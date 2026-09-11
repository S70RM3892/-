const {chromium}=require('playwright-core');
(async()=>{
const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome'});
for(const w of [400,430,760]){
 const pg=await b.newPage({viewport:{width:w,height:700}});
 await pg.goto('file://'+process.cwd()+'/kyodai-map.html');await pg.waitForTimeout(700);
 console.log(w,JSON.stringify(await pg.evaluate(()=>{
  const st=document.querySelector('.subtabs');
  return {fits:st.scrollWidth<=st.clientWidth+1, sw:st.scrollWidth, cw:st.clientWidth,
    ow:document.documentElement.scrollWidth>document.documentElement.clientWidth};})));
 await pg.close();
}
await b.close();})();
