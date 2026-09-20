import {test,expect} from '@playwright/test';
import {completeBoardFixture} from './complete-board-fixture.js';

test('run, watch, scrub, replay independently, and display responsive results',async({page,context})=>{
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('/');
  await expect(page.getByRole('heading',{name:'Every move. At your own pace.'})).toBeVisible();
  await page.getByRole('button',{name:'Run demo match',exact:true}).click();
  await expect(page.locator('#timeline')).toBeVisible();
  await expect(page.locator('[data-tile]')).toHaveCount(19);
  await expect(page.locator('#timeline')).toHaveValue('0');
  await expect(page.locator('#results')).toBeHidden();
  await page.screenshot({path:'test-results/replay-desktop.png',fullPage:true});
  await page.getByRole('button',{name:'Next event',exact:true}).click();
  await expect(page.locator('#timeline')).toHaveValue('1');
  await page.getByRole('button',{name:'Next turn',exact:true}).click();
  await expect(page.locator('#turnBadge')).toHaveText('TURN 2');
  await page.getByRole('button',{name:'Previous turn',exact:true}).click();
  await expect(page.locator('#timeline')).toHaveValue('0');
  await page.locator('#timeline').fill('6');
  await expect(page.locator('#position')).toHaveText(/^6 \/ /);
  await page.locator('[data-frame="3"]').click();
  await expect(page.locator('#timeline')).toHaveValue('3');
  await page.getByRole('button',{name:'▶ Play',exact:true}).click();
  await expect(page.locator('#timeline')).not.toHaveValue('3');
  await page.getByRole('button',{name:'Ⅱ Pause',exact:true}).click();
  const paused=await page.locator('#timeline').inputValue();
  await page.waitForTimeout(900);
  await expect(page.locator('#timeline')).toHaveValue(paused);
  await page.getByRole('button',{name:'End',exact:true}).click();
  await expect(page.locator('#results')).toBeVisible();
  await expect(page.getByText('No winner',{exact:true})).toBeVisible();
  await expect(page.getByRole('button',{name:'Next event',exact:true})).toBeDisabled();
  const final=await page.locator('#timeline').inputValue();
  const other=await context.newPage();await other.goto(page.url());
  await expect(other.locator('#timeline')).toHaveValue('0');
  await expect(page.locator('#timeline')).toHaveValue(final);
  await other.close();
  await page.getByRole('button',{name:'Beginning',exact:true}).click();
  await expect(page.locator('#players')).toContainText('0 roads');
  await page.reload();await expect(page.locator('#timeline')).toHaveValue('0');
  await page.setViewportSize({width:390,height:844});
  await page.screenshot({path:'test-results/replay-mobile.png',fullPage:true});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBeTruthy();
  await page.getByRole('link',{name:'Matches',exact:true}).click();
  await expect(page.getByRole('button',{name:'Watch match →'}).first()).toBeVisible();
  expect(errors).toEqual([]);
});

