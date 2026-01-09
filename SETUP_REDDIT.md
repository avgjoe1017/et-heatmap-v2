# Reddit API Setup Guide

## Getting Reddit API Credentials

1. Go to https://www.reddit.com/prefs/apps
2. Click "create another app..." or "create an app"
3. Fill in the form:
   - **Name**: `et-heatmap` (or any name you prefer)
   - **App type**: Select **"script"** for personal scripts
   - **Description**: "Entertainment Feelings Heatmap data ingestion"
   - **About URL**: (optional)
   - **Redirect URI**: `http://localhost:8000` (required but not used for script apps)
4. Click "create app"
5. You'll see:
   - **client_id**: The string under the app name (e.g., `dnOnguwIgflNw5KoVi8sIg`)
   - **client_secret**: The "secret" field (e.g., `wCiIBM8DY7AEojauXFePHKaE_45OPA`)

## Setting Up Credentials

### Option 1: Environment Variables (Recommended)

Create a `.env` file in the project root:

```bash
# Reddit API Credentials
REDDIT_CLIENT_ID=dnOnguwIgflNw5KoVi8sIg
REDDIT_CLIENT_SECRET=wCiIBM8DY7AEojauXFePHKaE_45OPA
REDDIT_USERNAME=Slight_Television486
REDDIT_PASSWORD=regguy1017
REDDIT_USER_AGENT=gaze_scraper/0.1 by Slight_Television486
```

**Important**: 
- Never commit `.env` to git (it's already in `.gitignore`)
- Keep your credentials secure
- The user_agent should follow the format: `app_name/version by reddit_username`

### Option 2: System Environment Variables

On Windows (PowerShell):
```powershell
$env:REDDIT_CLIENT_ID="dnOnguwIgflNw5KoVi8sIg"
$env:REDDIT_CLIENT_SECRET="wCiIBM8DY7AEojauXFePHKaE_45OPA"
$env:REDDIT_USERNAME="Slight_Television486"
$env:REDDIT_PASSWORD="regguy1017"
$env:REDDIT_USER_AGENT="gaze_scraper/0.1 by Slight_Television486"
```

On Linux/Mac:
```bash
export REDDIT_CLIENT_ID="dnOnguwIgflNw5KoVi8sIg"
export REDDIT_CLIENT_SECRET="wCiIBM8DY7AEojauXFePHKaE_45OPA"
export REDDIT_USERNAME="Slight_Television486"
export REDDIT_PASSWORD="regguy1017"
export REDDIT_USER_AGENT="gaze_scraper/0.1 by Slight_Television486"
```

## Authentication Types

### Script App (Recommended for Personal Use)
- Requires: `client_id`, `client_secret`, `username`, `password`
- Higher rate limits (60 requests/minute)
- Can access user-specific data
- Best for personal scripts and data collection

### Read-Only (No Login)
- Requires: `client_id`, `client_secret` only
- Lower rate limits (30 requests/minute)
- Public data only
- Good for simple scraping

## Testing Reddit Connection

After setting up credentials, test the connection:

```bash
python -c "from src.pipeline.steps.ingest_reddit import ingest_reddit; from datetime import datetime, timedelta; print('Testing Reddit connection...'); items = ingest_reddit(datetime.utcnow() - timedelta(days=1), datetime.utcnow()); print(f'Success! Retrieved {len(items)} items')"
```

Or run a full pipeline test:
```bash
python -m src.pipeline.daily_run
```

## Rate Limits

Reddit API rate limits:
- **Script app**: 60 requests per minute
- **Read-only**: 30 requests per minute

The pipeline respects these limits automatically through PRAW. If you hit rate limits, you'll see warnings in the logs.

## Troubleshooting

### "invalid_client" Error
- Check that `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` are correct
- Ensure no extra spaces or quotes

### "invalid_grant" Error
- Check that `REDDIT_USERNAME` and `REDDIT_PASSWORD` are correct
- Verify your Reddit account password (or use app password if 2FA enabled)

### "Forbidden" Error
- Check that `REDDIT_USER_AGENT` follows the format: `app_name/version by username`
- Ensure your Reddit account has access (not banned/suspended)

### No Data Retrieved
- Check that subreddits in `config/subreddits.txt` are valid
- Verify the time window overlaps with recent posts
- Check logs for specific error messages

## Security Notes

⚠️ **Never commit credentials to git!**

- `.env` is already in `.gitignore`
- Don't share credentials in screenshots or documentation
- Rotate credentials if accidentally exposed
- Use environment variables, not hardcoded values
