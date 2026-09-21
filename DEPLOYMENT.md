# VPS deployment

The container runs the FastAPI service, simulator match workers, static web interface, SQLite catalog, and replay store. Persistent data lives in the `catan-data` Docker volume.

```bash
docker compose up -d --build
docker compose ps
curl http://127.0.0.1:8000/health
```

The Compose port binds to localhost deliberately. Put Caddy, nginx, or another TLS reverse proxy in front of `127.0.0.1:8000` and add authentication before exposing it to the internet. Back up the named volume with your normal Docker volume backup process.

Uploaded Player implementations execute in child processes with time and resource limits, but they are executable Python and are not a security boundary against a hostile author. Deploy this service for trusted participants. Public untrusted submissions require a separate locked-down runner host or per-match sandbox with no access to the application data volume.

Useful operations:

```bash
docker compose logs -f catan
docker compose restart catan
docker compose down
```

`docker compose down` preserves the named data volume. Do not add `--volumes` unless you intend to delete the database and every replay.
