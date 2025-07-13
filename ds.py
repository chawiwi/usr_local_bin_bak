#!/usr/bin/env python3


import glob
from zeep import Client
import xml.etree.ElementTree as ET
import json
import sys
import subprocess
import paramiko
import warnings
import os
from datetime import datetime

username = "root"
password = "root"
api_url = 'http://192.168.66.20/AMA_L10/AMAService.svc?singleWsdl'

client = Client(api_url)


class TextColors:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"

def get_ETH0(SN):
    API_Type="CONFIG"
    API_Station = "QUERY"
    res = client.service.SendRequest(API_Station,SN,API_Type)
    response_text = str(res).replace("'", "\"").replace("None", "null")
    output_xml_file = 'array.xml'
    with open(output_xml_file, 'w') as xml_file:
        xml_file.write(response_text)
    response_dict = json.loads(response_text)
    for r in response_dict['Configs']['Config']:
        if (r['Parameter'] == 'ETH0'):
            ETH0 = (f"{r['Value'].split(',')[0]}")
            return ETH0
    return ''
    
def find_ip(ETH0):
    try:
        # ip_output = subprocess.check_output(["find_ip", '12.3.1.1'])
        ip_output = subprocess.check_output(["find_ip", ETH0]).decode().strip()
        return ip_output
    except subprocess.CalledProcessError as e:
        print(f"Error executing find_ip command: {e}")

def check_ping(host):
    try:
        subprocess.check_output(['ping', '-c', '1', '-W', '1', host], stderr=subprocess.STDOUT, text=True)
        print(f"{host} is reachable.")
        return True
    except subprocess.CalledProcessError as e:
        print(TextColors.RED + f"{host} is not reachable. Error: {e.output.strip()}" + TextColors.RESET)
        return False


def check_startup(target_host):
    warnings.filterwarnings("ignore", category=UserWarning)
    ssh_client = paramiko.SSHClient()
    # ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.set_missing_host_key_policy(paramiko.WarningPolicy())

    try:
        # Connect to the target system
        ssh_client.connect(target_host, username=username, password=password)

        # Run the command 'ps aux | grep startup'
        command = 'ps aux | grep startup'
        stdin, stdout, stderr = ssh_client.exec_command(command)

        output_lines = stdout.readlines()
        startupFound = False
        for line in output_lines:
            if 'startup_m3' in line:
                startupFound = True
        #         print (line)
        if startupFound:
            print (TextColors.GREEN + 'startup_m3 is running' + TextColors.RESET)
        else:
            print (TextColors.RED + 'startup_m3 process is not running' + TextColors.RESET)
    finally:
        # Close the SSH connectio
        ssh_client.close()
    


def check_startup_detailed(target_host):
    warnings.filterwarnings("ignore", category=UserWarning)
    ssh_client = paramiko.SSHClient()
    # ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.set_missing_host_key_policy(paramiko.WarningPolicy())

    try:
        # Connect to the target system
        ssh_client.connect(target_host, username=username, password=password)

        # Run the command 'ps aux | grep startup'
        command = 'ps aux | grep startup'
        stdin, stdout, stderr = ssh_client.exec_command(command)

        output_lines = stdout.readlines()
        startupFound = False
        for line in output_lines:
            if 'startup_m3' in line:
                startupFound = True
        dmi_command = 'dmidecode | grep Serial'
        stdin, stdout, stderr = ssh_client.exec_command(dmi_command)
        output_lines = stdout.readlines()
        mbsn =  (output_lines[1].strip())
        command = 'uptime'
        stdin, stdout, stderr = ssh_client.exec_command(command)

        uptime = stdout.readlines()[0].strip().split(',')[0]
        clean_sn =  (mbsn.split(':')[-1]).strip()
        if startupFound:
            # print (clean_sn)
            print (TextColors.GREEN + f"{target_host} | {mbsn} | startup_m3 is running | {uptime} | {find_latest_status(clean_sn)}" + TextColors.RESET)
        else:
            print (TextColors.RED + f"{target_host} | {mbsn} | startup_m3 is not running | {uptime} | {find_latest_status(clean_sn)}" + TextColors.RESET )
    except:
        print (f'{target_host} | Serial Number : Unknown | Cannot Check | Unreachable | Unknown ')
    finally:
        # Close the SSH connectio
        ssh_client.close()
        

def find_latest_status(pattern):
    directory = '/SFC/NetApp/Status/Bak'
    # Find files matching the pattern
    files = [f for f in os.listdir(directory) if f.startswith(pattern)]
    
    # If no files match the pattern, return None
    if not files:
        return None, None
    
    # Get the full paths of the matching files
    full_paths = [os.path.join(directory, f) for f in files]

    # Sort the full paths by modification time (most recent first)
    latest_file = max(full_paths, key=os.path.getmtime)
    
    # Get the modification timestamp of the latest file
    timestamp = os.path.getmtime(latest_file)

    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')


def main():
    if len(sys.argv) != 2:
        print (TextColors.CYAN +'ds is a tool used to check the status of the diagnostic with either the csn or mbsn.'+ TextColors.RESET)
        sys.exit(1)
    SN = sys.argv[1]
    ETH0 = get_ETH0(SN)
    ip = find_ip(ETH0)
    
    if ('not' in ip):
        print (TextColors.RED + "Mac Address not found" + TextColors.RESET)
        sys.exit(1)
    if check_ping(ip):
        check_startup(ip)
    sys.exit(1)
        

if __name__ == "__main__":
    print(find_latest_status('B68504044027703A'))
    # main()