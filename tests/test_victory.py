from src.simulation import Simulator
from src.simulator.types.identifiers import PlayerId
from src.simulator.types.resource import DevelopmentCardType as D
from tests.engine_helpers import playing,apply


def test_hidden_vp_win_only_on_owners_turn():
    s=playing();p=s.player(PlayerId.P2)
    # Synthetic scoring fixture isolates victory timing from board construction.
    p.development_cards[D.VICTORY_POINT]=8
    s._recalculate_victory_points()
    assert p.victory_points==10 and s.result is None
    apply(s,'END_TURN')
    assert s.result['winner']=='P2' and s.result['status']=='completed'


def test_road_loop_and_branch_counts_edges_without_reuse():
    s=Simulator(1);tile=s.board_geometry.tiles['T00'];pid=PlayerId.P1
    for e in tile.edge_ids:s._place_road(pid,e)
    assert s._longest_road_for_player(pid)==6
    v=next(iter(sorted(tile.vertex_ids)))
    branch=next(e for e in s.board_geometry.vertices[v].adjacent_edge_ids if e not in tile.edge_ids)
    s._place_road(pid,branch)
    assert s._longest_road_for_player(pid)==7
    s._place_settlement(PlayerId.P2,v)
    assert s._longest_road_for_player(pid)==6


def test_largest_army_tie_retains_incumbent():
    s=Simulator(1)
    s.player(PlayerId.P2).largest_army_count=3;s._recalculate_victory_points()
    s.player(PlayerId.P1).largest_army_count=3;s._recalculate_victory_points()
    assert s.player(PlayerId.P2).has_largest_army and not s.player(PlayerId.P1).has_largest_army
    s.player(PlayerId.P1).largest_army_count=4;s._recalculate_victory_points()
    assert s.player(PlayerId.P1).has_largest_army
