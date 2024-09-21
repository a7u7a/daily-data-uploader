import csv
from datetime import datetime
from collections import defaultdict

def parse_daily_tracker_csv(file_path):
    data = defaultdict(lambda: defaultdict(dict))
    
    with open(file_path, 'r') as csvfile:
        # Skip metadata lines
        for _ in range(6):
            next(csvfile)
        
        reader = csv.reader(csvfile)
        headers = next(reader)
        
        # Replace empty headers with correct values
        headers[0] = 'Activity'
        headers[1] = 'Group'
        
        
        # Parse dates
        dates = [datetime.strptime(date, '%d-%m-%y') for date in headers[2:]]
        
        for row in reader:
            activity, group = row[:2]
            for date, duration in zip(dates, row[2:]):
                if duration:  # Skip empty durations
                    data[date.strftime('%Y-%m-%d')][group] = {
                        'activity': activity,
                        'duration': int(duration)
                    }
    
    return data