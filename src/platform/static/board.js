const NS = 'http://www.w3.org/2000/svg';
export const playerColors = ['#c9663b', '#4b83a0', '#9273aa', '#c5a344'];
const terrain = {WOOD:'#416e50', BRICK:'#b8714e', SHEEP:'#8fa65b', WHEAT:'#c5a354', ORE:'#7a8a8d', DESERT:'#c7b58a'};
const color = id => playerColors[Number((id || 'P1').slice(1)) - 1] || '#708070';
function svgNode(tag, attrs={}, text) {
  const el = document.createElementNS(NS, tag);
  for (const [key, value] of Object.entries(attrs)) el.setAttribute(key, value);
  if (text !== undefined) el.textContent = text;
  return el;
}
function label(parent, x, y, text, attrs={}) {
  parent.append(svgNode('text', {x,y,'text-anchor':'middle',...attrs}, text));
}
function house(parent, x, y, owner, city=false, size=9) {
  const group = svgNode('g', {transform:`translate(${x} ${y}) scale(${size/9})`});
  group.append(svgNode('path',{d:city?'M-13 9V-3L-6-10 1-3V0H8V-8H14V9Z':'M-9 8V-2L0-10 9-2V8Z',fill:color(owner),stroke:'#fff8e8','stroke-width':2}));
  parent.append(group);
}

export class Board {
  constructor(container, geometry) {
    this.container = container; this.geometry=geometry; this.zoom=1; this.pan={x:0,y:0};
    this.svg=svgNode('svg',{viewBox:'-270 -225 540 450',role:'img','aria-label':'Recorded Catan board',class:'board-svg'});
    this.scene=svgNode('g'); this.svg.append(this.scene); container.replaceChildren(this.svg);
    this.svg.addEventListener('pointerdown', e=>{this.drag={cx:e.clientX,cy:e.clientY,px:this.pan.x,py:this.pan.y};this.svg.setPointerCapture(e.pointerId);});
    this.svg.addEventListener('pointermove',e=>{if(!this.drag)return;const ratio=Math.max(540/this.svg.clientWidth,450/this.svg.clientHeight);
      this.pan={x:this.drag.px+(e.clientX-this.drag.cx)*ratio,y:this.drag.py+(e.clientY-this.drag.cy)*ratio};this.transform();});
    for(const type of ['pointerup','pointercancel','lostpointercapture'])this.svg.addEventListener(type,()=>{this.drag=null;});
    this.svg.addEventListener('wheel',e=>{e.preventDefault();this.setZoom(this.zoom*(e.deltaY<0?1.12:1/1.12));},{passive:false});
  }
  transform(){this.scene.setAttribute('transform',`translate(${this.pan.x} ${this.pan.y}) scale(${this.zoom})`);}
  setZoom(n){this.zoom=Math.max(.6,Math.min(3,n));this.transform();}
  reset(){this.zoom=1;this.pan={x:0,y:0};this.transform();}
  render(state){
    this.scene.replaceChildren();
    const g=this.geometry;
    const vertices=new Map();
    if(g.valid_hex_topology){
      const xs=g.vertices.map(v=>v.x),ys=g.vertices.map(v=>v.y);
      const xmin=Math.min(...xs),xmax=Math.max(...xs),ymin=Math.min(...ys),ymax=Math.max(...ys);
      const scale=Math.min(460/(xmax-xmin||1),410/(ymax-ymin||1));
      g.vertices.forEach(v=>vertices.set(v.id,[(v.x-(xmin+xmax)/2)*scale,(v.y-(ymin+ymax)/2)*scale]));
    }
    for(const tile of g.tiles){
      const data=state.tiles[tile.id];if(!data)continue;
      let x=Math.sqrt(3)*51*(tile.x+tile.y/2), y=1.5*51*tile.y;
      let points;
      if(g.valid_hex_topology){
        const corners=tile.vertices.map(id=>vertices.get(id));
        x=corners.reduce((s,p)=>s+p[0],0)/corners.length;y=corners.reduce((s,p)=>s+p[1],0)/corners.length;
        points=corners.sort((a,b)=>Math.atan2(a[1]-y,a[0]-x)-Math.atan2(b[1]-y,b[0]-x));
      } else points=Array.from({length:6},(_,i)=>[x+50*Math.cos((i*60-30)*Math.PI/180),y+50*Math.sin((i*60-30)*Math.PI/180)]);
      const group=svgNode('g',{'data-tile':tile.id});
      group.append(svgNode('title',{},`${tile.id}: ${data.resource}, ${data.number || 'no number'}${data.robber?', robber':''}`));
      group.append(svgNode('polygon',{points:points.map(p=>p.join(',')).join(' '),fill:terrain[data.resource]||terrain.DESERT}));
      // Small terrain silhouettes keep the board legible without external assets.
      if(data.resource==='WOOD')for(const dx of [-14,0,14])group.append(svgNode('path',{d:`M${x+dx-7} ${y-16}l7-15 7 15Z`,fill:'#244e39',opacity:.65}));
      if(data.resource==='ORE')group.append(svgNode('path',{d:`M${x-22} ${y-16}l14-18 13 18 8-11 12 15Z`,fill:'#4e666b',opacity:.65}));
      if(data.resource==='WHEAT')for(const dx of [-12,0,12])group.append(svgNode('path',{d:`M${x+dx} ${y-15}v-16m0 9l-5-5m5 1l5-5`,stroke:'#f7db8a','stroke-width':2,fill:'none'}));
      if(data.resource==='SHEEP')group.append(svgNode('ellipse',{cx:x,cy:y-24,rx:14,ry:8,fill:'#e8edcd',opacity:.8}));
      if(data.resource==='BRICK')for(const dx of [-12,0,12])group.append(svgNode('rect',{x:x+dx-5,y:y-29,width:10,height:7,rx:1,fill:'#dd9b74'}));
      if(data.number){group.append(svgNode('circle',{cx:x,cy:y+4,r:17,fill:'#fff6df',stroke:'#fff9e9','stroke-width':1}));
        label(group,x,y+9,data.number,{class:'tile-number',style:[6,8].includes(data.number)?'fill:#b45339':''});}
      label(group,x,y+33,data.resource,{class:'tile-label'});
      if(data.robber){group.append(svgNode('path',{d:`M${x+20} ${y+15}l4-18h8l4 18Z`,fill:'#24372f',stroke:'#eee7d2','stroke-width':1.5}));group.append(svgNode('circle',{cx:x+28,cy:y-8,r:6,fill:'#24372f',stroke:'#eee7d2','stroke-width':1.5}));}
      this.scene.append(group);
    }
    if(g.valid_hex_topology){
      for(const edge of g.edges){const owner=state.roads[edge.id];if(!owner)continue;const [a,b]=edge.vertices.map(id=>vertices.get(id));
        const line=svgNode('line',{x1:a[0],y1:a[1],x2:b[0],y2:b[1],stroke:color(owner),'stroke-width':7,'stroke-linecap':'round'});line.append(svgNode('title',{},`${edge.id} · ${owner}`));this.scene.append(line);}
      for(const [id,b] of Object.entries(state.buildings)){const p=vertices.get(id);if(p)house(this.scene,...p,b.owner,b.type==='CITY');}
      for(const port of g.ports){const ends=port.vertices.map(id=>vertices.get(id));const x=(ends[0][0]+ends[1][0])/2,y=(ends[0][1]+ends[1][1])/2;
        const distance=Math.hypot(x,y)||1;const px=x+x/distance*28,py=y+y/distance*28;
        this.scene.append(svgNode('line',{x1:x,y1:y,x2:px,y2:py,stroke:'#7a8c7c','stroke-width':1}));
        label(this.scene,px,py,port.type==='THREE_TO_ONE'?'3:1':`2:1 ${port.type.replace('TWO_TO_ONE_','').toLowerCase()}`,{'font-size':7,fill:'#354d3e'});}
    }
  }
}

