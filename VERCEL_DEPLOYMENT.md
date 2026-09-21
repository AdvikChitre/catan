# Deploy the frontend to Vercel

The static frontend is built from `src/platform/static` into `dist`. The production build uses `https://catansim.duckdns.org` as its API origin unless `CATAN_API_BASE_URL` overrides it.

## Create the Vercel project

1. In Vercel, choose **Add New → Project** and import `AdvikChitre/catan`.
2. Leave the root directory as the repository root. `vercel.json` forces the **Other** framework preset so Vercel does not auto-detect the FastAPI backend.
3. Set the production branch to `simulator` under **Settings → Git**.
4. Add `CATAN_API_BASE_URL=https://catansim.duckdns.org` under **Settings → Environment Variables** for Production and Preview.
5. Deploy. `vercel.json` supplies `npm run build` and the `dist` output directory.

Record the stable production origin Vercel assigns, for example `https://catan-simulator.vercel.app`. Do not use a commit-specific preview URL for the backend setting.

## Allow the Vercel production origin on the VPS

SSH to the VPS and update the checkout. The committed Compose file binds FastAPI only to `127.0.0.1:8000`, behind Caddy.

```bash
cd /home/ubuntu/Projects/catan
git status
git pull --ff-only origin simulator
printf '%s\n' 'CATAN_FRONTEND_ORIGINS=https://YOUR-PROJECT.vercel.app' > .env
sudo docker-compose -f compose.yaml up -d --build
```

Use the exact Vercel origin: include `https://`, omit the trailing slash, and do not include a path. Multiple approved origins may be comma-separated.

Verify the cross-origin response:

```bash
curl -i -X OPTIONS https://catansim.duckdns.org/games \
  -H 'Origin: https://YOUR-PROJECT.vercel.app' \
  -H 'Access-Control-Request-Method: GET'
```

The response should contain:

```text
access-control-allow-origin: https://YOUR-PROJECT.vercel.app
```

Open the Vercel production URL and confirm Matches, Rooms, My players, SDK download, and player upload all reach the VPS. Preview deployments use different origins and are intentionally blocked until their exact URLs are added to `CATAN_FRONTEND_ORIGINS`.

## Later updates

Every push to the `simulator` branch triggers a Vercel production deployment. Update the VPS for backend changes with:

```bash
cd /home/ubuntu/Projects/catan
git pull --ff-only origin simulator
sudo docker-compose -f compose.yaml up -d --build
curl https://catansim.duckdns.org/health
```
