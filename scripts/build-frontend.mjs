import {cp, mkdir, readFile, rm, writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';

const root=resolve(import.meta.dirname,'..');
const source=resolve(root,'src/platform/static');
const output=resolve(root,'dist');
const apiBase=(process.env.CATAN_API_BASE_URL||'https://catansim.duckdns.org').replace(/\/$/,'');

if(!/^https:\/\/[a-z0-9.-]+(?::\d+)?$/i.test(apiBase)){
  throw new Error('CATAN_API_BASE_URL must be an HTTPS origin without a path');
}

await rm(output,{recursive:true,force:true});
await mkdir(resolve(output,'static'),{recursive:true});
await cp(source,resolve(output,'static'),{recursive:true});
await cp(resolve(source,'index.html'),resolve(output,'index.html'));
await writeFile(resolve(output,'static/config.js'),`window.CATAN_CONFIG = ${JSON.stringify({apiBaseUrl:apiBase})};\n`);

const index=await readFile(resolve(output,'index.html'),'utf8');
if(!index.includes('/static/config.js'))throw new Error('Frontend config script is missing from index.html');
console.log(`Built static frontend for ${apiBase}`);
