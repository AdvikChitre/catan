"""Main simulator orchestrator"""
from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from ..board import BoardGeometry, BoardSetup
from ..bots import BotManager
from ..core import BankState, GamePhase, GameState, GameStatus, PlayerState, TurnState
from ..core.building import Building, EdgeState, Road, VertexState
from ..events import EventBus, GameEvent
from ..simulation.seeded_rng import SeededRng
from ..simulator.types.identifiers import PlayerId
from ..views import GameViewBuilder


class Simulator:
    """Top-level orchestrator for the game."""
    def __init__(self, seed: Optional[int] = None):
        self.rng = SeededRng(seed)
        self.game_state = GameState()
        self.game_state.game_id = f"game-{self.rng.seed}"
        self.game_state.seed = self.rng.seed
        self.game_state.phase = GamePhase.SETUP_FIRST
        self.game_state.status = GameStatus.ACTIVE
        self.board_geometry = BoardGeometry()
        self.game_state.board_state = BoardSetup.build_board_state(self.board_geometry, self.rng)
        self.game_state.bank_state = BankState()
        self.game_state.players = [PlayerState(player_id) for player_id in PlayerId.all_players()]
        self.game_state.turn_state = TurnState()
        self.game_state.turn_state.current_player = PlayerId.P1
        self.game_state.turn_state.turn_number = 1
        self.game_state.turn_state.phase = "PRE_ROLL"
        self.bot_manager = BotManager()
        self.event_bus = EventBus()

    def register_bots(self, bots: Dict[PlayerId, object]) -> None:
        """Register exactly four bots for the four players."""
        if set(bots.keys()) != set(PlayerId.all_players()):
            raise ValueError("Exactly one bot is required for each player.")
        for player_id, bot in bots.items():
            self.bot_manager.register_bot(player_id, bot)

    def build_view_for_player(self, player_id: PlayerId):
        """Build the current view for a specific player."""
        return GameViewBuilder(self.game_state).build_view(player_id)

    def _legal_setup_choices(self, player_id: PlayerId) -> List[dict]:
        """Compute legal settlement and road choices in setup order."""
        board_state = self.game_state.board_state
        if board_state is None:
            return []

        choices: List[dict] = []
        for vertex_id, vertex_def in self.board_geometry.vertices.items():
            if vertex_id in board_state.vertices and not board_state.vertices[vertex_id].building.is_empty():
                continue

            adjacent_occupied = False
            for neighbor_id in vertex_def.adjacent_vertex_ids:
                if neighbor_id in board_state.vertices and not board_state.vertices[neighbor_id].building.is_empty():
                    adjacent_occupied = True
                    break
            if adjacent_occupied:
                continue

            legal_roads = [
                edge_id
                for edge_id in vertex_def.adjacent_edge_ids
                if edge_id not in board_state.edges or board_state.edges[edge_id].road.is_empty()
            ]
            if not legal_roads:
                continue

            choices.append({
                "settlement_vertex": vertex_id,
                "road_edge": legal_roads[0],
                "road_edges": legal_roads,
            })

        return choices

    def _award_starting_resources(self, player_id: PlayerId, settlement_vertex_id) -> None:
        """Award one resource card per adjacent tile during second setup placement."""
        vertex_def = self.board_geometry.get_vertex(settlement_vertex_id)
        if vertex_def is None:
            return

        player = self.game_state.get_player(player_id)
        if player is None:
            return

        for tile_id in vertex_def.adjacent_tile_ids:
            tile = self.game_state.board_state.get_tile(tile_id) if self.game_state.board_state else None
            if tile is None or tile.resource_type is None:
                continue
            player.resources[tile.resource_type] += 1

    def _perform_setup_placement(self, player_id: PlayerId, is_second_pass: bool) -> None:
        """Ask a bot to pick a legal initial placement and apply it."""
        choices = self._legal_setup_choices(player_id)
        if not choices:
            raise ValueError(f"No legal setup moves for {player_id}.")

        bot = self.bot_manager.get_bot(player_id)
        decision = None
        if hasattr(bot, "choose_initial_placement"):
            decision = bot.choose_initial_placement(self.build_view_for_player(player_id), choices)
        if decision is None:
            decision = choices[0]

        settlement_vertex = decision.get("settlement_vertex") if isinstance(decision, dict) else None
        road_edge = decision.get("road_edge") if isinstance(decision, dict) else None
        if settlement_vertex is None or road_edge is None:
            settlement_vertex = choices[0]["settlement_vertex"]
            road_edge = choices[0]["road_edge"]

        valid = any(
            choice["settlement_vertex"] == settlement_vertex and road_edge in choice["road_edges"]
            for choice in choices
        )
        if not valid:
            settlement_vertex = choices[0]["settlement_vertex"]
            road_edge = choices[0]["road_edge"]

        player = self.game_state.get_player(player_id)
        if player is None:
            raise ValueError(f"Unknown player {player_id}.")

        board_state = self.game_state.board_state
        if board_state is None:
            raise ValueError("Board state is not initialized.")

        board_state.vertices[settlement_vertex] = VertexState(str(settlement_vertex), Building.settlement(player_id))
        board_state.edges[road_edge] = EdgeState(str(road_edge), Road(owner=player_id))

        player.settlements.add(settlement_vertex)
        player.roads.add(road_edge)
        player.settlements_remaining = max(0, player.settlements_remaining - 1)
        player.roads_remaining = max(0, player.roads_remaining - 1)

        if is_second_pass:
            self._award_starting_resources(player_id, settlement_vertex)

        self.event_bus.publish(
            GameEvent(
                "SetupPlacementMade",
                data={
                    "player_id": player_id.value,
                    "settlement_vertex": str(settlement_vertex),
                    "road_edge": str(road_edge),
                    "second_pass": is_second_pass,
                },
                game_id=self.game_state.game_id,
                turn_number=self.game_state.turn_state.turn_number if self.game_state.turn_state else 0,
                player_id=player_id,
                visibility="PUBLIC",
            )
        )

    def perform_setup(self) -> None:
        """Run the two setup rounds in canonical snake order."""
        setup_order = [PlayerId.P1, PlayerId.P2, PlayerId.P3, PlayerId.P4, PlayerId.P4, PlayerId.P3, PlayerId.P2, PlayerId.P1]
        self.game_state.phase = GamePhase.SETUP_FIRST
        for player_id in setup_order[:4]:
            self._perform_setup_placement(player_id, is_second_pass=False)

        self.game_state.phase = GamePhase.SETUP_SECOND
        for player_id in setup_order[4:]:
            self._perform_setup_placement(player_id, is_second_pass=True)

        self.game_state.phase = GamePhase.NORMAL_PLAY
        self.game_state.turn_state.current_player = PlayerId.P1
        self.game_state.turn_state.phase = "PRE_ROLL"

    def start_game(self) -> GameState:
        """Notify every bot that the game has started and publish the initial public event."""
        if len(self.bot_manager.bots) != 4:
            raise ValueError("All four bots must be registered before starting the game.")

        for player_id in PlayerId.all_players():
            bot = self.bot_manager.get_bot(player_id)
            if hasattr(bot, "on_game_start"):
                bot.on_game_start(self.build_view_for_player(player_id))

        for player_id in PlayerId.all_players():
            self.event_bus.publish(
                GameEvent(
                    "GameStarted",
                    data={"seed": self.game_state.seed, "player_id": player_id.value},
                    game_id=self.game_state.game_id,
                    turn_number=self.game_state.turn_state.turn_number if self.game_state.turn_state else 0,
                    player_id=player_id,
                    visibility="PUBLIC",
                )
            )

        self.game_state.phase = GamePhase.SETUP_FIRST
        self.game_state.status = GameStatus.ACTIVE
        return self.game_state

    def run(self) -> None:
        """Execute a complete game."""
        if len(self.bot_manager.bots) != 4:
            raise ValueError("All four bots must be registered before starting the game.")

        self.start_game()
        self.perform_setup()
