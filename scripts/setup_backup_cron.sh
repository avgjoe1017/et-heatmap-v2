#!/bin/bash
# Setup automated database backups via cron

# This script sets up automated daily backups at 3 AM
# Adjust the schedule as needed

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Check if cron is available
if ! command -v crontab &> /dev/null; then
    echo "❌ crontab not found. Please install cron."
    exit 1
fi

# Create backup cron job
BACKUP_SCRIPT="$SCRIPT_DIR/backup_database.py"
PYTHON_PATH=$(which python3)

# Cron schedule: Daily at 3 AM
CRON_SCHEDULE="0 3 * * *"

# Create cron entry
CRON_ENTRY="$CRON_SCHEDULE cd $PROJECT_DIR && $PYTHON_PATH $BACKUP_SCRIPT --action backup >> $PROJECT_DIR/logs/backup.log 2>&1"

echo "Setting up automated database backups..."
echo ""
echo "Schedule: Daily at 3:00 AM"
echo "Script: $BACKUP_SCRIPT"
echo "Logs: $PROJECT_DIR/logs/backup.log"
echo ""

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "$BACKUP_SCRIPT"; then
    echo "⚠️  Backup cron job already exists. Updating..."
    # Remove old entry
    crontab -l | grep -v "$BACKUP_SCRIPT" | crontab -
fi

# Add new cron entry
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -

echo "✅ Automated backups configured successfully!"
echo ""
echo "To view cron jobs: crontab -l"
echo "To remove: crontab -l | grep -v 'backup_database.py' | crontab -"
echo ""
echo "Note: Make sure DATABASE_URL is set in your environment or .env file"
