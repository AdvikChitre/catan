"""Main entry point for the simulator"""
from simulation import Simulator
from simulator.types.identifiers import PlayerId
from bots.bot_interface import BotInterface


class DummyBot(BotInterface):
    """Simple test bot for initial testing"""
    def take_turn(self, view, available_actions):
        """Return the first available action"""
        if available_actions:
            return available_actions[0]
        return None

    def on_event(self, event):
        """Receive a game event"""
        pass


def main():
    """Run a complete game with dummy bots"""
    # Create simulator with a seed for determinism
    simulator = Simulator(seed=42)

    # Register four dummy bots
    bots = {
        PlayerId.P1: DummyBot(),
        PlayerId.P2: DummyBot(),
        PlayerId.P3: DummyBot(),
        PlayerId.P4: DummyBot(),
    }
    simulator.register_bots(bots)

    # Run the game
    print("Starting Catan simulator...")
    simulator.run()
    print("Game complete!")


if __name__ == "__main__":
    main()
