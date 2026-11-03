#!/usr/bin/env bash
# Deploy the latest code on the VPS. Run as the "assam" user:
#   bash ~/assam_healthcare/deploy/update.sh
set -euo pipefail

APP_DIR=/home/assam/assam_healthcare
VENV=/home/assam/venv

cd "$APP_DIR"

echo "Backing up the database first..."
bash "$APP_DIR/deploy/backup.sh"

git pull --ff-only
"$VENV/bin/pip" install -r requirements.txt

# manage.py needs the production settings from the environment file.
set -a
# shellcheck disable=SC1091
source /etc/assam_healthcare.env
set +a

"$VENV/bin/python" manage.py migrate --noinput
"$VENV/bin/python" manage.py collectstatic --noinput
"$VENV/bin/python" manage.py check --deploy

sudo systemctl restart assam_healthcare
echo "Done. The site has been restarted."
