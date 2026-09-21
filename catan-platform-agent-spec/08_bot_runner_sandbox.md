# 8. Bot Runner and Sandbox

Uploaded bot code is untrusted.

Never run it:
- inside the web/API server;
- inside the simulator process;
- with host filesystem access;
- with database/cloud credentials.

## Execution
Run one isolated bot process/container per bot in a game.

## Required restrictions
Bot cannot:
- read host filesystem;
- access another bot workspace/process;
- access simulator memory;
- access server credentials;
- access internal services;
- make arbitrary outbound network connections.

Default network: disabled.

## Resource limits
Configure:
- CPU quota
- memory limit
- process/thread limit
- temporary filesystem quota
- wall-clock timeout

## Lifecycle
1. start four runners;
2. load frozen BotVersion artifacts;
3. establish protocol;
4. process game;
5. stop runners when game ends;
6. forcibly terminate stuck runners.

## Logs
Capture stderr, runner diagnostics, exit code, protocol errors and timeout information.
Do not expose secrets in user-facing diagnostics.

## Adapter
Simulator sees a BotController interface.
Local testing may use direct trusted bot classes.
Production uses the isolated protocol runner.
