#!/bin/bash
# Setup script to install daily cleanup cron job

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLEANUP_SCRIPT="${SCRIPT_DIR}/cleanup_sophia_daily.sh"
CRON_SCHEDULE="0 3 * * *"  # Daily at 3 AM

echo "Setting up Sophia daily cleanup cron job..."

# Check if cleanup script exists
if [ ! -f "${CLEANUP_SCRIPT}" ]; then
    echo "Error: Cleanup script not found at ${CLEANUP_SCRIPT}"
    exit 1
fi

# Create cron entry
CRON_CMD="${CRON_SCHEDULE} ${CLEANUP_SCRIPT} >> ${SCRIPT_DIR}/../logs/cleanup/cron.log 2>&1"

# Check if cron entry already exists
if crontab -l 2>/dev/null | grep -q "${CLEANUP_SCRIPT}"; then
    echo "Cleanup cron job already exists. Updating..."
    # Remove old entry
    (crontab -l 2>/dev/null | grep -v "${CLEANUP_SCRIPT}") | crontab -
fi

# Add new cron entry
(crontab -l 2>/dev/null; echo "${CRON_CMD}") | crontab -

echo "Cron job installed successfully!"
echo "Schedule: ${CRON_SCHEDULE} (daily at 3 AM)"
echo "Script: ${CLEANUP_SCRIPT}"
echo ""
echo "To verify, run: crontab -l"
echo "To remove, run: crontab -l | grep -v cleanup_sophia_daily.sh | crontab -"
echo ""
echo "Manual run: ${CLEANUP_SCRIPT}"
