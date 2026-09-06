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
from ..simulator.types.resource import DevelopmentCardType, ResourceType
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
        self.development_deck = BoardSetup.shuffle_development_deck(self.rng)
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
            decision = self.bot_manager.call_bot(
                player_id,
                "choose_initial_placement",
                self.build_view_for_player(player_id),
                choices,
                default=choices[0],
                fallback=choices[0],
            )
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

        self._recalculate_victory_points()
        self.check_victory()

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
                self.bot_manager.call_bot(
                    player_id,
                    "on_game_start",
                    self.build_view_for_player(player_id),
                    default=None,
                    fallback=None,
                )

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

    def _resolve_roll(self, total: int) -> None:
        """Distribute resources for a successful roll and update turn state."""
        if total == 7:
            self.game_state.turn_state.phase = "PLAYING"
            return

        board_state = self.game_state.board_state
        if board_state is None:
            return

        for player in self.game_state.players:
            for tile_id, tile_state in board_state.tiles.items():
                if tile_state.number_token != total or tile_state.has_robber:
                    continue
                for vertex_id in self.board_geometry.get_tile(tile_id).vertex_ids:
                    vertex_state = board_state.get_vertex(vertex_id)
                    if vertex_state is None or vertex_state.building.is_empty():
                        continue
                    owner = vertex_state.building.owner
                    if owner is None:
                        continue
                    if owner == player.player_id:
                        resource_type = tile_state.resource_type
                        if resource_type is not None:
                            player.resources[resource_type] += 1
                            if vertex_state.building.type and vertex_state.building.type.value == "CITY":
                                player.resources[resource_type] += 1

        self.game_state.turn_state.phase = "PLAYING"

    def roll_dice(self) -> int:
        """Roll the dice for the current player and publish the public event."""
        die1 = self.rng.randint(1, 6)
        die2 = self.rng.randint(1, 6)
        total = die1 + die2
        self.game_state.turn_state.dice_roll = total
        self.game_state.turn_state.phase = "ROLLED"

        self.event_bus.publish(
            GameEvent(
                "DiceRolled",
                data={"die1": die1, "die2": die2, "total": total},
                game_id=self.game_state.game_id,
                turn_number=self.game_state.turn_state.turn_number,
                player_id=self.game_state.turn_state.current_player,
                visibility="PUBLIC",
            )
        )

        self._resolve_roll(total)
        return total

    def end_turn(self) -> None:
        """Advance to the next player and reset turn-phase markers."""
        player_order = PlayerId.all_players()
        current_index = player_order.index(self.game_state.turn_state.current_player)
        next_player = player_order[(current_index + 1) % len(player_order)]
        self.game_state.turn_state.current_player = next_player
        self.game_state.turn_state.turn_number += 1
        self.game_state.turn_state.phase = "PRE_ROLL"
        self.game_state.turn_state.dice_roll = None

    @staticmethod
    def _coerce_action_name(action: object, default: str) -> str:
        """Normalize a bot decision to a safe action string."""
        if isinstance(action, dict):
            action_name = action.get("type")
        else:
            action_name = action

        if action_name is None:
            return default
        return str(action_name).upper()

    def take_turn_for_current_player(self) -> None:
        """Advance the current player through the basic pre-roll and end-turn flow."""
        current_player = self.game_state.turn_state.current_player

        if self.game_state.turn_state.phase == "PRE_ROLL":
            action = self.bot_manager.call_bot(
                current_player,
                "take_turn",
                self.build_view_for_player(current_player),
                ["ROLL"],
                default="ROLL",
                fallback="ROLL",
            )
            action_name = self._coerce_action_name(action, "ROLL")

            if action_name not in ("ROLL", "END_TURN"):
                action_name = "ROLL"

            if action_name == "ROLL":
                self.roll_dice()
                action = self.bot_manager.call_bot(
                    current_player,
                    "take_turn",
                    self.build_view_for_player(current_player),
                    ["END_TURN"],
                    default="END_TURN",
                    fallback="END_TURN",
                )
                action_name = self._coerce_action_name(action, "END_TURN")
                if action_name != "END_TURN":
                    action_name = "END_TURN"
            self.end_turn()
            return

        action = self.bot_manager.call_bot(
            current_player,
            "take_turn",
            self.build_view_for_player(current_player),
            ["END_TURN"],
            default="END_TURN",
            fallback="END_TURN",
        )
        action_name = self._coerce_action_name(action, "END_TURN")
        if action_name == "END_TURN":
            self.end_turn()

    def run(self) -> None:
        """Execute a complete game."""
        if len(self.bot_manager.bots) != 4:
            raise ValueError("All four bots must be registered before starting the game.")

        self.start_game()
        self.perform_setup()

        for _ in range(8):
            self.take_turn_for_current_player()

    def can_build_settlement(self, player_id: PlayerId, vertex_id) -> bool:
        """Check whether a settlement can legally be built at this vertex."""
        player = self.game_state.get_player(player_id)
        if player is None or player.settlements_remaining <= 0:
            return False

        board_state = self.game_state.board_state
        if board_state is None:
            return False

        if vertex_id in board_state.vertices and not board_state.vertices[vertex_id].building.is_empty():
            return False

        vertex_def = self.board_geometry.get_vertex(vertex_id)
        if vertex_def is None:
            return False

        for neighbor_id in vertex_def.adjacent_vertex_ids:
            if neighbor_id in board_state.vertices and not board_state.vertices[neighbor_id].building.is_empty():
                return False

        return all(player.resources.get(resource_type, 0) >= amount for resource_type, amount in {
            ResourceType.WOOD: 1,
            ResourceType.BRICK: 1,
            ResourceType.SHEEP: 1,
            ResourceType.WHEAT: 1,
        }.items())

    def can_build_road(self, player_id: PlayerId, edge_id) -> bool:
        """Check whether a road can legally be built on the given edge."""
        player = self.game_state.get_player(player_id)
        if player is None or player.roads_remaining <= 0:
            return False

        board_state = self.game_state.board_state
        if board_state is None:
            return False

        if edge_id in board_state.edges and not board_state.edges[edge_id].road.is_empty():
            return False

        return all(player.resources.get(resource_type, 0) >= amount for resource_type, amount in {
            ResourceType.WOOD: 1,
            ResourceType.BRICK: 1,
        }.items())

    def can_build_city(self, player_id: PlayerId, vertex_id) -> bool:
        """Check whether a settlement can be upgraded to a city."""
        player = self.game_state.get_player(player_id)
        if player is None or player.cities_remaining <= 0:
            return False

        board_state = self.game_state.board_state
        if board_state is None:
            return False

        if vertex_id not in board_state.vertices:
            return False

        building = board_state.vertices[vertex_id].building
        if building.is_empty() or building.type is None or building.type.value != "SETTLEMENT" or building.owner != player_id:
            return False

        return all(player.resources.get(resource_type, 0) >= amount for resource_type, amount in {
            ResourceType.WHEAT: 2,
            ResourceType.ORE: 3,
        }.items())

    def can_buy_development_card(self, player_id: PlayerId) -> bool:
        """Check whether a development card purchase is legal."""
        player = self.game_state.get_player(player_id)
        if player is None:
            return False
        return all(player.resources.get(resource_type, 0) >= amount for resource_type, amount in {
            ResourceType.WHEAT: 1,
            ResourceType.SHEEP: 1,
            ResourceType.ORE: 1,
        }.items())

    def _coerce_resource_type(self, value):
        """Normalize a resource-like input to a ResourceType enum."""
        if isinstance(value, ResourceType):
            return value
        if isinstance(value, str):
            normalized = value.upper().replace("-", "_")
            return ResourceType[normalized]
        raise ValueError(f"Unsupported resource type: {value!r}")

    def _coerce_development_card(self, value):
        """Normalize a development-card-like input to a DevelopmentCardType enum."""
        if isinstance(value, DevelopmentCardType):
            return value
        if isinstance(value, str):
            normalized = value.upper().replace("-", "_")
            return DevelopmentCardType[normalized]
        raise ValueError(f"Unsupported development card type: {value!r}")

    def _normalize_resource_dict(self, values):
        """Normalize resource data into a dict keyed by ResourceType."""
        if values is None:
            return {}
        if isinstance(values, dict):
            return {self._coerce_resource_type(k): int(v) for k, v in values.items()}
        if isinstance(values, (list, tuple, set)):
            counts = {}
            for item in values:
                resource_type = self._coerce_resource_type(item)
                counts[resource_type] = counts.get(resource_type, 0) + 1
            return counts
        raise ValueError(f"Unsupported resource payload: {values!r}")

    def _player_has_resources(self, player: PlayerState, resource_map: Dict[ResourceType, int]) -> bool:
        return all(player.resources.get(resource_type, 0) >= amount for resource_type, amount in resource_map.items())

    def _place_road(self, player_id: PlayerId, edge_id) -> None:
        """Place a road for a player when the edge is legal."""
        board_state = self.game_state.board_state
        if board_state is None:
            raise ValueError("Board state is not initialized.")
        if edge_id in board_state.edges and not board_state.edges[edge_id].road.is_empty():
            raise ValueError(f"Road already exists on {edge_id}.")

        edge_def = self.board_geometry.get_edge(edge_id)
        if edge_def is None:
            raise ValueError(f"Unknown edge: {edge_id}.")

        player = self.game_state.get_player(player_id)
        if player is None:
            raise ValueError(f"Unknown player {player_id}.")

        connected = False
        for vertex_id in edge_def.vertex_ids:
            vertex_state = board_state.get_vertex(vertex_id)
            if vertex_state is not None and not vertex_state.building.is_empty() and vertex_state.building.owner == player_id:
                connected = True
                break
            vertex_def = self.board_geometry.get_vertex(vertex_id)
            if vertex_def is None:
                continue
            for adjacent_vertex_id in vertex_def.adjacent_vertex_ids:
                adjacent_vertex = board_state.get_vertex(adjacent_vertex_id)
                if adjacent_vertex is not None and not adjacent_vertex.building.is_empty() and adjacent_vertex.building.owner == player_id:
                    connected = True
                    break
            if connected:
                break
        if not connected:
            raise ValueError(f"Road placement on {edge_id} is not connected to the player's network.")

        board_state.edges[edge_id] = EdgeState(str(edge_id), Road(owner=player_id))
        player.roads.add(edge_id)
        player.roads_remaining = max(0, player.roads_remaining - 1)
        self._recalculate_victory_points()
        self.check_victory()

    def _steal_resource(self, player_id: PlayerId, victim_id: PlayerId):
        """Steal one random card from a victim."""
        if player_id == victim_id:
            return None
        player = self.game_state.get_player(player_id)
        victim = self.game_state.get_player(victim_id)
        if player is None or victim is None:
            return None

        stealable = [resource_type for resource_type, amount in victim.resources.items() if amount > 0]
        if not stealable:
            return None

        resource_type = self.rng.choice(stealable)
        victim.resources[resource_type] -= 1
        player.resources[resource_type] += 1
        self.event_bus.publish(
            GameEvent(
                "ResourceStolen",
                data={
                    "from_player": victim_id.value,
                    "to_player": player_id.value,
                    "resource": resource_type.value,
                },
                game_id=self.game_state.game_id,
                turn_number=self.game_state.turn_state.turn_number if self.game_state.turn_state else 0,
                player_id=player_id,
                visibility="PRIVATE",
            )
        )
        return resource_type

    def move_robber(self, tile_id, victim_id: Optional[PlayerId] = None, player_id: Optional[PlayerId] = None) -> dict:
        """Move the robber to a new tile and optionally steal one resource from a victim."""
        board_state = self.game_state.board_state
        if board_state is None:
            raise ValueError("Board state is not initialized.")
        if tile_id not in board_state.tiles:
            raise ValueError(f"Unknown tile {tile_id}.")
        if board_state.robber_tile_id is not None and board_state.robber_tile_id == tile_id:
            raise ValueError(f"Robber already on tile {tile_id}.")

        if board_state.robber_tile_id is not None:
            board_state.tiles[board_state.robber_tile_id].has_robber = False
        board_state.tiles[tile_id].has_robber = True
        board_state.robber_tile_id = tile_id

        if player_id is not None and victim_id is not None:
            self._steal_resource(player_id, victim_id)

        self.event_bus.publish(
            GameEvent(
                "RobberMoved",
                data={"tile_id": str(tile_id), "victim_id": victim_id.value if victim_id is not None else None},
                game_id=self.game_state.game_id,
                turn_number=self.game_state.turn_state.turn_number if self.game_state.turn_state else 0,
                player_id=player_id,
                visibility="PUBLIC",
            )
        )
        return {"type": "MOVE_ROBBER", "tile_id": str(tile_id), "victim_id": victim_id.value if victim_id is not None else None}

    def can_play_development_card(self, player_id: PlayerId, card_type) -> bool:
        """Check whether a development card can be played."""
        player = self.game_state.get_player(player_id)
        if player is None:
            return False
        card = self._coerce_development_card(card_type)
        if card == DevelopmentCardType.VICTORY_POINT:
            return False
        return player.development_cards.get(card, 0) > 0

    def play_development_card(self, player_id: PlayerId, card_type, **kwargs):
        """Execute a development card effect for the given player."""
        player = self.game_state.get_player(player_id)
        if player is None:
            raise ValueError(f"Unknown player {player_id}.")

        card = self._coerce_development_card(card_type)
        if not self.can_play_development_card(player_id, card):
            raise ValueError(f"Player {player_id} does not own a {card.value} development card.")

        player.development_cards[card] -= 1
        player.played_development_cards.add(card)

        if card == DevelopmentCardType.KNIGHT:
            player.largest_army_count += 1
            if player.largest_army_count >= 3:
                player.has_largest_army = True
            tile_id = kwargs.get("tile_id")
            victim_id = kwargs.get("victim_id")
            if tile_id is not None:
                self.move_robber(tile_id, victim_id=victim_id, player_id=player_id)
            self.event_bus.publish(
                GameEvent(
                    "KnightPlayed",
                    data={"player_id": player_id.value, "knights_played": player.largest_army_count},
                    game_id=self.game_state.game_id,
                    turn_number=self.game_state.turn_state.turn_number if self.game_state.turn_state else 0,
                    player_id=player_id,
                    visibility="PUBLIC",
                )
            )
            self._recalculate_victory_points()
            self.check_victory()
            return {"type": "PLAY_KNIGHT", "tile_id": str(tile_id) if tile_id is not None else None}

        if card == DevelopmentCardType.ROAD_BUILDING:
            road_edges = kwargs.get("road_edges") or []
            placed = []
            for edge_id in road_edges[:2]:
                try:
                    self._place_road(player_id, edge_id)
                    placed.append(str(edge_id))
                except ValueError:
                    break
            self.event_bus.publish(
                GameEvent(
                    "RoadBuildingPlayed",
                    data={"player_id": player_id.value, "edges": placed},
                    game_id=self.game_state.game_id,
                    turn_number=self.game_state.turn_state.turn_number if self.game_state.turn_state else 0,
                    player_id=player_id,
                    visibility="PUBLIC",
                )
            )
            self._recalculate_victory_points()
            self.check_victory()
            return {"type": "PLAY_ROAD_BUILDING", "edges": placed}

        if card == DevelopmentCardType.YEAR_OF_PLENTY:
            resource_choices = self._normalize_resource_dict(kwargs.get("resources") or kwargs.get("resource_types"))
            if len(resource_choices) != 2:
                raise ValueError("Year of Plenty requires exactly two resource choices.")
            for resource_type, count in resource_choices.items():
                if count < 1:
                    continue
                if self.game_state.bank_state is None:
                    raise ValueError("Bank is not initialized.")
                if self.game_state.bank_state.resources.get(resource_type, 0) < count:
                    raise ValueError(f"Bank does not have enough {resource_type.value} for Year of Plenty.")
                self.game_state.bank_state.resources[resource_type] -= count
                player.resources[resource_type] += count
            self.event_bus.publish(
                GameEvent(
                    "YearOfPlentyPlayed",
                    data={"player_id": player_id.value, "resources": {r.value: c for r, c in resource_choices.items()}},
                    game_id=self.game_state.game_id,
                    turn_number=self.game_state.turn_state.turn_number if self.game_state.turn_state else 0,
                    player_id=player_id,
                    visibility="PUBLIC",
                )
            )
            self._recalculate_victory_points()
            self.check_victory()
            return {"type": "PLAY_YEAR_OF_PLENTY", "resources": {r.value: c for r, c in resource_choices.items()}}

        if card == DevelopmentCardType.MONOPOLY:
            resource_type = self._coerce_resource_type(kwargs.get("resource_type"))
            monopolized = 0
            for opp_id in PlayerId.all_players():
                if opp_id == player_id:
                    continue
                opp_player = self.game_state.get_player(opp_id)
                if opp_player is None:
                    continue
                amount = opp_player.resources.get(resource_type, 0)
                if amount > 0:
                    opp_player.resources[resource_type] = 0
                    player.resources[resource_type] += amount
                    monopolized += amount
            self.event_bus.publish(
                GameEvent(
                    "MonopolyPlayed",
                    data={"player_id": player_id.value, "resource": resource_type.value, "amount": monopolized},
                    game_id=self.game_state.game_id,
                    turn_number=self.game_state.turn_state.turn_number if self.game_state.turn_state else 0,
                    player_id=player_id,
                    visibility="PUBLIC",
                )
            )
            self._recalculate_victory_points()
            self.check_victory()
            return {"type": "PLAY_MONOPOLY", "resource": resource_type.value, "amount": monopolized}

        raise ValueError(f"Development card {card.value} cannot be played.")

    def can_bank_trade(self, player_id: PlayerId, give_resource, receive_resource, ratio: int = 4) -> bool:
        """Check whether a 4:1 or custom bank trade is legal."""
        player = self.game_state.get_player(player_id)
        if player is None or self.game_state.bank_state is None:
            return False
        give_type = self._coerce_resource_type(give_resource)
        receive_type = self._coerce_resource_type(receive_resource)
        return player.resources.get(give_type, 0) >= ratio and self.game_state.bank_state.resources.get(receive_type, 0) > 0

    def bank_trade(self, player_id: PlayerId, give_resource, receive_resource, ratio: int = 4) -> dict:
        """Execute an atomic bank trade."""
        if not self.can_bank_trade(player_id, give_resource, receive_resource, ratio):
            raise ValueError(f"Bank trade is not legal for {player_id}.")
        player = self.game_state.get_player(player_id)
        if player is None or self.game_state.bank_state is None:
            raise ValueError(f"Unknown player {player_id}.")

        give_type = self._coerce_resource_type(give_resource)
        receive_type = self._coerce_resource_type(receive_resource)
        player.resources[give_type] -= ratio
        self.game_state.bank_state.resources[give_type] += ratio
        player.resources[receive_type] += 1
        self.game_state.bank_state.resources[receive_type] -= 1

        self.event_bus.publish(
            GameEvent(
                "BankTradeCompleted",
                data={
                    "player_id": player_id.value,
                    "give": {give_type.value: ratio},
                    "receive": {receive_type.value: 1},
                },
                game_id=self.game_state.game_id,
                turn_number=self.game_state.turn_state.turn_number if self.game_state.turn_state else 0,
                player_id=player_id,
                visibility="PUBLIC",
            )
        )
        return {"type": "BANK_TRADE", "give": {give_type.value: ratio}, "receive": {receive_type.value: 1}}

    def player_trade(self, proposer_id: PlayerId, responder_id: PlayerId, give: Dict[ResourceType, int], receive: Dict[ResourceType, int]) -> dict:
        """Execute an atomic direct trade between two players."""
        proposer = self.game_state.get_player(proposer_id)
        responder = self.game_state.get_player(responder_id)
        if proposer is None or responder is None:
            raise ValueError("Trade requires both players to exist.")

        give_map = self._normalize_resource_dict(give)
        receive_map = self._normalize_resource_dict(receive)

        if not self._player_has_resources(proposer, give_map):
            raise ValueError(f"Proposer {proposer_id} cannot complete the requested offer.")
        if not self._player_has_resources(responder, receive_map):
            raise ValueError(f"Responder {responder_id} cannot complete the requested counter-offer.")

        for resource_type, amount in give_map.items():
            proposer.resources[resource_type] -= amount
            responder.resources[resource_type] += amount
        for resource_type, amount in receive_map.items():
            responder.resources[resource_type] -= amount
            proposer.resources[resource_type] += amount

        self.event_bus.publish(
            GameEvent(
                "TradeCompleted",
                data={
                    "proposer_id": proposer_id.value,
                    "responder_id": responder_id.value,
                    "give": {r.value: a for r, a in give_map.items()},
                    "receive": {r.value: a for r, a in receive_map.items()},
                },
                game_id=self.game_state.game_id,
                turn_number=self.game_state.turn_state.turn_number if self.game_state.turn_state else 0,
                player_id=proposer_id,
                visibility="PUBLIC",
            )
        )
        return {"type": "TRADE", "proposer_id": proposer_id.value, "responder_id": responder_id.value, "give": give_map, "receive": receive_map}

    def buy_development_card(self, player_id: PlayerId):
        """Buy one development card for the specified player, drawing from the seeded deck."""
        if not self.can_buy_development_card(player_id):
            raise ValueError(f"Player {player_id} cannot buy a development card.")

        if not self.development_deck:
            raise ValueError("Development deck is empty.")

        player = self.game_state.get_player(player_id)
        if player is None:
            raise ValueError(f"Unknown player {player_id}.")

        card = self.development_deck.pop(0)
        self.game_state.bank_state.development_cards[card] -= 1
        player.development_cards[card] += 1

        for resource_type in [
            __import__("src.simulator.types.resource", fromlist=["ResourceType"]).ResourceType.WHEAT,
            __import__("src.simulator.types.resource", fromlist=["ResourceType"]).ResourceType.SHEEP,
            __import__("src.simulator.types.resource", fromlist=["ResourceType"]).ResourceType.ORE,
        ]:
            player.resources[resource_type] -= 1

        self.event_bus.publish(
            GameEvent(
                "DevelopmentCardPurchased",
                data={"player_id": player_id.value, "card": card.value},
                game_id=self.game_state.game_id,
                turn_number=self.game_state.turn_state.turn_number if self.game_state.turn_state else 0,
                player_id=player_id,
                visibility="PUBLIC",
            )
        )

        self._recalculate_victory_points()
        self.check_victory()

        return card

    def execute_action(self, player_id: PlayerId, action: object) -> object:
        """Execute one legal action for a player and mutate the authoritative game state."""
        action_name = action.get("type") if isinstance(action, dict) else action
        if action_name == "BUILD_SETTLEMENT":
            vertex_id = action.get("vertex") if isinstance(action, dict) else None
            if vertex_id is None:
                raise ValueError("BUILD_SETTLEMENT action requires a vertex")
            if not self.can_build_settlement(player_id, vertex_id):
                raise ValueError(f"Settlement is not legal at {vertex_id}.")
            player = self.game_state.get_player(player_id)
            if player is None:
                raise ValueError(f"Unknown player {player_id}.")
            for resource_type, amount in {
                __import__("src.simulator.types.resource", fromlist=["ResourceType"]).ResourceType.WOOD: 1,
                __import__("src.simulator.types.resource", fromlist=["ResourceType"]).ResourceType.BRICK: 1,
                __import__("src.simulator.types.resource", fromlist=["ResourceType"]).ResourceType.SHEEP: 1,
                __import__("src.simulator.types.resource", fromlist=["ResourceType"]).ResourceType.WHEAT: 1,
            }.items():
                player.resources[resource_type] -= amount
            self.game_state.board_state.vertices[vertex_id] = VertexState(str(vertex_id), Building.settlement(player_id))
            player.settlements.add(vertex_id)
            player.settlements_remaining = max(0, player.settlements_remaining - 1)
            self._recalculate_victory_points()
            self.check_victory()
            return {"type": "BUILD_SETTLEMENT", "vertex": str(vertex_id)}

        if action_name == "BUILD_ROAD":
            edge_id = action.get("edge") if isinstance(action, dict) else None
            if edge_id is None:
                raise ValueError("BUILD_ROAD action requires an edge")
            if not self.can_build_road(player_id, edge_id):
                raise ValueError(f"Road is not legal on {edge_id}.")
            player = self.game_state.get_player(player_id)
            for resource_type, amount in {
                __import__("src.simulator.types.resource", fromlist=["ResourceType"]).ResourceType.WOOD: 1,
                __import__("src.simulator.types.resource", fromlist=["ResourceType"]).ResourceType.BRICK: 1,
            }.items():
                player.resources[resource_type] -= amount
            self.game_state.board_state.edges[edge_id] = EdgeState(str(edge_id), Road(owner=player_id))
            player.roads.add(edge_id)
            player.roads_remaining = max(0, player.roads_remaining - 1)
            self._recalculate_victory_points()
            self.check_victory()
            return {"type": "BUILD_ROAD", "edge": str(edge_id)}

        if action_name == "BUILD_CITY":
            vertex_id = action.get("vertex") if isinstance(action, dict) else None
            if vertex_id is None:
                raise ValueError("BUILD_CITY action requires a vertex")
            if not self.can_build_city(player_id, vertex_id):
                raise ValueError(f"City is not legal at {vertex_id}.")
            player = self.game_state.get_player(player_id)
            for resource_type, amount in {
                __import__("src.simulator.types.resource", fromlist=["ResourceType"]).ResourceType.WHEAT: 2,
                __import__("src.simulator.types.resource", fromlist=["ResourceType"]).ResourceType.ORE: 3,
            }.items():
                player.resources[resource_type] -= amount
            self.game_state.board_state.vertices[vertex_id].building = Building.city(player_id)
            player.settlements.discard(vertex_id)
            player.cities.add(vertex_id)
            player.cities_remaining = max(0, player.cities_remaining - 1)
            self._recalculate_victory_points()
            self.check_victory()
            return {"type": "BUILD_CITY", "vertex": str(vertex_id)}

        if action_name == "BUY_DEVELOPMENT_CARD":
            return self.buy_development_card(player_id)

        if action_name == "PLAY_KNIGHT":
            action_payload = action if isinstance(action, dict) else {}
            return self.play_development_card(
                player_id,
                DevelopmentCardType.KNIGHT,
                tile_id=action_payload.get("tile_id"),
                victim_id=action_payload.get("victim_id"),
            )

        if action_name == "PLAY_ROAD_BUILDING":
            action_payload = action if isinstance(action, dict) else {}
            return self.play_development_card(player_id, DevelopmentCardType.ROAD_BUILDING, road_edges=action_payload.get("road_edges", []))

        if action_name == "PLAY_YEAR_OF_PLENTY":
            action_payload = action if isinstance(action, dict) else {}
            return self.play_development_card(player_id, DevelopmentCardType.YEAR_OF_PLENTY, resources=action_payload.get("resources"))

        if action_name == "PLAY_MONOPOLY":
            action_payload = action if isinstance(action, dict) else {}
            return self.play_development_card(player_id, DevelopmentCardType.MONOPOLY, resource_type=action_payload.get("resource"))

        if action_name == "MOVE_ROBBER":
            action_payload = action if isinstance(action, dict) else {}
            return self.move_robber(
                action_payload.get("tile_id"),
                victim_id=action_payload.get("victim_id"),
                player_id=player_id,
            )

        if action_name == "BANK_TRADE":
            action_payload = action if isinstance(action, dict) else {}
            return self.bank_trade(
                player_id,
                action_payload.get("give_resource"),
                action_payload.get("receive_resource"),
                ratio=action_payload.get("ratio", 4),
            )

        if action_name == "TRADE":
            action_payload = action if isinstance(action, dict) else {}
            return self.player_trade(player_id, action_payload.get("to_player"), action_payload.get("give", {}), action_payload.get("receive", {}))

        if action_name == "END_TURN":
            self.end_turn()
            return {"type": "END_TURN"}

        raise ValueError(f"Unsupported action: {action_name}")

    def _recalculate_largest_army(self) -> None:
        """Assign largest army based on knights played in the current game state."""
        for player in self.game_state.players:
            player.has_largest_army = False
        winner_id = None
        winner_count = -1
        for player in self.game_state.players:
            if player.largest_army_count >= 3 and player.largest_army_count > winner_count:
                winner_id = player.player_id
                winner_count = player.largest_army_count
        if winner_id is not None:
            winner = self.game_state.get_player(winner_id)
            if winner is not None:
                winner.has_largest_army = True

    def _road_neighbors(self, edge_id):
        """Return neighboring edges that belong to the same player in the road graph."""
        board_state = self.game_state.board_state
        if board_state is None:
            return []
        edge_def = self.board_geometry.get_edge(edge_id)
        if edge_def is None:
            return []
        neighbors = []
        for vertex_id in edge_def.vertex_ids:
            for adjacent_edge_id in self.board_geometry.get_vertex(vertex_id).adjacent_edge_ids:
                if adjacent_edge_id == edge_id:
                    continue
                other = board_state.get_edge(adjacent_edge_id)
                if other is not None and not other.road.is_empty() and other.road.owner == board_state.get_edge(edge_id).road.owner:
                    neighbors.append(adjacent_edge_id)
        return neighbors

    def _longest_road_for_player(self, player_id: PlayerId) -> int:
        """Compute the longest road path length for a player using a simple graph walk."""
        board_state = self.game_state.board_state
        if board_state is None:
            return 0

        candidate_roads = [
            edge_id for edge_id, edge_data in board_state.edges.items()
            if not edge_data.road.is_empty() and edge_data.road.owner == player_id
        ]
        if not candidate_roads:
            return 0

        best = 0
        visited = set()

        def dfs(edge_id, path_length):
            nonlocal best
            best = max(best, path_length)
            visited.add(edge_id)
            for neighbor in self._road_neighbors(edge_id):
                if neighbor in visited:
                    continue
                dfs(neighbor, path_length + 1)

        for edge_id in candidate_roads:
            if edge_id in visited:
                continue
            dfs(edge_id, 1)

        return best

    def _recalculate_longest_road(self) -> None:
        """Assign longest-road achievement to the player with the longest connected road."""
        for player in self.game_state.players:
            player.has_longest_road = False

        lengths = {player.player_id: self._longest_road_for_player(player.player_id) for player in self.game_state.players}
        if not lengths:
            return

        longest_id = max(lengths, key=lambda pid: (lengths[pid], pid.value))
        if lengths[longest_id] >= 5:
            self.game_state.get_player(longest_id).has_longest_road = True

    def _recalculate_victory_points(self) -> None:
        """Refresh each player's derived victory-point totals and achievement flags."""
        self._recalculate_largest_army()
        self._recalculate_longest_road()
        for player in self.game_state.players:
            player.victory_points = player.get_calculated_victory_points()

    def check_victory(self) -> Optional[PlayerId]:
        """Return the winner if any player has reached the standard Catan threshold."""
        self._recalculate_victory_points()
        for player in self.game_state.players:
            if player.victory_points >= 10:
                self.game_state.winner = player.player_id
                self.game_state.status = GameStatus.COMPLETED
                self.game_state.phase = GamePhase.GAME_OVER
                return player.player_id
        self.game_state.winner = None
        return None
