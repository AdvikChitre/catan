"""Deterministic baseline player; strategy is deliberately simple and inspectable."""
from collections import deque
from .interface import Player, thaw


class ExamplePlayer(Player):
    def on_game_start(self,view):
        self.events_seen=0

    def on_event(self,event):
        self.events_seen+=1

    def choose_action(self,view,options):
        actions=thaw(options)
        board=view.board;own=view.self;pid=view.player_id
        by_type={}
        for a in actions: by_type.setdefault(a['type'],[]).append(a)
        def value(v):
            tiles=[board.tiles[t] for t in board.vertices[v].tiles]
            return sum((6-abs(7-t.number)) if t.number else 0 for t in tiles)+len({t.resource for t in tiles})
        for kind in ('PLACE_SETTLEMENT','BUILD_SETTLEMENT','BUILD_CITY'):
            if kind in by_type:
                return max(by_type[kind],key=lambda a:value(a['vertex']))
        if 'DISCARD' in by_type:
            remaining=by_type['DISCARD'][0]['count'];hand=dict(own.resources);out={}
            while remaining:
                r=max(hand,key=lambda k:hand[k]);hand[r]-=1;out[r]=out.get(r,0)+1;remaining-=1
            return {'type':'DISCARD','resources':out}
        if 'MOVE_ROBBER' in by_type:
            def harm(a):
                tile=board.tiles[a['tile']]
                return (sum(1 if board.vertices[v].owner not in (None,pid) else -2 if board.vertices[v].owner==pid else 0
                            for v in tile.vertices)*(6-abs(7-(tile.number or 7)))+bool(a['victim']))
            return max(by_type['MOVE_ROBBER'],key=harm)
        for kind in ('PLAY_DEVELOPMENT_CARD','ROLL','ACCEPT','REJECT','SELECT_TRADE','CANCEL_TRADE'):
            if kind in by_type: return by_type[kind][0]
        if 'TAKE_MONOPOLY' in by_type:
            return max(by_type['TAKE_MONOPOLY'],key=lambda a:19-view.bank[a['resource']]-own.resources[a['resource']])
        if 'TAKE_RESOURCES' in by_type:
            return max(by_type['TAKE_RESOURCES'],key=lambda a:sum(n/(1+own.resources[r]) for r,n in a['resources'].items()))
        # Connect toward a vacant settlement site, never through an opponent.
        def route(edge):
            starts=board.edges[edge].vertices
            queue=deque((v,0) for v in starts);seen=set(starts);best=-100
            while queue:
                v,d=queue.popleft();node=board.vertices[v]
                if node.owner not in (None,pid): continue
                if node.owner is None and all(board.vertices[n].owner is None for n in node.neighbors):
                    best=max(best,value(v)-8*d)
                if d>=4: continue
                for e in node.edges:
                    if board.edges[e].owner not in (None,pid): continue
                    for n in board.edges[e].vertices:
                        if n not in seen: seen.add(n);queue.append((n,d+1))
            return best
        for kind in ('PLACE_ROAD','BUILD_FREE_ROAD'):
            if kind in by_type: return max(by_type[kind],key=lambda a:route(a['edge']))
        if 'BUILD_ROAD' in by_type and own.roads_remaining>3:
            return max(by_type['BUILD_ROAD'],key=lambda a:route(a['edge']))
        if 'BUY_DEVELOPMENT_CARD' in by_type: return by_type['BUY_DEVELOPMENT_CARD'][0]
        # Bank exchange only when it strictly reduces the deficit for a goal;
        # this prevents cycling between equivalent resource hands.
        goals=[{'ORE':3,'WHEAT':2},{'WOOD':1,'BRICK':1,'SHEEP':1,'WHEAT':1},
               {'SHEEP':1,'WHEAT':1,'ORE':1},{'WOOD':1,'BRICK':1}]
        if own.cities_remaining==0: goals=goals[1:]
        hand=dict(own.resources)
        def deficit(h,g): return sum(max(0,n-h[r]) for r,n in g.items())
        candidates=[]
        for i,g in enumerate(goals):
            before=deficit(hand,g)
            for a in by_type.get('BANK_TRADE',[]):
                after=dict(hand);after[a['give_resource']]-=a['ratio'];after[a['receive_resource']]+=1
                if deficit(after,g)<before:
                    candidates.append((before,i,a))
        if candidates: return min(candidates,key=lambda x:(x[0],x[1]))[2]
        if 'END_TURN' in by_type: return by_type['END_TURN'][0]
        return actions[0]
