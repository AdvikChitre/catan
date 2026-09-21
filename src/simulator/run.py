"""Run a full local match with the example players."""
from ..player.example import ExamplePlayer
from ..simulation import Simulator
from .types.identifiers import PlayerId

DummyBot = ExamplePlayer  # Compatibility import for the existing platform.


def main():
    import argparse
    import json
    from pathlib import Path
    from ..player.process import ProcessPlayer
    from ..platform.recording import RecordingSimulator
    from ..simulation.simulator import GameConfig
    parser=argparse.ArgumentParser(description='Run a headless four-player Catan match')
    parser.add_argument('--seed',type=int,default=42)
    parser.add_argument('--max-turns',type=int,default=1000)
    parser.add_argument('--player',action='append',default=[],help='Python implementation file; repeat four times')
    parser.add_argument('--replay',help='Save the public replay JSON')
    parser.add_argument('--audit',help='Save a private decision audit; do not publish this file')
    args=parser.parse_args()
    if len(args.player) not in (0,4): parser.error('Supply zero or four --player arguments')
    sim=RecordingSimulator(args.seed,GameConfig(max_turns=args.max_turns))
    players={}
    try:
        for i,pid in enumerate(PlayerId.all_players()):
            players[pid]=ProcessPlayer(Path(args.player[i]).read_text(encoding='utf-8')) if args.player else ExamplePlayer()
        sim.register_players(players);sim.begin_recording()
        result=sim.run();sim.assert_invariants()
        if args.replay:
            Path(args.replay).write_text(json.dumps(sim.export_recording({'seed':args.seed,'game_id':sim.game_state.game_id})),encoding='utf-8')
        if args.audit: Path(args.audit).write_text(json.dumps(sim.export_private_audit()),encoding='utf-8')
        print(json.dumps(result))
        return 1 if result['status'] in ('failed','player_failed') else 0
    finally:
        for player in players.values():
            if isinstance(player,ProcessPlayer): player.close()


if __name__ == '__main__':
    raise SystemExit(main())
