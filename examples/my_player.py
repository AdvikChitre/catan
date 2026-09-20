"""Upload this file to try the SDK, then replace the strategy with your own."""
from src.player.example import ExamplePlayer


class MyPlayer(ExamplePlayer):
    def on_game_start(self, view):
        super().on_game_start(view)
        self.production_seen = {}

    def on_event(self, event):
        super().on_event(event)
        if event.type == 'ResourcesProduced':
            for resource, count in event.data.resources.items():
                key = (event.player_id, resource)
                self.production_seen[key] = self.production_seen.get(key, 0) + count

    def choose_action(self, view, options):
        # Replace with your strategy. Event handling stays separate.
        return super().choose_action(view, options)
