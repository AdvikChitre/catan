/** Pure playback navigation, independent of the DOM and simulator rules. */
export class Playback {
  constructor(frames){this.frames=frames;this.index=0;}
  seek(index){this.index=Math.max(0,Math.min(this.frames.length-1,Number(index)||0));return this.frames[this.index];}
  step(direction){return this.seek(this.index+direction);}
  turn(direction){
    const current=this.frames[this.index].state.turn_number;
    if(direction>0){const next=this.frames.findIndex((f,i)=>i>this.index&&f.state.turn_number!==current);return this.seek(next<0?this.frames.length-1:next);}
    for(let i=this.index-1;i>=0;i--)if(this.frames[i].state.turn_number!==current){const previous=this.frames[i].state.turn_number;while(i>0&&this.frames[i-1].state.turn_number===previous)i--;return this.seek(i);}
    return this.seek(0);
  }
  get atEnd(){return this.index===this.frames.length-1;}
}
