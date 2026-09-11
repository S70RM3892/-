const { chromium } = require('playwright-core');
(async () => {
  const b = await chromium.launch({ executablePath:'/opt/pw-browsers/chromium', args:['--no-sandbox'] });
  const p = await b.newPage({ viewport:{width:1000,height:1500}, deviceScaleFactor:1.4 });
  const errs=[]; p.on('pageerror',e=>errs.push(e.message)); p.on('console',m=>{if(m.type()==='error')errs.push('C:'+m.text());});
  await p.goto('file://'+process.cwd()+'/kyodai-score-sheet.html',{waitUntil:'load'});
  await p.waitForTimeout(1500);
  console.log('errors:', errs.length?errs:'none');
  // 記録タブ
  await p.click('#t-log'); await p.waitForTimeout(600);
  console.log('例の行 z =', await p.$eval('[data-z]', e=>e.textContent));
  console.log('Phase5 実測z=', await p.$eval('#ro-z',e=>e.textContent), '| σ_z=', await p.$eval('#ro-sz',e=>e.textContent),
              '| σ_z注=', await p.$eval('#ro-szn',e=>e.textContent), '| P=', await p.$eval('#ro-p',e=>e.textContent));
  // 2行目に順位を入れて実測σ_zに切り替わるか
  const rows = await p.$$('.lg[data-rid]');
  const inputs = await rows[1].$$('input');
  await inputs[5].fill('130'); await inputs[6].fill('398');
  await p.waitForTimeout(500);
  console.log('2件入力後 → z̄=', await p.$eval('#ro-z',e=>e.textContent), '| σ_z=', await p.$eval('#ro-sz',e=>e.textContent),
              '|', await p.$eval('#ro-szn',e=>e.textContent), '| P=', await p.$eval('#ro-p',e=>e.textContent));
  await p.screenshot({path:'v_log.png', clip:{x:0,y:0,width:1000,height:1050}});
  await b.close();
})();
