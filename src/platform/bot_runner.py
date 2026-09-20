"""Platform wrapper for the public Player API."""
from dataclasses import dataclass, field
from typing import Any, Optional
from ..player import Player
from ..player.example import ExamplePlayer
from ..player.process import ProcessPlayer

@dataclass
class BotRunner(Player):
    bot_id: str
    name: str
    version: str = 'v1'
    status: str = 'pending'
    ready: bool = False
    last_error: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    use_sandbox: bool = False
    bot_code: Optional[str] = None
    sandbox_config: Any = None
    _delegate: Any = None

    def validate(self):
        try:
            if self._delegate is None:
                self._delegate=ProcessPlayer(self.bot_code) if self.use_sandbox else ExamplePlayer()
            self.status='ready';self.ready=True
            return {'ok':True,'bot_id':self.bot_id,'version':self.version}
        except Exception as error:
            self.status='invalid';self.ready=False;self.last_error=str(error)
            return {'ok':False,'error':self.last_error}

    def on_game_start(self,view): self._delegate.on_game_start(view)
    def on_event(self,event): self._delegate.on_event(event)
    def choose_action(self,view,options): return self._delegate.choose_action(view,options)
    def on_game_end(self,result): self._delegate.on_game_end(result)

    def start(self):
        if not self.ready: raise RuntimeError('Player not ready')
        self.status='running'
        return {'bot_id':self.bot_id,'status':self.status}

    def stop(self):
        if isinstance(self._delegate,ProcessPlayer): self._delegate.close()
        self._delegate=None;self.status='stopped'
        return {'bot_id':self.bot_id,'status':self.status}
