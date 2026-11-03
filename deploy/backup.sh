#!/usr/bin/env bash
# Daily backup of the SQLite database and uploaded files.
# Schedule as the "assam" user with `crontab -e`:
#   30 2 * * * bash /home/assam/assam_healthcare/deploy/backup.sh >> /home/assam/backups/backup.log 2>&1
# Copy the backups folder off the server regularly (see LAUNCH_CHECKLIST.md).
set -euo pipefail

APP_DIR=/home/assam/assam_healthcare
BACKUP_DIR=/home/assam/backups
KEEP_DAYS=14
STAMP=$(date +%Y-%m-%d_%H%M)

mkdir -p "$BACKUP_DIR"

# Python's sqlite3 backup API makes a consistent copy even while the site
# is running, and does not need the sqlite3 command-line tool.
/usr/bin/python3 - "$APP_DIR/db.sqlite3" "$BACKUP_DIR/db-$STAMP.sqlite3" <<'PY'
import sqlite3, sys
source = sqlite3.connect(sys.argv[1])
target = sqlite3.connect(sys.argv[2])
with target:
    source.backup(target)
target.close()
source.close()
PY

tar -czf "$BACKUP_DIR/media-$STAMP.tar.gz" -C "$APP_DIR" media

# Delete backups older than KEEP_DAYS days.
find "$BACKUP_DIR" -name 'db-*.sqlite3' -mtime +"$KEEP_DAYS" -delete
find "$BACKUP_DIR" -name 'media-*.tar.gz' -mtime +"$KEEP_DAYS" -delete

echo "$(date) backup complete: db-$STAMP.sqlite3, media-$STAMP.tar.gz"
