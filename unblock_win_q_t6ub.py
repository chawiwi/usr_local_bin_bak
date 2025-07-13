#!/usr/bin/env python3

import os
import time
from datetime import datetime, timedelta

# Directory to check
directory = "/RACKLOG/t6ub/queue"
# Log file path
log_file_path = "/home/huy/workers/unblocking_win_queue_t6ub.log"

def ensure_log_file_exists(log_path):
    # Check if the directory for the log file exists, if not, create it
    log_dir = os.path.dirname(log_path)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Check if the log file exists, if not, create it
    if not os.path.exists(log_path):
        open(log_path, 'w').close()

def delete_old_files(dir_path):
    # Ensure the log file exists
    ensure_log_file_exists(log_file_path)
    
    # Get the current time
    now = time.time()
    # Get list of all files in the directory
    files = [os.path.join(dir_path, f) for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))]

    if not files:
        print("No files found in the directory.")
        return

    # Sort files by creation time
    files.sort(key=lambda x: os.path.getctime(x))
    
    # Delete files older than 20 minutes
    for file in files:
        creation_time = os.path.getctime(file)
        creation_time_formatted = datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d %H:%M:%S')
        
        # Print the file and its creation time for troubleshooting
        print(f"Checking file: {file}, creation time: {creation_time_formatted}")

        if now - creation_time > 20 * 60:
            os.remove(file)
            with open(log_file_path, "a") as log_file:
                log_file.write(f"Deleted {file} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            print(f"Deleted {file} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    delete_old_files(directory)

