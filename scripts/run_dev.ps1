# PowerShell script to run ET Heatmap in development mode
# Starts both backend API and frontend UI

Write-Host "🚀 Starting ET Heatmap Development Environment" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env exists
if (-not (Test-Path .env)) {
    Write-Host "⚠️  .env file not found." -ForegroundColor Yellow
    if (Test-Path .env.example) {
        Copy-Item .env.example .env
        Write-Host "✓ Created .env from .env.example" -ForegroundColor Green
        Write-Host "⚠️  Please edit .env and add your API keys before continuing!" -ForegroundColor Yellow
        Write-Host "   Required: YOUTUBE_API_KEY, REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET" -ForegroundColor Yellow
        $response = Read-Host "Press Enter to continue after editing .env (or Ctrl+C to exit)"
    } else {
        Write-Host "❌ .env.example not found. Please create .env manually." -ForegroundColor Red
        exit 1
    }
}

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.10+" -ForegroundColor Red
    exit 1
}

# Check Node.js
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✓ Node.js found: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js not found. Please install Node.js 18+" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "1️⃣  Installing Python dependencies..." -ForegroundColor Cyan
python -m pip install -e . --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✓ Python dependencies installed" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Python dependency installation had issues" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "2️⃣  Setting up database..." -ForegroundColor Cyan
python scripts/setup.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "   ⚠️  Database setup had issues, but continuing..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "3️⃣  Installing frontend dependencies..." -ForegroundColor Cyan
Set-Location ui
if (-not (Test-Path node_modules)) {
    npm install
    Write-Host "   ✓ Frontend dependencies installed" -ForegroundColor Green
} else {
    Write-Host "   ✓ Frontend dependencies already installed" -ForegroundColor Green
}
Set-Location ..

Write-Host ""
Write-Host "4️⃣  Starting services..." -ForegroundColor Cyan
Write-Host ""
Write-Host "   Backend API: http://localhost:8000" -ForegroundColor White
Write-Host "   Frontend UI: http://localhost:5173" -ForegroundColor White
Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "   Press Ctrl+C to stop all services" -ForegroundColor Yellow
Write-Host ""

# Start backend
Write-Host "Starting backend API..." -ForegroundColor Cyan
Start-Process -NoNewWindow python -ArgumentList "scripts/run_api.py"

# Wait for backend to start
Start-Sleep -Seconds 3

# Start frontend
Write-Host "Starting frontend UI..." -ForegroundColor Cyan
Set-Location ui
Start-Process -NoNewWindow npm -ArgumentList "run", "dev"
Set-Location ..

Write-Host ""
Write-Host "✅ Services started!" -ForegroundColor Green
Write-Host "   Backend running in background. Check logs if needed." -ForegroundColor Gray
Write-Host "   Frontend should open automatically in your browser." -ForegroundColor Gray
Write-Host ""
Write-Host "   To stop services, close the terminal windows or press Ctrl+C" -ForegroundColor Yellow
