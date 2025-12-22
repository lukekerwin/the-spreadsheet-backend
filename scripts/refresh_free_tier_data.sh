#!/bin/bash
# ============================================
# Free Tier Data Refresh Script
# ============================================
# Copies data from premium tables to free tier snapshot tables.
# Run every Tuesday at 11:30 PM ET after dbt models complete.
# ============================================

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load environment variables if .env exists (check multiple locations)
if [ -f "$SCRIPT_DIR/../.env" ]; then
    export $(grep -v '^#' "$SCRIPT_DIR/../.env" | xargs)
elif [ -f "$SCRIPT_DIR/../../.env" ]; then
    export $(grep -v '^#' "$SCRIPT_DIR/../../.env" | xargs)
fi

# Use production database if --prod flag is passed
if [ "$1" = "--prod" ]; then
    DB_HOST="${DB_HOST_PROD:-$DB_HOST}"
    DB_PORT="${DB_PORT_PROD:-$DB_PORT}"
    DB_USER="${DB_USER_PROD:-$DB_USER}"
    DB_PASSWORD="${DB_PASSWORD_PROD:-$DB_PASSWORD}"
    DB_NAME="${DB_NAME_PROD:-$DB_NAME}"
    echo "Using PRODUCTION database"
else
    echo "Using LOCAL database (pass --prod for production)"
fi

# Build connection string
export PGPASSWORD="$DB_PASSWORD"

echo "============================================"
echo "Free Tier Data Refresh"
echo "============================================"
echo "Host: $DB_HOST"
echo "Database: $DB_NAME"
echo "Started at: $(date)"
echo "============================================"

# Run the SQL script
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$SCRIPT_DIR/refresh_free_tier_data.sql"

echo "============================================"
echo "Completed at: $(date)"
echo "============================================"
