"""Player snapshot projection. No backend or database dependencies."""
from ..player import freeze
from ..simulator.types.resource import ResourceType


def observation(sim,pid):
    public=[]
    for p in sim.game_state.players:
        item={'player_id':p.player_id.value,'resource_count':p.get_total_resources(),
              'development_card_count':p.get_total_development_cards(),
              'victory_points':len(p.settlements)+2*len(p.cities)+2*p.has_longest_road+2*p.has_largest_army,
              'roads_remaining':p.roads_remaining,'settlements_remaining':p.settlements_remaining,
              'cities_remaining':p.cities_remaining,'knights_played':p.largest_army_count,
              'has_longest_road':p.has_longest_road,'has_largest_army':p.has_largest_army}
        if p.player_id==pid:
            item.update(resources={r.value:n for r,n in p.resources.items()},
                        development_cards={c.value:n for c,n in p.development_cards.items()},
                        new_development_cards={c.value:n for c,n in sim.new_cards[pid].items()},
                        victory_points=p.get_calculated_victory_points())
            own=item
        else: public.append(item)
    g=sim.board_geometry
    board={'tiles':{t:{'resource':tile.resource_type.value if tile.resource_type else None,
                          'number':tile.number_token,'has_robber':tile.has_robber,
                          'vertices':sorted(g.tiles[t].vertex_ids),'edges':sorted(g.tiles[t].edge_ids)}
                    for t,tile in sim.board.tiles.items()},
           'vertices':{v:{'x':vertex.coordinate.x,'y':vertex.coordinate.y,
                          'neighbors':sorted(vertex.adjacent_vertex_ids),'edges':sorted(vertex.adjacent_edge_ids),
                          'tiles':sorted(vertex.adjacent_tile_ids),'port':vertex.port_id,
                          'owner':sim._building(v).owner.value if sim._building(v).owner else None,
                          'building':sim._building(v).type.value if sim._building(v).type else None}
                       for v,vertex in g.vertices.items()},
           'edges':{e:{'vertices':sorted(edge.vertex_ids),'owner':sim._road_owner(e).value if sim._road_owner(e) else None}
                    for e,edge in g.edges.items()},
           'ports':{k:{'type':p.port_type.value,'vertices':sorted(p.vertex_ids)} for k,p in g.ports.items()},
           'robber_tile':sim.board.robber_tile_id}
    trade=None
    if sim.trade:
        trade={'proposer':sim.active.value,'give':{r.value:n for r,n in sim.trade['give'].items()},
               'receive':{r.value:n for r,n in sim.trade['receive'].items()},
               'recipients':[p.value for p in sim.trade['recipients']],
               'responses':[{'player_id':r['player'].value,'give':{k.value:n for k,n in r['give'].items()},
                             'receive':{k.value:n for k,n in r['receive'].items()}} for r in sim.trade['responses']]}
    return freeze({'protocol_version':1,'game_id':sim.game_state.game_id,'player_id':pid.value,
                   'self':own,'opponents':public,'board':board,'trade':trade,
                   'bank':{r.value:sim.bank.resources[r] for r in ResourceType},
                   'development_deck_count':len(sim.development_deck),
                   'turn':{'number':sim.game_state.turn_state.turn_number,'current_player':sim.active.value,
                           'game_phase':sim.game_state.phase.value,'phase':sim.stage,
                           'dice':sim.game_state.turn_state.dice_roll},
                   'decision_id':sim.decision_number})
