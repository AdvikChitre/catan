"""One match per process. No HTTP application or SQL room service is imported."""
import json
from pathlib import Path
import sys
from dataclasses import asdict
from .recording import RecordingSimulator
from .replay_store import ReplayStore
from ..player.example import ExamplePlayer
from ..player.process import ProcessPlayer
from ..simulation.simulator import GameConfig
from ..simulator.types.identifiers import PlayerId


def run_job(job):
    metadata=job['metadata']
    store=ReplayStore(job['replay_directory'],job.get('catalog_path'))
    sim=RecordingSimulator(metadata['seed'],GameConfig(**job.get('config',{})))
    sim.game_state.game_id=metadata['game_id']
    sim.replay_recorder.metadata['game_id']=metadata['game_id']
    runners=[]
    try:
        players={}
        for pid,package in zip(PlayerId.all_players(),job['packages']):
            player=ProcessPlayer(package['code']) if package and package.get('code') else ExamplePlayer()
            if isinstance(player,ProcessPlayer): runners.append(player)
            players[pid]=player
        sim.register_players(players)
        sim.begin_recording()
        sim.run()
        sim.assert_invariants()
        store.save_private_audit(metadata['game_id'],sim.export_private_audit())
        metadata.update(engine_version='2.0',protocol_version=1,rules=asdict(sim.config))
        recording=sim.export_recording(metadata)
        # Only the public projection is persisted here. No private callbacks,
        # raw code, or internal decision audit are served as replay data.
        metadata.update(status=recording['result']['status'],winner=recording['result']['winner'],
                        reason=recording['result']['reason'],replay_available=True)
        recording['metadata']=metadata
        store.finish(metadata['game_id'],recording,metadata)
    finally:
        for player in runners: player.close()


if __name__=='__main__':
    run_job(json.loads(Path(sys.argv[1]).read_text(encoding='utf-8')))
