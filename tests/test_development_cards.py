import pytest
from tests.engine_helpers import playing,grant,apply

def test_purchase_draws_seeded_card_and_returns_cost_to_bank():
    s=playing();grant(s,s.active,{'WHEAT':1,'SHEEP':1,'ORE':1})
    card=s.development_deck[0];apply(s,'BUY_DEVELOPMENT_CARD')
    assert s.player(s.active).development_cards[card]==1
    assert s.new_cards[s.active][card]==1
    assert not any(a.get('card')==card.value for a in s.available_actions())
    s.assert_invariants()

def test_purchase_without_resources_is_rejected():
    s=playing()
    for p in s.game_state.players:s._pay(p.player_id,dict(p.resources))
    with pytest.raises(ValueError):apply(s,'BUY_DEVELOPMENT_CARD')
