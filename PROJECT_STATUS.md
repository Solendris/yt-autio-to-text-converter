# Project Status & Migration Notes

**Date:** 2026-01-17
**Goal:** Migrate Backend to Raspberry Pi & Refactor

## Migration Summary
We successfully migrated the backend to Raspberry Pi using Docker and connected it to the GitHub Pages frontend via Cloudflare Tunnel.

### Key Changes
1.  **Backend Configuration**:
    - Defined `docker-compose.yml` with port `5000:5000` and `restart: unless-stopped`.
    - Increased Gunicorn timeout to 600s for Raspberry Pi performance.

2.  **Frontend Updates**:
    - **Configurable API URL**: `api.js` loads `VITE_API_BASE_URL` from `.env`.
    - **Connection Logging**: Added detailed logs (`[API] ...`) for fetch errors to help diagnose connection issues.
    - **Health Check**: `App.jsx` checks backend health on startup and logs result to console.

3.  **Connectivity & Documentation**:
    - **Cloudflare Tunnel**: Used to bypass NAT and provide HTTPS (fixes Mixed Content).
    - **Documentation**: Created `RASPBERRY_PI_SETUP.md` with step-by-step deployment guide.

## Deployment & Verification Guide
(From Walkthrough)

1.  **Deploy to Pi**:
    - Transfer files (`scp`), ensure `.env` keys are present.
    - Run `docker-compose up -d --build`.
2.  **Verify Backend**:
    - Check logs: `docker-compose logs -f`.
    - Test health: `curl http://localhost:5000/api/health`.
3.  **Connect Frontend**:
    - Update frontend `.env` with the Cloudflare Tunnel URL.
    - Run `cmd /c npm run build` and `cmd /c npm run deploy`.
    - Check browser console for `[API] Health check passed`.

## Debugging & Troubleshooting "Gotchas"
(Crucial for future maintainence)

### 1. Mixed Content Error (CORS-like symptoms)
*   **Problem**: Frontend (GitHub Pages) is HTTPS, but Pi local IP is HTTP. Browser blocks the connection.
*   **Solution**: **Cloudflare Tunnel**. It provides a free HTTPS URL.
    *   Command: `cloudflared tunnel --url http://localhost:5000`

### 2. "Worker Timeout" / 502 Bad Gateway
*   **Problem**: Raspberry Pi is slower than big servers. Long videos take >30s to process. Gunicorn kills the worker, causing a 502 error (often mistaken for CORS).
*   **Solution**: Increased timeout to 10 minutes in `docker-compose.yml`.
    ```yaml
    command: gunicorn --bind 0.0.0.0:5000 --timeout 600 run:app
    ```

### 3. Deploying from Windows (PowerShell Policy)
*   **Problem**: `npm run deploy` fails because running scripts is disabled in PowerShell.
*   **Solution**: Run via CMD: `cmd /c npm run deploy` or flush DNS/Policy.

## Next Steps (Refactoring Plan)
*   [ ] Refactor modules (cleanup `app/` structure).
*   [ ] Remove unused files (cleanup `run.py` vs `wsgi.py` confusion, old scripts).
*   [ ] Optimize imports.
