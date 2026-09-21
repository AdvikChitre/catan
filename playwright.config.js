import {defineConfig} from '@playwright/test';
import {mkdtempSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';

const data=mkdtempSync(join(tmpdir(),'catan-browser-'));
export default defineConfig({
  testDir:'tests/browser', fullyParallel:false, workers:1, timeout:45000,
  use:{baseURL:'http://127.0.0.1:8011',viewport:{width:1440,height:1050},screenshot:'only-on-failure',trace:'retain-on-failure'},
  webServer:{command:'python -m uvicorn src.platform.server:app --host 127.0.0.1 --port 8011',url:'http://127.0.0.1:8011',reuseExistingServer:false,
    env:{CATAN_DB_URL:`sqlite:///${join(data,'browser.db')}`,CATAN_REPLAY_DIR:join(data,'replays')},timeout:30000},
});
