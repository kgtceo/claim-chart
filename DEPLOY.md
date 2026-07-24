# Deploy

Backend (FastAPI) → **Railway**; frontend (Next.js in `web/`) → **Vercel**. Push to GitHub first.

## Backend → Railway
1. New Project → Deploy from GitHub repo → `claim-chart`. Uses the `Dockerfile`.
2. **Variables:** `ANTHROPIC_API_KEY` (+ `CH_CORS_ORIGINS` = your custom domain if attached).
3. Settings → **Networking → Generate Domain**. Set the domain's target port to the deploy-log port.
4. `GET /health` → `{"status":"ok"}`.

## Frontend → Vercel
1. Import `claim-chart`, **Root Directory = `web`**.
2. Env var `NEXT_PUBLIC_API_URL` = the Railway URL.
3. Deploy. Optionally attach `claim-chart.kareemghazal.com` and add it to `CH_CORS_ORIGINS`.
