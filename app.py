import os
import shutil
import logging
from datetime import datetime
from csv_parser import parse_daily_data_csv
from supabase import create_client, Client, ClientOptions

EXPORT_DIR = os.getenv('DAILY_UPLOADER_EXPORT_DIR')
PROCESSED_DIR = os.path.join(EXPORT_DIR, 'processed')
LAST_UPDATE_FILE = os.path.join(EXPORT_DIR, "last_update.txt")
LOG_DIR = os.getenv('DAILY_UPLOADER_LOG_DIR')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
USER_EMAIL = os.getenv('SUPABASE_USER_EMAIL')
USER_PASSWORD = os.getenv('SUPABASE_USER_PASSWORD')

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY, options=ClientOptions(auto_refresh_token=False))

required_vars = ['DAILY_UPLOADER_EXPORT_DIR', 'DAILY_UPLOADER_LOG_DIR','SUPABASE_URL','SUPABASE_KEY','SUPABASE_USER_EMAIL','SUPABASE_USER_PASSWORD']
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

if not os.path.exists(PROCESSED_DIR):
    os.makedirs(PROCESSED_DIR)

logging.basicConfig(
    filename=os.path.join(LOG_DIR, 'daily-data-uploader.log'), 
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def sign_in_user():
    try:
        response = supabase.auth.sign_in_with_password({
            "email": USER_EMAIL,
            "password": USER_PASSWORD
        })
        return response.user.id
    except Exception as e:
        logging.error(f"Error signing in: {str(e)}")
        raise

def get_last_update_time():
        if os.path.exists(LAST_UPDATE_FILE):
            with open(LAST_UPDATE_FILE, 'r') as f:
                return datetime.fromisoformat(f.read().strip())
        else:
            current_time = datetime.now()
            set_last_update_time(current_time)
            return current_time
        
def set_last_update_time(dt):
    os.makedirs(os.path.dirname(LAST_UPDATE_FILE), exist_ok=True)
    with open(LAST_UPDATE_FILE, 'w') as f:
        f.write(dt.isoformat())
        
def get_new_csv_files():
    return [f for f in os.listdir(EXPORT_DIR) if f.endswith('.csv')]

def process_file(filename):
    file_path = os.path.join(EXPORT_DIR, filename)
    logging.info(f"Processing file: {filename}")
    try:
        data = parse_daily_data_csv(file_path)
        update_supabase(data)
        shutil.move(file_path, os.path.join(PROCESSED_DIR, filename))
        logging.info(f"Successfully processed and moved file: {filename}")
    except Exception as e:
        logging.error(f"Error processing file {filename}: {str(e)}")
    
def get_or_create_groups(group_names, user_id):
    existing_groups = supabase.table('groups').select('id', 'name').eq('user_id', user_id).execute()
    existing_groups_dict = {group['name']: group['id'] for group in existing_groups.data}

    groups_to_create = [{'name': name, 'user_id': user_id} for name in group_names if name not in existing_groups_dict]

    if groups_to_create:
        new_groups = supabase.table('groups').insert(groups_to_create).execute()
        for group in new_groups.data:
            existing_groups_dict[group['name']] = group['id']

    return existing_groups_dict

    # Bulk update
def update_supabase(data):
    logging.info("Updating Supabase")
    try:
        user_id = sign_in_user()
        if not user_id:
            raise Exception("Failed to authenticate user")

        all_group_names = set(group_name for groups in data.values() for group_name in groups.keys())

        group_id_map = get_or_create_groups(all_group_names, user_id)

        records_to_insert = []
        records_to_update = []

        existing_records = supabase.table('time_tracking').select('id', 'date', 'activity').eq('user_id', user_id).execute()
        existing_records_dict = {(record['date'], record['activity']): record['id'] for record in existing_records.data}

        for date, groups in data.items():
            for group_name, activity_details in groups.items():
                record = {
                    'date': date,
                    'group_id': group_id_map[group_name],
                    'activity': activity_details['activity'],
                    'duration': activity_details['duration'],
                    'user_id': user_id
                }

                if (date, activity_details['activity']) in existing_records_dict:
                    record['id'] = existing_records_dict[(date, activity_details['activity'])]
                    records_to_update.append(record)
                else:
                    records_to_insert.append(record)

        if records_to_insert:
            supabase.table('time_tracking').insert(records_to_insert).execute()
            logging.info(f"Inserted {len(records_to_insert)} new records")

        if records_to_update:
            supabase.table('time_tracking').upsert(records_to_update).execute()
            logging.info(f"Updated {len(records_to_update)} existing records")

        logging.info("Supabase update completed successfully")
    except Exception as e:
        logging.error(f"Error updating Supabase: {str(e)}")
        raise

def main():
    logging.info("Starting Daily Uploader Updater")
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
                
        logging.info(f"Update completed. New last update time: {last_update}")        
        set_last_update_time(last_update)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
    finally:
        logging.info("Daily Updater finished. Exiting.")

if __name__ == "__main__":
    main()