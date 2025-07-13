import os
import shutil
from datetime import datetime

# Source sf config folder
source_folder = '/SFC/NetApp/Response'

# Destination folder to store all sf config copies
destination_path = '/project/CP_config_temp'

current_datetime = datetime.now()
formatted_datetime = current_datetime.strftime('%Y-%m-%d %H:%M:%S:%f')

# Error handling if the source folder does not exist
if not os.path.exists(source_folder):
	print(f"Source folder '{source_folder}' does not exist. | {formatted_datetime}")
	exit(1)

# Create the destination folder if it doesn't exist
if not os.path.exists(destination_path):
	os.makedirs(destination_path)

# Go through every file in source_folder
for filename in os.listdir(source_folder):
	current_datetime = datetime.now()
	formatted_datetime = current_datetime.strftime('%Y-%m-%d %H:%M:%S:%f')
	source_path = os.path.join(source_folder, filename)
	destination_file = os.path.join(destination_path, filename)
	
	# Copy file to Destination folder if the file is .txt file
	if os.path.isfile(source_path) and filename.endswith('.txt'):
		shutil.copy(source_path, destination_file)
		print(f"Successfully copied '{filename}' to '{destination_path}' | {formatted_datetime}")

# Exit the program with a success code
exit(0)
