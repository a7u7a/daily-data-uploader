#!/bin/bash
export DAILY_TRACKER_EXPORT_DIR="/Users/userfriendly/Documents/daily-export-data"
export DAILY_TRACKER_LOG_DIR="$DAILY_TRACKER_EXPORT_DIR/logs"

# Ensure the log directory exists
mkdir -p "$DAILY_TRACKER_LOG_DIR"

/usr/bin/python3 ./app.py