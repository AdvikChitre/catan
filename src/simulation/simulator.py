"""Headless engine: one decision, committed state, then ordered events."""
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass, asdict
import uuid

from ..board import BoardGeometry, BoardSetup
from ..core import BankState, GamePhase, GameState, GameStatus, PlayerState, TurnState
from ..events import EventBus, GameEvent
from ..player import Player, freeze, thaw
from ..replay import ReplayRecorder
from ..simulator.types.identifiers import PlayerId
from .seeded_rng import SeededRng
from ..rules.rules_engine import RulesEngine

ENGINE_VERSION = '2.0'


@dataclass(frozen=True)
class GameConfig:
    max_turns: int = 1000
    max_decisions: int = 20000
    max_decisions_per_turn: int = 200
    random_start: bool = False


class PlayerFailure(RuntimeError):
    pass


class Simulator(RulesEngine):
    def __init__(self, seed=None, config=None):
        self.config = config or GameConfig()
        if any(type(n) is not int or n<=0 for n in (self.config.max_turns,self.config.max_decisions,self.config.max_decisions_per_turn)):
            raise ValueError('Simulation limits must be positive integers')
        self.rng = SeededRng(seed)
        self.board_geometry = BoardGeometry()
        s = self.game_state = GameState()
        s.game_id = 'game-' + uuid.uuid4().hex
        s.seed = self.rng.seed
        s.board_state = BoardSetup.build_board_state(self.board_geometry,self.rng)
        s.bank_state = BankState()
        s.players = [PlayerState(pid) for pid in PlayerId.all_players()]
        s.turn_state = TurnState()
        self.order = PlayerId.all_players()
        if self.config.random_start:
            offset=self.rng.randint(0,3)
            self.order=self.order[offset:]+self.order[:offset]
        s.turn_state.current_player=self.order[0]
        s.turn_state.turn_number=1
        s.phase=GamePhase.SETUP_FIRST
        self.development_deck=BoardSetup.shuffle_development_deck(self.rng)
        self.players={}
        self.event_bus=EventBus()
        self.replay_recorder=ReplayRecorder()
        self.event_bus.subscribe(self.replay_recorder.record_event)
        self.replay_recorder.metadata.update(game_id=s.game_id,seed=s.seed,engine_version=ENGINE_VERSION,protocol_version=1)
        self.observers=[]
        self.decisions=[]
        self.result=None
        self.started=False
        self.stage='SETUP_SETTLEMENT'
        self.setup_index=0
        self.setup_order=self.order+list(reversed(self.order))
        self.setup_vertex=None
        self.return_stage='PLAYING'
        self.discard_queue=[]
        self.free_roads=0
        self.trade=None
        self.new_cards={pid:Counter() for pid in self.order}
        self.card_played=False
        self.discarded_cards=Counter()
        self.decision_number=0
        self.turn_decisions=0
        self._events=[]
        self._in_callback=False
        self._faults=[]

    @property
    def board(self): return self.game_state.board_state

    @property
    def bank(self): return self.game_state.bank_state

    @property
    def active(self): return self.game_state.turn_state.current_player

    def player(self,pid):
        if isinstance(pid,str): pid=PlayerId(pid)
        p=self.game_state.get_player(pid)
        if p is None: raise ValueError('Unknown player')
        return p

    def register_players(self, players):
        if self.started: raise ValueError('Match already started')
        if set(players)!=set(PlayerId.all_players()): raise ValueError('Exactly four player seats required')
        if len({id(p) for p in players.values()})!=4: raise ValueError('Each seat needs its own player instance')
        for p in players.values():
            if not isinstance(p,Player): raise TypeError('Implement src.player.Player')
            if p.protocol_version!=1: raise ValueError('Unsupported player protocol version')
        self.players=dict(players)

    register_bots=register_players

    def subscribe(self, observer):
        """A trusted observer receives committed transitions, not private callbacks."""
        self.observers.append(observer)

    def _emit(self,kind,data=None,pid=None,visibility='PUBLIC',recipients=None):
        self._events.append(GameEvent(kind,data or {},self.game_state.game_id,
            self.game_state.turn_state.turn_number,pid or self.active,visibility,
            metadata={'player_ids':recipients or []}))

    def _call(self,pid,method,*args):
        if self._in_callback: raise RuntimeError('Reentrant player callback')
        self._in_callback=True
        try:
            return getattr(self.players[pid],method)(*args)
        except Exception as error:
            raise PlayerFailure(f'{pid.value} failed in {method}: {type(error).__name__}') from error
        finally:
            self._in_callback=False

    def _flush(self,label):
        events=self._events
        self._events=[]
        for event in events:
            self.event_bus.publish(event)
            for pid in self.order:
                if pid in self.players and event.is_visible_to(pid) and pid not in self._faults:
                    try:
                        self._call(pid,'on_event',freeze({'sequence':event.sequence_number,
                            'type':event.event_type,'player_id':event.player_id,
                            'turn_number':event.turn_number,'data':event.data}))
                    except PlayerFailure:
                        self._faults.append(pid)
        for observer in self.observers: observer(label)
        if self._faults and self.result is None:
            self._finish('player_failed',f'{self._faults[0].value} failed while handling an event')

    def start_game(self):
        if self.started: raise ValueError('Match already started')
        if len(self.players)!=4: raise ValueError('Register four players first')
        self.started=True
        for pid in self.order:
            try: self._call(pid,'on_game_start',self.build_view_for_player(pid))
            except PlayerFailure as error:
                self._finish('player_failed',str(error));return self.game_state
        # Seed is replay metadata, never player input: it would reveal the deck.
        self._emit('GameStarted',{'order':[p.value for p in self.order]})
        self._flush('Game started')
        return self.game_state

    def acting_player(self):
        if self.stage.startswith('SETUP'): return self.setup_order[self.setup_index]
        if self.stage=='DISCARD': return self.discard_queue[0]
        if self.stage=='TRADE_RESPONSE': return self.trade['recipients'][self.trade['index']]
        return self.active

    def build_view_for_player(self,pid):
        from ..views.observation import observation
        return observation(self,pid)

    def decision(self):
        if not self.started: raise ValueError('Start match first')
        if self.result: return None
        return freeze({'id':self.decision_number,'player_id':self.acting_player(),'phase':self.stage,
                       'options':self.available_actions()})

    def apply_action(self,pid,action,decision_id=None):
        if isinstance(pid,str): pid=PlayerId(pid)
        action=thaw(action)
        if decision_id is not None and decision_id!=self.decision_number: raise ValueError('Stale decision')
        self._validate(pid,action)
        self.decisions.append({'decision':self.decision_number,'player_id':pid.value,'action':deepcopy(action)})
        self.decision_number+=1;self.turn_decisions+=1
        self._apply(pid,action)
        self.game_state.turn_state.phase=self.stage
        self._recalculate_victory_points()
        if self.game_state.phase==GamePhase.NORMAL_PLAY and self.player(self.active).victory_points>=10:
            self._finish('completed','Victory',self.active)
        else:
            self._flush(action['type'].replace('_',' ').title())
        return action

    execute_action=apply_action

    def step(self):
        if not self.started: self.start_game()
        if self.result: return self.result
        if (self.decision_number>=self.config.max_decisions or self.turn_decisions>=self.config.max_decisions_per_turn
                or self.game_state.turn_state.turn_number>self.config.max_turns):
            self._finish('stopped','Configured simulation limit reached');return self.result
        pid=self.acting_player()
        try:
            action=self._call(pid,'choose_action',self.build_view_for_player(pid),freeze(self.available_actions()))
        except PlayerFailure as error:
            self._finish('player_failed',str(error));return self.result
        try:
            self.apply_action(pid,action,self.decision_number)
        except (ValueError,TypeError,KeyError) as error:
            self._finish('player_failed',f'{pid.value}: invalid action ({error})')
        return self.result

    def run(self):
        while self.result is None: self.step()
        return self.result

    def export_private_audit(self):
        """Trusted local analysis only: includes private decisions and events."""
        return {'seed':self.game_state.seed,'engine_version':ENGINE_VERSION,
                'protocol_version':1,'config':asdict(self.config),
                'decisions':deepcopy(self.decisions),'events':self.replay_recorder.export(),
                'result':deepcopy(self.result)}

    def _finish(self,status,reason,winner=None):
        if self.result is not None: return
        self.game_state.winner=winner
        self.game_state.status=GameStatus.COMPLETED if status=='completed' else GameStatus.ERROR if status in ('player_failed','failed') else GameStatus.STOPPED
        self.game_state.phase=GamePhase.GAME_OVER;self.stage='GAME_OVER'
        self.game_state.turn_state.phase=self.stage
        self.result={'status':status,'reason':reason,'winner':winner.value if winner else None,
                     'turn_count':self.game_state.turn_state.turn_number,'decisions':self.decision_number,
                     'engine_version':ENGINE_VERSION,'protocol_version':1}
        if winner:
            self._emit('GameWon',{'winner':winner.value,'victory_points':self.player(winner).victory_points},winner)
        self._emit('GameEnded',dict(self.result))
        self._flush('Game finished')
        for pid in self.order:
            if pid in self.players and pid not in self._faults:
                try: self._call(pid,'on_game_end',freeze(self.result))
                except PlayerFailure: self._faults.append(pid)
