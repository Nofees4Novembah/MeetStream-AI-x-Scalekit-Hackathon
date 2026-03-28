@echo off
setlocal

echo Starting MeetStream services...

REM Get the project root directory
set ROOT=%~dp0

REM T1 — post-call webhook server (port 3001)
start "Webhook Server :3001" cmd /k "cd /d "%ROOT%" && uv run python server.py"

REM T2 — dashboard backend (port 3000)
start "Backend API :3000" cmd /k "cd /d "%ROOT%" && uv run uvicorn backend.main:app --port 3000 --reload"

REM T3 — real-time bridge / AI agent (port 8000)
start "Bridge AI :8000" cmd /k "cd /d "%ROOT%" && uv run uvicorn app.server:app --port 8000 --reload"

REM T4 — Next.js dashboard (port 3002)
start "Dashboard :3002" cmd /k "cd /d "%ROOT%dashboard" && npm run dev -- --port 3002"

echo.
echo All services started in separate windows.
echo.
echo Once ngrok is running, paste its HTTPS URL into .env as WEBHOOK_BASE_URL,
echo then restart the "Webhook Server :3001" window.
echo.
echo Starting ngrok now (exposing port 3001)...
start "ngrok :3001" cmd /k "ngrok http 3001"

echo.
echo Done! Check the window titles to find each service.
pause
