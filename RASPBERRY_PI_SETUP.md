# Raspberry Pi Deployment Guide

This guide explains how to deploy the YouTube Summarizer backend to a Raspberry Pi using Docker.

## Prerequisites

- Raspberry Pi (3B+ or newer recommended)
- Docker and Docker Compose installed
- Internet connection

## 1. Setup Backend on Raspberry Pi

1.  **Transfer Files**: Copy the project files to your Raspberry Pi.
    ```bash
    # Example using scp
    scp -r yt-autio-to-text-converter pi@raspberrypi.local:/home/pi/
    ```

2.  **Navigate to Directory**:
    ```bash
    cd yt-autio-to-text-converter/local
    ```

3.  **Configure Environment**:
    - Ensure `.env` is present and contains your API keys (`PERPLEXITY_API_KEY`, etc.).

4.  **Run with Docker**:
    ```bash
    docker-compose up -d --build
    ```
    - The backend will start on port `5000`.
    - Check logs: `docker-compose logs -f`

5.  **Verify Local Connection**:
    - Run: `curl http://localhost:5000/api/health`
    - You should see a JSON response.
    - You should see a JSON response.

## 2. Managing Code with Git (Updating & Switching Branches)

Instead of copying files manually via `scp`, you can use Git directly on the Pi.

1.  **First Time Setup (Clone)**:
    If you haven't cloned the repo on the Pi yet:
    ```bash
    cd /home/pi/
    # If the folder exists from scp, rename it to backup just in case
    mv yt-autio-to-text-converter yt-autio-to-text-converter.bak
    
    # Clone your repo (replace URL with your actual repo URL)
    git clone https://github.com/YOUR_USERNAME/yt-autio-to-text-converter.git
    cd yt-autio-to-text-converter/local
    ```

2.  **Updating to a Specific Branch**:
    ```bash
    # 1. Fetch latest changes from all branches
    git fetch --all

    # 2. Switch to the branch you want (e.g., 'main' or 'feature-branch')
    git checkout <branch_name>

    # 3. Pull the latest code
    git pull origin <branch_name>
    ```

3.  **Apply Changes (Rebuild Docker)**:
    After any code change, you must restart the containers:
    ```bash
    docker-compose down
    docker-compose up -d --build
    ```

## 3. Expose Backend (Persistent Access)

To allow the frontend (GitHub Pages) to access your Raspberry Pi reliability, we will use **Ngrok** with your free static domain.

1.  **Transfer Setup Script**: Use the provided `setup_ngrok.sh` script.
    ```bash
    # Run this on your Raspberry Pi inside the project directory
    chmod +x setup_ngrok.sh
    ./setup_ngrok.sh
    ```

2.  **Follow Instructions**:
    - The script will ask for your **Ngrok Authtoken**. You can find it here: [https://dashboard.ngrok.com/get-started/your-authtoken](https://dashboard.ngrok.com/get-started/your-authtoken).
    - It will automatically configure the tunnel for `ridgy-collin-gardenless.ngrok-free.dev`.

3.  **Verify**:
    - Open `https://ridgy-collin-gardenless.ngrok-free.dev/api/health` in your browser.
    - You should see the health check response.

## 3. Configure Frontend

1.  **Update `.env`** (or create one) in `frontend/`:
    ```
    VITE_API_BASE_URL=https://your-raspberry-pi-url.com/api
    ```
    *Note: Append `/api` to the URL.*

2.  **Rebuild Frontend**:
    ```bash
    cd frontend
    npm run build
    npm run deploy
    ```

## Troubleshooting

- **Check Console Logs**: Open your browser's Developer Tools (F12) -> Console.
- Look for `[API] Health check passed` or connection errors.
- If you see `Failed to fetch`, check:
    - Is the Pi running?
    - Is the URL in `VITE_API_BASE_URL` correct?
    - Are you mixing HTTPS (frontend) with HTTP (backend)? use Cloudflare Tunnel to fix this.
