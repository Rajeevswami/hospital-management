#!/bin/bash
# Daily PostgreSQL backup. Keeps last 14 days, deletes older ones automatically.
# Setup as a cron job (run `crontab -e` and add):
#   0 2 * * * /var/www/hospital_system/deploy/backup_db.sh >> /var/log/hospital_system/backup.log 2>&1

set -e

BACKUP_DIR="/var/backups/hospital_system"
DB_NAME="hospital_db"
DB_USER="hospital_user"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=14

mkdir -p "$BACKUP_DIR"

pg_dump -U "$DB_USER" -h 127.0.0.1 "$DB_NAME" | gzip > "$BACKUP_DIR/hospital_db_$TIMESTAMP.sql.gz"

# Delete backups older than retention period
find "$BACKUP_DIR" -name "hospital_db_*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "[$(date)] Backup completed: hospital_db_$TIMESTAMP.sql.gz"
