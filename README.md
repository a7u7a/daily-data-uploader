# daily-data-uploader

Upload data exported by [Daily Time Tracker](https://dailytimetracking.com/) to a Supabase project.

## How I run this

- Create a new virtual env: `python3 -m venv daily-tracker-env` and activate `source daily-tracker-env/bin/activate`
- Install dependencies: `pip install -r requirements.txt`
- Create a new bash file called `run-daily-tracker.sh` like this:

```bash
#!/bin/bash
export DAILY_TRACKER_EXPORT_DIR="/your-export-path-here"
export DAILY_TRACKER_LOG_DIR="$DAILY_TRACKER_EXPORT_DIR/logs"
export SUPABASE_URL="https://your-project-url-here.supabase.co/"
export SUPABASE_KEY="your-key-here"

mkdir -p "$DAILY_TRACKER_LOG_DIR"
source daily-tracker-env/bin/activate
/usr/bin/python3 ./app.py
deactivate
```

- Register in chron job: To-Do
