#!/bin/bash
# Development startup script - runs both backend and frontend

set -e

echo "🚀 Starting ET Heatmap Development Environment"
echo "=============================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✓ Created .env from .env.example"
        echo "⚠️  Please edit .env and add your API keys before continuing!"
        echo "   Required: YOUTUBE_API_KEY, REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET"
        read -p "Press Enter to continue after editing .env..."
    else
        echo "❌ .env.example not found. Please create .env manually."
        exit 1
    fi
fi

# Check Python installation
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.10+"
    exit 1
fi

PYTHON_CMD=python
if ! command -v python &> /dev/null; then
    PYTHON_CMD=python3
fi

# Check Node.js installation
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 18+"
    exit 1
fi

echo "1️⃣  Installing Python dependencies..."
if [ -f "pyproject.toml" ]; then
    $PYTHON_CMD -m pip install -e . --quiet || pip install -e . --quiet
    echo "   ✓ Python dependencies installed"
else
    echo "   ⚠️  pyproject.toml not found, skipping Python dependencies"
fi

echo ""
echo "2️⃣  Setting up database..."
$PYTHON_CMD scripts/setup.py || {
    echo "   ⚠️  Database setup had issues, but continuing..."
}

echo ""
echo "3️⃣  Installing frontend dependencies..."
cd ui
if [ ! -d "node_modules" ]; then
    npm install
    echo "   ✓ Frontend dependencies installed"
else
    echo "   ✓ Frontend dependencies already installed"
fi
cd ..

echo ""
echo "4️⃣  Starting services..."
echo ""
echo "   Backend API will start on: http://localhost:8000"
echo "   Frontend UI will start on: http://localhost:5173"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "   Press Ctrl+C to stop all services"
echo ""

# Start backend in background
echo "Starting backend API..."
$PYTHON_CMD scripts/run_api.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend
echo "Starting frontend UI..."
cd ui
npm run dev &
FRONTEND_PID=$!
cd ..

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    echo "✓ Services stopped"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Wait for both processes
wait
