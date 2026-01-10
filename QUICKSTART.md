# ET Heatmap - Quick Start Guide

## 🚀 Running the Application

### Prerequisites
- Python 3.10+ installed
- Node.js 18+ installed
- `.env` file configured with API keys (see `.env.example`)

### Quick Start (Windows PowerShell)

```powershell
# 1. Install Python dependencies
pip install -e .

# 2. Set up database
python scripts/setup.py

# 3. Install frontend dependencies
cd ui
npm install
cd ..

# 4. Start backend API (in one terminal)
python scripts/run_api.py

# 5. Start frontend UI (in another terminal)
cd ui
npm run dev
```

### Or Use the Startup Script

```powershell
# Run the PowerShell startup script
.\scripts\run_dev.ps1
```

### Access the Application

Once both services are running:

- **Frontend UI**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Required Environment Variables

Create a `.env` file in the project root with:

```env
# Database (defaults to SQLite)
DATABASE_URL=sqlite:///./data/et_heatmap.db

# YouTube API (required for YouTube ingestion)
YOUTUBE_API_KEY=your_youtube_api_key_here

# Reddit API (required for Reddit ingestion)
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret

# Optional: Reddit authentication
REDDIT_USERNAME=your_reddit_username
REDDIT_PASSWORD=your_reddit_password

# Optional: Sentry error tracking
SENTRY_DSN=your_sentry_dsn

# Optional: Debug mode
DEBUG=false
LOG_LEVEL=INFO
```

### First Time Setup

1. **Copy environment template**:
   ```powershell
   Copy-Item .env.example .env
   ```

2. **Edit `.env`** and add your API keys

3. **Install dependencies**:
   ```powershell
   pip install -e .
   cd ui && npm install && cd ..
   ```

4. **Set up database**:
   ```powershell
   python scripts/setup.py
   ```

5. **Run a pipeline** (to generate data):
   ```powershell
   python scripts/run_pipeline.py
   ```

6. **Start services**:
   ```powershell
   # Terminal 1: Backend
   python scripts/run_api.py
   
   # Terminal 2: Frontend
   cd ui && npm run dev
   ```

### Troubleshooting

**Backend won't start:**
- Check that port 8000 is available
- Verify `.env` file exists and has required API keys
- Run `python scripts/validate_config.py` to check configuration

**Frontend won't start:**
- Check that port 5173 is available
- Verify `node_modules` exists (run `npm install` in `ui/` directory)
- Check for TypeScript errors: `cd ui && npm run lint`

**No data in heatmap:**
- Run the pipeline first: `python scripts/run_pipeline.py`
- Check database has data: `python -c "from src.storage.db import get_session; from src.storage.dao.snapshots import SnapshotDAO; print(SnapshotDAO(get_session()).get_latest())"`

**Database errors:**
- Run migrations: `python scripts/migrate_db.py`
- Check database file exists: `Test-Path data/et_heatmap.db`

### Development Tips

- **Hot Reload**: Both frontend and backend support hot reload in development mode
- **API Docs**: Visit http://localhost:8000/docs for interactive API documentation
- **Database Viewer**: Use a SQLite browser to inspect `data/et_heatmap.db`
- **Logs**: Check `logs/app.log` for backend logs
- **Debug Mode**: Set `DEBUG=true` in `.env` for detailed error messages

### Production Deployment

For production deployment, see `docs/DEPLOYMENT.md` for Docker and cloud deployment instructions.