export function renderTopology(container,geometry,state){
  if(geometry.valid_hex_topology){container.hidden=true;return;}
  container.hidden=false;
  let svg=container.querySelector('svg');if(!svg){svg=svgNode('svg',{viewBox:'-310 -205 620 410',role:'img','aria-label':'Simulator vertex and road topology, schematic layout'});container.append(svg);}
  svg.replaceChildren();const coords=new Map();
  geometry.vertices.forEach((v,i)=>{const a=2*Math.PI*i/geometry.vertices.length-Math.PI/2;coords.set(v.id,[Math.cos(a)*250,Math.sin(a)*158]);});
  const seen=new Map();
  for(const edge of geometry.edges){const [a,b]=edge.vertices.map(id=>coords.get(id));const key=edge.vertices.join(':');const repeated=seen.has(key);seen.set(key,true);const owner=state.roads[edge.id];
    const mid=[(a[0]+b[0])/2,(a[1]+b[1])/2];const path=svgNode('path',{d:repeated?`M${a} Q${mid[0]*.80},${mid[1]*.80} ${b}`:`M${a} L${b}`,fill:'none',stroke:owner?color(owner):'#d3ddcf','stroke-width':owner?4:1.5});
    path.append(svgNode('title',{},`${edge.id}: ${edge.vertices.join(' ↔ ')} · ${owner||'empty'}`));svg.append(path);
  }
  geometry.vertices.forEach(v=>{const [x,y]=coords.get(v.id),b=state.buildings[v.id];if(b)house(svg,x,y,b.owner,b.type==='CITY',6);else svg.append(svgNode('circle',{cx:x,cy:y,r:2.5,fill:'#bccab6'}));
    label(svg,x*1.09,y*1.11,v.id,{'font-size':7,fill:'#65775f'});});
  label(svg,0,-12,'Recorded roads & buildings',{'font-size':14,fill:'#314f3c'});
  label(svg,0,10,'Schematic only · simulator topology is provisional',{'font-size':9,fill:'#7a8871'});
}
