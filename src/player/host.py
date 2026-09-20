"""SDK-owned JSON Lines process host. Authors only implement a Player class."""
import contextlib
import importlib.util
import inspect
import json
import sys
import os
from .interface import Player, freeze, thaw, PROTOCOL_VERSION

MAX_MESSAGE = 2_000_000


def main():
    if os.name!='nt':
        import resource
        resource.setrlimit(resource.RLIMIT_AS,(256*1024*1024,256*1024*1024))
        resource.setrlimit(resource.RLIMIT_CPU,(30,30))
        resource.setrlimit(resource.RLIMIT_FSIZE,(10*1024*1024,10*1024*1024))
        resource.setrlimit(resource.RLIMIT_NOFILE,(64,64))
    output=sys.stdout
    # User prints are diagnostics, never protocol messages.
    with contextlib.redirect_stdout(sys.stderr):
        spec=importlib.util.spec_from_file_location('submitted_player',sys.argv[1])
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        classes=[c for c in vars(module).values() if inspect.isclass(c) and c is not Player
                 and issubclass(c,Player) and c.__module__==module.__name__]
        if len(classes)!=1: raise ValueError('Define exactly one Player subclass')
        cls=classes[0]
        if cls.choose_action is Player.choose_action: raise ValueError('Override choose_action')
        player=cls()
        if player.protocol_version!=PROTOCOL_VERSION: raise ValueError('Unsupported protocol')
    output.write(json.dumps({'ready':True,'protocol_version':PROTOCOL_VERSION})+'\n');output.flush()
    while True:
        line=sys.stdin.buffer.readline(MAX_MESSAGE+1)
        if not line: break
        if len(line)>MAX_MESSAGE: raise ValueError('Request too large')
        request=json.loads(line)
        method=request['method']
        if method not in ('on_game_start','choose_action','on_event','on_game_end'): raise ValueError('Unknown method')
        try:
            with contextlib.redirect_stdout(sys.stderr):
                result=getattr(player,method)(*(freeze(a) for a in request['args']))
            reply={'id':request['id'],'result':thaw(result)}
            encoded=json.dumps(reply,allow_nan=False)
            if len(encoded.encode())>MAX_MESSAGE: raise ValueError('Response too large')
        except Exception as error:
            # Do not publish exception messages, which may contain private state.
            encoded=json.dumps({'id':request['id'],'error':type(error).__name__})
        output.write(encoded+'\n');output.flush()


if __name__=='__main__':
    main()
