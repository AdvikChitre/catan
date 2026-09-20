"""Compatibility helpers. Public export never exposes the internal recorder."""
from ..player import thaw
from ..platform.recording import public_state, EVENT_FIELDS

def get_replay(sim):
    events=[]
    for e in sim.event_bus.events:
        if e.visibility!='PUBLIC': continue
        events.append({'sequence':len(events),'type':e.event_type,
                       'data':{k:e.data[k] for k in EVENT_FIELDS.get(e.event_type,()) if k in (e.data or {})}})
    return {'metadata':dict(sim.replay_recorder.metadata),'events':events}

def get_state(sim,player_id=None):
    # Per-player projection is for trusted internal callers; HTTP rejects it.
    if player_id is not None: return thaw(sim.build_view_for_player(player_id))
    return public_state(sim)
