import test from 'node:test';
import assert from 'node:assert/strict';
import {Playback} from '../src/platform/static/playback.js';

const frames=[1,1,1,2,2,3,3].map((turn_number,i)=>({state:{turn_number},sequence:i}));
test('seek clamps to the recording, and backward stepping does not wrap',()=>{
  const p=new Playback(frames);assert.equal(p.step(-1).sequence,0);
  assert.equal(p.seek(999).sequence,6);assert.ok(p.atEnd);
  assert.equal(p.step(1).sequence,6);assert.equal(p.step(-1).sequence,5);
  assert.equal(p.seek(0).sequence,0);assert.equal(frames[0].state.turn_number,1);
});
test('turn navigation reaches the beginning of adjacent recorded turns',()=>{
  const p=new Playback(frames);assert.equal(p.turn(1).sequence,3);
  p.seek(4);assert.equal(p.turn(-1).sequence,0);
  p.seek(6);assert.equal(p.turn(-1).sequence,3);
  assert.equal(p.turn(1).sequence,5);assert.equal(p.turn(1).sequence,6);
});