test('four participants select a saved bot, ready up and launch a recorded room match',async({page,browser})=>{
  const suffix=Date.now().toString(36),bot=`Demo-${suffix}`;
  await page.goto('/#bots');
  await page.getByRole('button',{name:'+ Add bot version',exact:true}).click();
  await page.getByRole('textbox',{name:'Bot name',exact:true}).fill(bot);
  await page.getByRole('textbox',{name:'Version',exact:true}).fill('v1');
  await page.getByRole('button',{name:'Save bot version',exact:true}).click();
  await expect(page.getByRole('heading',{name:bot,exact:true})).toBeVisible();
  await page.getByRole('link',{name:'Rooms',exact:true}).click();
  await page.getByRole('button',{name:'+ Create room',exact:true}).click();
  await page.getByRole('textbox',{name:'Room name',exact:true}).fill(`Test table ${suffix}`);
  await page.getByRole('textbox',{name:'Your name',exact:true}).fill('Alice');
  await page.locator('#roomForm').getByRole('button',{name:'Create room',exact:true}).click();
  await expect(page.locator('[data-seat-bot]')).toBeVisible();
  const url=page.url();
  await page.locator('[data-seat-bot]').selectOption(`${bot}-v1`);
  await page.getByRole('button',{name:'Mark ready',exact:true}).click();
  await expect(page.getByRole('button',{name:'Not ready',exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Not ready',exact:true}).click();
  await expect(page.getByRole('button',{name:'Mark ready',exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Mark ready',exact:true}).click();
  const contexts=[];
  try{
    for(const who of ['Bob','Carol','Dave']){
      const ctx=await browser.newContext();contexts.push(ctx);const participant=await ctx.newPage();
      await participant.goto(url);await participant.getByRole('textbox',{name:'Your local player name'}).fill(who);
      await participant.getByRole('textbox',{name:'Your local player name'}).press('Tab');
      await participant.getByRole('button',{name:'Join this room',exact:true}).first().click();
      await participant.locator('[data-seat-bot]').selectOption(`${bot}-v1`);
      await participant.getByRole('button',{name:'Mark ready',exact:true}).click();
      await expect(participant.getByRole('button',{name:'Not ready',exact:true})).toBeVisible();
    }
    await page.reload();
    await expect(page.getByRole('button',{name:'Simulate match →',exact:true})).toBeEnabled();
    await page.screenshot({path:'test-results/room-ready.png',fullPage:true});
    await page.getByRole('button',{name:'Simulate match →',exact:true}).click();
    await expect(page.locator('#timeline')).toBeVisible();
    await expect(page.locator('#players')).toContainText('Alice');
    await expect(page.locator('#players')).toContainText('Dave');
    await expect(page.locator('#players')).toContainText(bot);
    await page.goto(url);
    await expect(page.getByRole('button',{name:'Watch match →',exact:true})).toBeVisible();
  }finally{for(const ctx of contexts)await ctx.close();}
});

test('user names are rendered as text, and missing matches have a recoverable error',async({page,request})=>{
  const bot=`<img src=x onerror=alert(1)>-${Date.now()}`;
  await request.post('/bots/upload',{data:{bot_name:bot,bot_version:'v1'}});
  let alert=false;page.on('dialog',async d=>{alert=true;await d.dismiss();});
  await page.goto('/#bots');
  await expect(page.getByRole('heading',{name:bot,exact:true})).toBeVisible();
  expect(await page.locator('.card img').count()).toBe(0);expect(alert).toBe(false);
  await page.goto('/#match/game-missing');
  await expect(page.getByRole('heading',{name:'Something needs another look.'})).toBeVisible();
  await expect(page.getByRole('button',{name:'Try again'})).toBeVisible();
});

test('complete geometry contract renders roads, cities, ports and reversible positions',async({page})=>{
  const {metadata,replay}=completeBoardFixture();
  expect(replay.geometry.vertices).toHaveLength(54);
  expect(replay.geometry.edges).toHaveLength(72);
  expect(replay.geometry.ports).toHaveLength(9);
  await page.route('**/games/game-fixture',route=>route.fulfill({json:metadata}));
  await page.route('**/game/game-fixture/replay',route=>route.fulfill({json:replay}));
  await page.goto('/#match/game-fixture');
  await expect(page.locator('[data-tile]')).toHaveCount(19);
  await expect(page.locator('#topology')).toBeHidden();
  await page.getByRole('button',{name:'Next event',exact:true}).click();
  await expect(page.locator('#players')).toContainText('1 cities');
  await expect(page.locator('#board line[stroke-width="7"]')).toHaveCount(4);
  await expect(page.locator('#board text').filter({hasText:/3:1|2:1/})).toHaveCount(9);
  await page.screenshot({path:'test-results/complete-geometry-fixture.png',fullPage:true});
  await page.getByRole('button',{name:'Previous event',exact:true}).click();
  await expect(page.locator('#board line[stroke-width="7"]')).toHaveCount(0);
  await expect(page.locator('#players')).toContainText('0 cities');
});
