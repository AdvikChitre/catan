// Presentation-contract fixture only: this is not a simulator-generated match.
export function completeBoardFixture(){
  const vertices=[],edges=[],tiles=[],points=new Map(),edgeIds=new Map(),edgeCounts=new Map();
  for(let q=-2;q<=2;q++)for(let r=-2;r<=2;r++){
    if(Math.abs(q+r)>2)continue;
    const cx=Math.sqrt(3)*51*(q+r/2),cy=1.5*51*r,ids=[];
    for(let i=0;i<6;i++){
      const a=(i*60-30)*Math.PI/180,x=cx+51*Math.cos(a),y=cy+51*Math.sin(a),key=`${Number(x.toFixed(4))},${Number(y.toFixed(4))}`;
      if(!points.has(key)){const id=`v${vertices.length}`;points.set(key,id);vertices.push({id,x,y});}
      ids.push(points.get(key));
    }
    for(let i=0;i<6;i++){const pair=[ids[i],ids[(i+1)%6]].sort(),key=pair.join(':');if(!edgeIds.has(key)){const id=`e${edges.length}`;edgeIds.set(key,id);edges.push({id,vertices:pair});}edgeCounts.set(key,(edgeCounts.get(key)||0)+1);}
    tiles.push({id:`t${tiles.length}`,x:q,y:r,vertices:ids});
  }
  const coastal=edges.filter(e=>edgeCounts.get(e.vertices.join(':'))===1);
  const ports=coastal.filter((e,i)=>i%3===0).slice(0,9).map((e,i)=>({id:`port${i}`,type:i<4?'THREE_TO_ONE':['TWO_TO_ONE_WOOD','TWO_TO_ONE_BRICK','TWO_TO_ONE_SHEEP','TWO_TO_ONE_WHEAT','TWO_TO_ONE_ORE'][i-4],vertices:e.vertices}));
  const participants=['Ada','Babbage','Curie','Dijkstra'].map((name,i)=>({name,player_id:`P${i+1}`,bot_name:'Fixture bot',bot_version:'v1',bot_id:`fixture-${i}`}));
  const metadata={game_id:'game-fixture',room_id:'room-fixture',seed:123,status:'completed',created_at:'2026-09-20T12:00:00Z',replay_available:true,participants,players:participants.map(p=>p.name)};
  const initial={game_id:'game-fixture',phase:'SETUP_FIRST',turn_number:1,current_player:'P1',dice:null,winner:null,tiles:Object.fromEntries(tiles.map((t,i)=>[t.id,{resource:i===9?'DESERT':['WOOD','BRICK','SHEEP','WHEAT','ORE'][i%5],number:i===9?null:[6,4,8,9,5][i%5],robber:i===9}])),buildings:{},roads:{},players:participants.map(p=>({player_id:p.player_id,victory_points:0,roads:0,settlements:0,cities:0,knights:0,longest_road:false,largest_army:false}))};
  const later=structuredClone(initial);later.phase='NORMAL_PLAY';later.turn_number=2;later.dice=8;
  for(let i=0;i<4;i++){later.buildings[vertices[i*8].id]={owner:`P${i+1}`,type:i===0?'CITY':'SETTLEMENT'};later.roads[edges[i*9].id]=`P${i+1}`;later.players[i].roads=1;later.players[i].victory_points=i===0?2:1;later.players[i].cities=i===0?1:0;later.players[i].settlements=i===0?0:1;}
  later.tiles.t9.robber=false;later.tiles.t3.robber=true;
  const frames=[{sequence:0,label:'Initial board',state:initial,events:[]},{sequence:1,label:'Fixture builds and robber move',state:later,events:[]}];
  return {metadata,replay:{schema_version:1,metadata,geometry:{valid_hex_topology:true,tiles,vertices,edges,ports},frames,events:[],result:{status:'completed',winner:'P1',reason:'Synthetic viewer test fixture',statistics:{dice_rolls:{8:1},roll_count:1,recorded_transitions:1,players:later.players}}}};
}
