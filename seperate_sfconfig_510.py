import os
import re
import shutil

# Source folder containing .txt files
source_folder = '/project/CP_config_temp'
destination_path_T6J = '/WIN/T6J/sfconfig'
destination_path_T6K = '/WIN/t6k/sfconfig'
destination_path_T6H = '/WIN/T6H/sfconfig'

# Check if the source folder exists
if not os.path.exists(source_folder):
    exit(1)

pattern = r'MODEL=([^=\n]+)'

for filename in os.listdir(source_folder):
    source_path = os.path.join(source_folder, filename)

    with open(source_path, 'r') as file:
        content = file.read()
        match = re.search(pattern, content)
        if match:
            model = match.group(1)
            if model == 'T6J-L10':
                destination_file = os.path.join(destination_path_T6J, filename)
                shutil.move(source_path, destination_file) 
                print(f"Successfully copied {filename} from {source_folder} to {destination_path_T6J}")
            elif model == 'T6K-L10':
                destination_file = os.path.join(destination_path_T6K, filename)
                shutil.move(source_path, destination_file)  
                print(f"Successfully copied {filename} from {source_folder} to {destination_path_T6K}")
            elif model == 'T6H-L10':
                destination_file = os.path.join(destination_path_T6H, filename)
                shutil.move(source_path, destination_file)
                print(f"Successfully copied {filename} from {source_folder} to {destination_path_T6H}")
            else:
                os.remove(source_path)
                print(f"Removed {filename} in {source_folder}")
        else:
            os.remove(source_path)
            print(f"Removed {filename} in {source_folder}")

# Exit with a success code
exit(0)
