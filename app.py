import os
import shutil
import logging
from datetime import datetime
from csv_parser import parse_daily_tracker_csv

EXPORT_DIR = os.getenv('DAILY_TRACKER_EXPORT_DIR')
PROCESSED_DIR = os.path.join(EXPORT_DIR, 'processed')
LAST_UPDATE_FILE = os.path.join(EXPORT_DIR, "last_update.txt")
LOG_DIR = os.getenv('DAILY_TRACKER_LOG_DIR')

required_vars = ['DAILY_TRACKER_EXPORT_DIR', 'DAILY_TRACKER_LOG_DIR']
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Ensure the processed directory exists
if not os.path.exists(PROCESSED_DIR):
    os.makedirs(PROCESSED_DIR)

# Set up logging configuration
logging.basicConfig(
    filename=os.path.join(LOG_DIR, 'timetracker.log'), 
    level=logging.INFO,  # Set to DEBUG to capture all types of logs
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
def get_last_update_time():
        if os.path.exists(LAST_UPDATE_FILE):
            with open(LAST_UPDATE_FILE, 'r') as f:
                return datetime.fromisoformat(f.read().strip())
        else:
            # If the file doesn't exist, create it with the current time
            current_time = datetime.now()
            set_last_update_time(current_time)
            return current_time
        
def set_last_update_time(dt):
    # Ensure the directory exists
    os.makedirs(os.path.dirname(LAST_UPDATE_FILE), exist_ok=True)
    with open(LAST_UPDATE_FILE, 'w') as f:
        f.write(dt.isoformat())
        
def get_new_csv_files():
    return [f for f in os.listdir(EXPORT_DIR) if f.endswith('.csv')]

def process_file(filename):
    file_path = os.path.join(EXPORT_DIR, filename)
    logging.info(f"Processing file: {filename}")
    try:
        data = parse_daily_tracker_csv(file_path)
        update_supabase(data)
        shutil.move(file_path, os.path.join(PROCESSED_DIR, filename))
        logging.info(f"Successfully processed and moved file: {filename}")
    except Exception as e:
        logging.error(f"Error processing file {filename}: {str(e)}")
    
def update_supabase(data):
    logging.info("Updating Supabase (dry)")
    try:
          # Placeholder for Supabase update logic
          for date, activities in data.items():
              for activity, details in activities.items():
                  logging.info(f"Would update: {date} - {activity}: {details}")
          
          # Example of how you might use the Supabase client:
          # existing_data = supabase.table('time_tracking').select('*').execute()
          # for date, activities in data.items():
          #     for activity, details in activities.items():
          #         # Check if data exists and update or insert as needed
          #         supabase.table('time_tracking').upsert({
          #             'date': date,
          #             'activity': activity,
          #             'group': details['group'],
          #             'duration': details['duration']
          #         }).execute()
          logging.info("Supabase update completed successfully")
    except Exception as e:
        logging.error(f"Error updating Supabase: {str(e)}")

def main():
    logging.info("Starting Daily Tracker Updater")
    try:
      last_update = get_last_update_time()
      logging.info(f"Last update time: {last_update}")
      new_files = get_new_csv_files()
      logging.info(f"Found {len(new_files)} new CSV files")
      
      for file in new_files:
          file_path = os.path.join(EXPORT_DIR, file)
          file_mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
          if file_mod_time > last_update:
              process_file(file)
              last_update = file_mod_time
      
      set_last_update_time(last_update)
      logging.info(f"Update completed. New last update time: {last_update}")
    except Exception as e:
      logging.error(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    main()