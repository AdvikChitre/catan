"""Shared legality and transition rules used by the headless engine."""
from collections import Counter
import json
from ..core import GamePhase
from ..core.building import Building, VertexState, EdgeState, Road
from ..simulator.types.identifiers import PlayerId, BuildingType
from ..simulator.types.resource import ResourceType as R, DevelopmentCardType as D

COSTS = {'BUILD_ROAD': {R.WOOD:1,R.BRICK:1},
         'BUILD_SETTLEMENT': {R.WOOD:1,R.BRICK:1,R.SHEEP:1,R.WHEAT:1},
         'BUILD_CITY': {R.WHEAT:2,R.ORE:3},
         'BUY_DEVELOPMENT_CARD': {R.WHEAT:1,R.SHEEP:1,R.ORE:1}}


class RulesEngine:
    def _building(self,v):
        state=self.board.vertices.get(v)
        return state.building if state else Building.empty()

    def _road_owner(self,e):
        state=self.board.edges.get(e)
        return state.road.owner if state else None

    def _space(self,v):
        return (v in self.board_geometry.vertices and self._building(v).is_empty()
                and all(self._building(n).is_empty() for n in self.board_geometry.vertices[v].adjacent_vertex_ids))

    def _affords(self,pid,cost):
        return all(self.player(pid).resources[r]>=n for r,n in cost.items())

    def can_build_settlement(self,pid,v):
        return (self._space(v) and self.player(pid).settlements_remaining>0
                and any(self._road_owner(e)==pid for e in self.board_geometry.vertices[v].adjacent_edge_ids)
                and self._affords(pid,COSTS['BUILD_SETTLEMENT']))

    def _road_legal(self,pid,e):
        if e not in self.board_geometry.edges or self._road_owner(e) is not None or self.player(pid).roads_remaining<=0:
            return False
        for v in self.board_geometry.edges[e].vertex_ids:
            owner=self._building(v).owner
            if owner==pid: return True
            if owner is None and any(self._road_owner(n)==pid for n in self.board_geometry.vertices[v].adjacent_edge_ids):
                return True
        return False

    def can_build_road(self,pid,e): return self._road_legal(pid,e) and self._affords(pid,COSTS['BUILD_ROAD'])

    def can_build_city(self,pid,v):
        b=self._building(v)
        return (b.owner==pid and b.type==BuildingType.SETTLEMENT and self.player(pid).cities_remaining>0
                and self._affords(pid,COSTS['BUILD_CITY']))

    def can_buy_development_card(self,pid):
        return bool(self.development_deck) and self._affords(pid,COSTS['BUY_DEVELOPMENT_CARD'])

    def _ratio(self,pid,resource):
        ratio=4
        for port in self.board_geometry.ports.values():
            if any(self._building(v).owner==pid for v in port.vertex_ids):
                if port.port_type.get_resource_type()==resource: ratio=min(ratio,2)
                elif not port.port_type.is_two_to_one(): ratio=min(ratio,3)
        return ratio

    def _victims(self,tile,pid):
        return sorted({self._building(v).owner for v in self.board_geometry.tiles[tile].vertex_ids
                       if self._building(v).owner not in (None,pid)
                       and self.player(self._building(v).owner).get_total_resources()>0},key=lambda p:p.value)

    def available_actions(self):
        if self.result: return []
        pid=self.acting_player();p=self.player(pid);stage=self.stage
        if stage=='SETUP_SETTLEMENT':
            return [{'type':'PLACE_SETTLEMENT','vertex':v} for v in sorted(self.board_geometry.vertices) if self._space(v)]
        if stage=='SETUP_ROAD':
            return [{'type':'PLACE_ROAD','edge':e} for e in sorted(self.board_geometry.vertices[self.setup_vertex].adjacent_edge_ids)
                    if self._road_owner(e) is None]
        if stage=='DISCARD': return [{'type':'DISCARD','count':p.get_total_resources()//2}]
        if stage=='ROBBER':
            return [{'type':'MOVE_ROBBER','tile':t,'victim':v.value if v else None}
                    for t in sorted(self.board.tiles) if t!=self.board.robber_tile_id
                    for v in (self._victims(t,pid) or [None])]
        if stage=='FREE_ROAD':
            return [{'type':'BUILD_FREE_ROAD','edge':e} for e in sorted(self.board_geometry.edges) if self._road_legal(pid,e)]
        if stage=='PLENTY':
            resources=[r for r in R if self.bank.resources[r]>0]
            pairs=[{'type':'TAKE_RESOURCES','resources':dict(Counter([a.value,b.value]))}
                   for i,a in enumerate(resources) for b in resources[i:]
                   if a!=b or self.bank.resources[a]>=2]
            return pairs or [{'type':'TAKE_RESOURCES','resources':{r.value:1}} for r in resources] or [{'type':'TAKE_RESOURCES','resources':{}}]
        if stage=='MONOPOLY': return [{'type':'TAKE_MONOPOLY','resource':r.value} for r in R]
        if stage=='TRADE_RESPONSE':
            offer=self.trade;actions=[{'type':'REJECT'},{'type':'COUNTER'}]
            if self._affords(pid,offer['receive']): actions.insert(0,{'type':'ACCEPT'})
            return actions
        if stage=='TRADE_SELECT':
            return [{'type':'SELECT_TRADE','response':i} for i,offer in enumerate(self.trade['responses'])
                    if self._affords(self.active,offer['give']) and self._affords(offer['player'],offer['receive'])]+[{'type':'CANCEL_TRADE'}]
        actions=[]
        if not self.card_played:
            for card in D:
                if card!=D.VICTORY_POINT and p.development_cards[card]>self.new_cards[pid][card]:
                    if card==D.ROAD_BUILDING and not any(self._road_legal(pid,e) for e in self.board_geometry.edges): continue
                    actions.append({'type':'PLAY_DEVELOPMENT_CARD','card':card.value})
        if stage=='PRE_ROLL': return [{'type':'ROLL'}]+actions
        if stage!='PLAYING': raise RuntimeError(f'Unknown stage {stage}')
        for v in sorted(self.board_geometry.vertices):
            if self.can_build_settlement(pid,v): actions.append({'type':'BUILD_SETTLEMENT','vertex':v})
            if self.can_build_city(pid,v): actions.append({'type':'BUILD_CITY','vertex':v})
        for e in sorted(self.board_geometry.edges):
            if self.can_build_road(pid,e): actions.append({'type':'BUILD_ROAD','edge':e})
        if self.can_buy_development_card(pid): actions.append({'type':'BUY_DEVELOPMENT_CARD'})
        for give in R:
            ratio=self._ratio(pid,give)
            if p.resources[give]<ratio: continue
            for receive in R:
                if receive!=give and self.bank.resources[receive]>0:
                    actions.append({'type':'BANK_TRADE','give_resource':give.value,'receive_resource':receive.value,'ratio':ratio})
        if p.get_total_resources()>0: actions.append({'type':'TRADE'})
        actions.append({'type':'END_TURN'})
        return actions

    @staticmethod
    def _resources(values,allow_empty=False):
        if not isinstance(values,dict) or (not values and not allow_empty): raise ValueError('Resource quantities required')
        result={}
        for key,n in values.items():
            if type(n) is not int or n<=0: raise ValueError('Resource amounts must be positive integers')
            result[R(key)]=n
        return result

    def _validate(self,pid,action):
        if self._in_callback: raise ValueError('Player callbacks cannot mutate the engine')
        if not self.started or self.result: raise ValueError('Match is not accepting actions')
        if pid!=self.acting_player(): raise ValueError('Wrong acting player')
        if not isinstance(action,dict): raise ValueError('Return an action mapping')
        kind=action.get('type');options=self.available_actions()
        if not any(o['type']==kind for o in options): raise ValueError('Action not available')
        if kind in ('TRADE','COUNTER'):
            allowed={'type','give','receive','recipients'} if kind=='TRADE' else {'type','give','receive'}
            if set(action)!=allowed: raise ValueError('Invalid offer fields')
            give=self._resources(action['give']);receive=self._resources(action['receive'])
            if set(give)&set(receive): raise ValueError('Cannot exchange a resource for itself')
            if not self._affords(pid,give): raise ValueError('Offer exceeds own resources')
            if kind=='TRADE':
                recipients=action['recipients']
                if not isinstance(recipients,list) or not recipients or len(set(recipients))!=len(recipients): raise ValueError('Choose distinct recipients')
                if any(PlayerId(r)==pid for r in recipients): raise ValueError('Cannot trade with self')
                for r in recipients: PlayerId(r)
        elif kind=='DISCARD':
            if set(action)!={'type','resources'}: raise ValueError('Discard requires resources')
            resources=self._resources(action['resources'])
            if sum(resources.values())!=self.player(pid).get_total_resources()//2 or not self._affords(pid,resources):
                raise ValueError('Incorrect discard')
        elif json.dumps(action,sort_keys=True,allow_nan=False) not in [json.dumps(o,sort_keys=True) for o in options]:
            raise ValueError('Return an offered action unchanged')

    def _pay(self,pid,cost):
        for r,n in cost.items():
            self.player(pid).resources[r]-=n;self.bank.resources[r]+=n

    def _grant(self,pid,resources):
        for r,n in resources.items():
            self.bank.resources[r]-=n;self.player(pid).resources[r]+=n

    def _place_settlement(self,pid,v):
        self.board.vertices[v]=VertexState(v,Building.settlement(pid))
        self.player(pid).settlements.add(v);self.player(pid).settlements_remaining-=1

    def _place_road(self,pid,e):
        self.board.edges[e]=EdgeState(e,Road(pid))
        self.player(pid).roads.add(e);self.player(pid).roads_remaining-=1

    def _apply(self,pid,a):
        kind=a['type'];p=self.player(pid)
        if kind=='PLACE_SETTLEMENT':
            self._place_settlement(pid,a['vertex']);self.setup_vertex=a['vertex'];self.stage='SETUP_ROAD'
            self._emit('SettlementBuilt',{'vertex':a['vertex'],'setup':True},pid)
        elif kind=='PLACE_ROAD':
            self._place_road(pid,a['edge'])
            self._emit('RoadBuilt',{'edge':a['edge'],'setup':True},pid)
            if self.setup_index>=4:
                resources=Counter(self.board.tiles[t].resource_type for t in sorted(self.board_geometry.vertices[self.setup_vertex].adjacent_tile_ids)
                                  if self.board.tiles[t].resource_type is not None)
                self._grant(pid,resources)
                self._emit('ResourcesProduced',{'resources':{r.value:n for r,n in resources.items()},'setup':True},pid)
            self.setup_index+=1
            if self.setup_index==8:
                self.game_state.phase=GamePhase.NORMAL_PLAY;self.stage='PRE_ROLL'
                self.game_state.turn_state.current_player=self.order[0]
                self.turn_decisions=0
                self._emit('TurnStarted',{'player_id':self.active.value})
            else:
                self.stage='SETUP_SETTLEMENT'
                self.game_state.phase=GamePhase.SETUP_SECOND if self.setup_index>=4 else GamePhase.SETUP_FIRST
                self.game_state.turn_state.current_player=self.setup_order[self.setup_index]
        elif kind=='ROLL': self._roll()
        elif kind=='END_TURN': self._end_turn()
        elif kind in COSTS:
            self._pay(pid,COSTS[kind])
            if kind=='BUILD_ROAD':
                self._place_road(pid,a['edge']);self._emit('RoadBuilt',{'edge':a['edge']},pid)
            elif kind=='BUILD_SETTLEMENT':
                self._place_settlement(pid,a['vertex']);self._emit('SettlementBuilt',{'vertex':a['vertex']},pid)
            elif kind=='BUILD_CITY':
                v=a['vertex'];self.board.vertices[v].building=Building.city(pid)
                p.settlements.remove(v);p.cities.add(v);p.settlements_remaining+=1;p.cities_remaining-=1
                self._emit('CityBuilt',{'vertex':v},pid)
            else:
                card=self.development_deck.pop(0);self.bank.development_cards[card]-=1
                p.development_cards[card]+=1;self.new_cards[pid][card]+=1
                self._emit('DevelopmentCardPurchased',{},pid)
                self._emit('DevelopmentCardDrawn',{'card':card.value},pid,'PLAYER_ONLY')
        elif kind=='DISCARD':
            resources=self._resources(a['resources']);self._pay(pid,resources)
            self._emit('CardsDiscarded',{'count':sum(resources.values())},pid)
            self._emit('DiscardDetails',{'resources':a['resources']},pid,'PLAYER_ONLY')
            self.discard_queue.pop(0);self.stage='DISCARD' if self.discard_queue else 'ROBBER'
        elif kind=='MOVE_ROBBER':
            self.board.tiles[self.board.robber_tile_id].has_robber=False
            self.board.robber_tile_id=a['tile'];self.board.tiles[a['tile']].has_robber=True
            self._emit('RobberMoved',{'tile_id':a['tile'],'victim_id':a['victim']},pid)
            if a['victim']:
                victim=PlayerId(a['victim']);hand=self.player(victim).resources
                cards=[r for r in R for _ in range(hand[r])]
                r=self.rng.choice(cards);hand[r]-=1;p.resources[r]+=1
                self._emit('ResourceStolen',{'from_player':victim.value,'to_player':pid.value},pid)
                self._emit('TheftDetails',{'from_player':victim.value,'to_player':pid.value,'resource':r.value},pid,'PLAYERS',[pid,victim])
            self.stage=self.return_stage
        elif kind=='PLAY_DEVELOPMENT_CARD':
            card=D(a['card']);p.development_cards[card]-=1;p.played_development_cards.add(card)
            self.discarded_cards[card]+=1
            self.card_played=True;self.return_stage=self.stage
            self._emit('DevelopmentCardPlayed',{'card':card.value},pid)
            if card==D.KNIGHT:
                p.largest_army_count+=1;self.stage='ROBBER'
            elif card==D.ROAD_BUILDING:
                self.free_roads=2;self.stage='FREE_ROAD'
            elif card==D.YEAR_OF_PLENTY: self.stage='PLENTY'
            elif card==D.MONOPOLY: self.stage='MONOPOLY'
        elif kind=='BUILD_FREE_ROAD':
            self._place_road(pid,a['edge']);self._emit('RoadBuilt',{'edge':a['edge'],'free':True},pid)
            self.free_roads-=1
            if not self.free_roads or not any(self._road_legal(pid,e) for e in self.board_geometry.edges): self.stage=self.return_stage
        elif kind=='TAKE_RESOURCES':
            resources=self._resources(a['resources'],allow_empty=True);self._grant(pid,resources)
            self._emit('ResourcesTaken',{'resources':a['resources']},pid);self.stage=self.return_stage
        elif kind=='TAKE_MONOPOLY':
            resource=R(a['resource']);amounts={}
            for other in self.order:
                if other==pid: continue
                n=self.player(other).resources[resource]
                self.player(other).resources[resource]=0;p.resources[resource]+=n;amounts[other.value]=n
            self._emit('MonopolyResolved',{'resource':resource.value,'amounts':amounts},pid);self.stage=self.return_stage
        elif kind=='BANK_TRADE':
            give=R(a['give_resource']);receive=R(a['receive_resource']);ratio=self._ratio(pid,give)
            self._pay(pid,{give:ratio});self._grant(pid,{receive:1})
            self._emit('BankTradeCompleted',{'give':{give.value:ratio},'receive':{receive.value:1}},pid)
        elif kind=='TRADE':
            self.trade={'give':self._resources(a['give']),'receive':self._resources(a['receive']),
                        'recipients':sorted([PlayerId(r) for r in a['recipients']],key=lambda p:p.value),
                        'index':0,'responses':[]}
            self.stage='TRADE_RESPONSE';self._emit('TradeOffered',a,pid)
        elif kind in ('ACCEPT','REJECT','COUNTER'):
            offer=self.trade
            if kind=='ACCEPT': offer['responses'].append({'player':pid,'give':offer['give'],'receive':offer['receive']})
            if kind=='COUNTER':
                offer['responses'].append({'player':pid,'give':self._resources(a['receive']),'receive':self._resources(a['give'])})
            self._emit('TradeResponse',a,pid)
            offer['index']+=1
            self.stage='TRADE_SELECT' if offer['index']==len(offer['recipients']) else 'TRADE_RESPONSE'
        elif kind=='SELECT_TRADE':
            offer=self.trade['responses'][a['response']];other=self.player(offer['player'])
            for r,n in offer['give'].items(): p.resources[r]-=n;other.resources[r]+=n
            for r,n in offer['receive'].items(): other.resources[r]-=n;p.resources[r]+=n
            self._emit('TradeCompleted',{'responder':offer['player'].value,
                'give':{r.value:n for r,n in offer['give'].items()},'receive':{r.value:n for r,n in offer['receive'].items()}},pid)
            self.trade=None;self.stage='PLAYING'
        elif kind=='CANCEL_TRADE':
            self.trade=None;self.stage='PLAYING';self._emit('TradeCancelled',{},pid)
        else: raise RuntimeError('Unhandled action')

    def _roll(self):
        d1=self.rng.randint(1,6);d2=self.rng.randint(1,6);total=d1+d2
        self.game_state.turn_state.dice_roll=total
        self._emit('DiceRolled',{'die1':d1,'die2':d2,'total':total})
        self.return_stage='PLAYING'
        if total==7:
            self.discard_queue=[pid for pid in self.order if self.player(pid).get_total_resources()>7]
            self.stage='DISCARD' if self.discard_queue else 'ROBBER'
        else: self._resolve_roll(total);self.stage='PLAYING'

    def _resolve_roll(self,total):
        claims={r:Counter() for r in R}
        for tid,tile in self.board.tiles.items():
            if tile.number_token!=total or tile.has_robber or tile.resource_type is None: continue
            for v in sorted(self.board_geometry.tiles[tid].vertex_ids):
                building=self._building(v)
                if building.owner:
                    claims[tile.resource_type][building.owner]+=2 if building.type==BuildingType.CITY else 1
        payouts={pid:Counter() for pid in self.order}
        for r,owners in claims.items():
            supply=self.bank.resources[r]
            if sum(owners.values())>supply:
                if len(owners)!=1: continue
                owners={next(iter(owners)):supply}
            for pid,n in owners.items():
                if n: payouts[pid][r]+=n
        for pid,resources in payouts.items():
            if resources:
                self._grant(pid,resources)
                self._emit('ResourcesProduced',{'resources':{r.value:n for r,n in resources.items()}},pid)

    def _end_turn(self):
        self._emit('TurnEnded',{},self.active)
        self.new_cards[self.active].clear();self.player(self.active).played_development_cards.clear()
        turn=self.game_state.turn_state
        turn.current_player=self.order[(self.order.index(self.active)+1)%4]
        turn.turn_number+=1;turn.dice_roll=None
        self.card_played=False;self.turn_decisions=0;self.stage='PRE_ROLL'
        self._emit('TurnStarted',{'player_id':self.active.value})

    def _longest_road_for_player(self,pid):
        owned={e for e in self.board_geometry.edges if self._road_owner(e)==pid}
        def walk(vertex,used):
            if used and self._building(vertex).owner not in (None,pid): return len(used)
            best=len(used)
            for e in sorted((self.board_geometry.vertices[vertex].adjacent_edge_ids & owned) - used):
                other=next(v for v in self.board_geometry.edges[e].vertex_ids if v!=vertex)
                best=max(best,walk(other,used|{e}))
            return best
        return max((walk(v,set()) for e in owned for v in self.board_geometry.edges[e].vertex_ids),default=0)

    def _award(self,flag,values,threshold):
        incumbent=next((p.player_id for p in self.game_state.players if getattr(p,flag)),None)
        best=max(values.values());leaders=[pid for pid in self.order if values[pid]==best]
        holder=None
        if best>=threshold:
            if incumbent in leaders: holder=incumbent
            elif len(leaders)==1: holder=leaders[0]
        for p in self.game_state.players: setattr(p,flag,p.player_id==holder)
        if holder!=incumbent:
            self._emit('AchievementChanged',{'achievement':flag,'owner':holder.value if holder else None})

    def _recalculate_victory_points(self):
        self._award('has_longest_road',{pid:self._longest_road_for_player(pid) for pid in self.order},5)
        self._award('has_largest_army',{pid:self.player(pid).largest_army_count for pid in self.order},3)
        for p in self.game_state.players: p.victory_points=p.get_calculated_victory_points()

    def assert_invariants(self):
        for r in R:
            counts=[self.bank.resources[r]]+[p.resources[r] for p in self.game_state.players]
            assert all(type(n) is int and n>=0 for n in counts)
            assert sum(counts)==19
        for p in self.game_state.players:
            assert len(p.roads)+p.roads_remaining==15
            assert len(p.settlements)+p.settlements_remaining==5
            assert len(p.cities)+p.cities_remaining==4
            assert p.roads=={e for e in self.board.edges if self._road_owner(e)==p.player_id}
            assert p.settlements=={v for v in self.board.vertices if self._building(v).owner==p.player_id and self._building(v).type==BuildingType.SETTLEMENT}
            assert p.cities=={v for v in self.board.vertices if self._building(v).owner==p.player_id and self._building(v).type==BuildingType.CITY}
        assert Counter(self.development_deck)==Counter({c:n for c,n in self.bank.development_cards.items() if n})
        for card,total in {D.KNIGHT:14,D.VICTORY_POINT:5,D.ROAD_BUILDING:2,D.YEAR_OF_PLENTY:2,D.MONOPOLY:2}.items():
            assert self.bank.development_cards[card]+self.discarded_cards[card]+sum(p.development_cards[card] for p in self.game_state.players)==total
        assert sum(t.has_robber for t in self.board.tiles.values())==1
