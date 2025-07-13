import sys
import re
import subprocess
from ds import check_startup_detailed
from datetime import datetime

class TextColors:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"



def find_all_ip():
    leases_file_path = '/var/lib/dhcp/dhcpd.leases'
    current_time = datetime.now()

    with open(leases_file_path, 'r') as leases_file:
        leases_content = leases_file.read()

    # Split leases by "lease" keyword
    leases = leases_content.split('lease ')[1:]

    # Normalize provided MAC address
    # normalized_mac_address = normalize_mac_address(mac_address)
    all_active = []
    for lease in leases:
        
        # Split lease block into lines
        lease_lines = lease.strip().split('\n')

        # Extract MAC address if present
        mac_lines = [line for line in lease_lines if 'hardware ethernet' in line]
        if not mac_lines:
            continue

        lease_mac = mac_lines[0].split(' ')[-1].strip(';').lower()
        starts_line = next(line for line in lease_lines if 'starts' in line)
        date_match = re.search(r'\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}', starts_line)
        if date_match:
            start_time_str = date_match.group(0)
            start_time = datetime.strptime(start_time_str, '%Y/%m/%d %H:%M:%S')
        else:
            continue

        end_line = next(line for line in lease_lines if 'ends' in line)
        date_match = re.search(r'\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}', end_line)
        if date_match:
            end_time_str = date_match.group(0)
            end_time = datetime.strptime(end_time_str, '%Y/%m/%d %H:%M:%S')
        else:
            continue

        # Check if the lease is still active
        if current_time <= end_time:
            # Extract and return IP address
            # return lease_lines[0].split(' ')[0]
            if 'quanta' in lease:
                all_active.append(lease_lines[0].split(' ')[0])
            
    return all_active


def check_ping(host):
    try:
        subprocess.check_output(['ping', '-c', '1', '-W', '1', host], stderr=subprocess.STDOUT, text=True)
        return True
    except subprocess.CalledProcessError as e:
        return False
    
if __name__ == "__main__":
    all_active = find_all_ip()
    if len(all_active) > 0:
        host_to_check = []
        for ip in all_active:
            if check_ping(ip):
                # print (TextColors.CYAN + f'Checking Startup Status for {ip}' + TextColors.RESET)
                check_startup_detailed(ip)
    
    