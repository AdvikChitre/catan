# 7. Bot Package Format

Users upload a ZIP package.

Example:
```text
my-bot.zip
  manifest.json
  bot.py
  requirements.txt
  ...
```

Manifest:
```json
{
  "name": "AggressiveBot",
  "version": "1.3.0",
  "language": "python",
  "entrypoint": "bot:MyBot",
  "sdkVersion": "1",
  "protocolVersion": "1"
}
```

Required:
- name
- version
- language
- entrypoint
- sdkVersion
- protocolVersion

Upload validation:
1. store immutable artifact;
2. validate manifest;
3. validate package paths;
4. verify language/runtime;
5. launch isolated validation runner;
6. instantiate bot;
7. run SDK/protocol smoke tests;
8. record diagnostics;
9. mark valid/invalid.

Reject:
- path traversal
- absolute paths
- symlink escapes
- oversized files/packages
- unsupported runtimes
- incompatible SDK/protocol
- missing required bot methods

Once validated, a BotVersion is immutable.
