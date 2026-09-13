#!/bin/bash
# Start script for Clinic Management App

echo "Starting Clinic Management System..."

# Ensure Node.js is on PATH (installed at ~/.local/node/bin on this machine)
export PATH="$HOME/.local/node/bin:$PATH"
command -v node >/dev/null 2>&1 || { echo "ERROR: node not found. Install Node.js 18+ first."; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "ERROR: python3 not found."; exit 1; }

# Shared secret between frontend and backend API. Override in production:
#   API_KEY="strong-random-value" ./start.sh
export API_KEY="${API_KEY:-dev-key}"
export FLASK_API_KEY="${FLASK_API_KEY:-$API_KEY}"
if [ "$API_KEY" = "dev-key" ]; then
  echo "WARNING: using default dev API key. Set API_KEY env var in production."
fi

# Persistent session secret (survives restarts so logins aren't wiped)
if [ ! -f ".session_secret" ]; then
  python3 -c "import secrets; print(secrets.token_hex(32))" > .session_secret
  chmod 600 .session_secret
fi
export SESSION_SECRET="$(cat .session_secret)"

# Start Flask backend
cd backend
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1
echo "Starting Flask backend on port 5001..."
FLASK_DEBUG=1 PORT=5001 python app.py &
BACKEND_PID=$!
cd ..

# Start Node.js frontend
cd frontend
if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install > /dev/null 2>&1
fi
echo "Starting Node.js frontend on port 3000..."
npm start &
FRONTEND_PID=$!
cd ..

echo ""
echo "=========================================="
echo "Clinic Management System is running!"
echo "=========================================="
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:5001/api"
echo ""
echo "Press Ctrl+C to stop both servers"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait