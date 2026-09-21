"""Persistent Player process protocol and failure boundaries."""
import time
import pytest
from src.player.process import ProcessPlayer
from src.player import freeze

CODE='''from src.player import Player
class MyPlayer(Player):
    def __init__(self): self.events=0
    def on_event(self,event): self.events+=1
    def choose_action(self,view,options): return {"seen":self.events}
'''


def test_memory_persists_and_events_are_separate():
    player=ProcessPlayer(CODE)
    try:
        player.on_event(freeze({'type':'A'}));player.on_event(freeze({'type':'B'}))
        assert player.choose_action(freeze({}),())=={'seen':2}
        assert player.choose_action(freeze({}),())=={'seen':2}
    finally: player.close()


@pytest.mark.parametrize('method',['choose_action','on_event'])
def test_infinite_callback_is_killed(method):
    code=f'from src.player import Player\nclass Bad(Player):\n    def choose_action(self,*args): return None\n    def {method}(self,*args):\n        while True: pass\n'
    player=ProcessPlayer(code,timeout=.5)
    start=time.monotonic()
    try:
        with pytest.raises(TimeoutError):getattr(player,method)(*([freeze({}),()] if method=='choose_action' else [freeze({})]))
        assert time.monotonic()-start<5
        assert player.process.poll() is not None
    finally:player.close()


@pytest.mark.parametrize('code',[
    'print("old script protocol")',
    'from src.player import Player\nclass Bad(Player): pass',
    'from src.player import Player\nclass Bad(Player):\n protocol_version=99\n def choose_action(self,*args): pass',
    'raise RuntimeError("import failure")',
])
def test_invalid_implementations_rejected(code):
    with pytest.raises((RuntimeError,TimeoutError)):ProcessPlayer(code)


def test_user_prints_are_diagnostics_and_bounded():
    code=CODE.replace('self.events+=1','print("x"*20000); self.events+=1')
    player=ProcessPlayer(code)
    try:
        player.on_event(freeze({}));assert player.choose_action(freeze({}),())=={'seen':1}
        assert len(player.diagnostics)<=16384
    finally:player.close()
