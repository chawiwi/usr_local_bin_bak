#!/usr/bin/env python3
#Version : 1.1
#Author : Lawrence Dizon
#.

import subprocess
import re
import sys

SLOTS_OF_BLADES = {
    '1' : '000000',
    '2' : '000001',
    '3' : '000010',
    '4' : '000011',
    '5' : '000100',
    '6' : '000101',
    '7' : '001000',
    '8' : '001001',
    '9' : '001010',
    '10' : '001011',
    '11' : '001100',
    '12' : '001101',
    '13' : '010000',
    '14' : '010001',
    '15' : '010010',
    '16' : '010011',
    '17' : '010100',
    '18' : '010101',
    '19' : '011000',
    '20' : '011001',
    '21' : '011010',
    '22' : '011011',
    '23' : '011100',
    '24' : '011101',
    '25' : '100000',
    '26' : '100001',
    '27' : '100010',
    '28' : '100011',
    '29' : '100100',
    '30' : '100101',
    '31' : '101000',
    '32' : '101001',
    '33' : '101010',
    '34' : '101011',
    '35' : '101100',
    '36' : '101101',
    '37' : '110000',
    '38' : '110001',
    '39' : '110010',
    '40' : '110011',
    '41' : '110100',
    '42' : '110101',
    '43' : '111000',
    '44' : '111001',
    '45' : '111010',
    '46' : '111011',
    '47' : '111100',
    '48' : '111101'
    }


def get_manager_inventory(rmIP):
    cmd = f"sshpass -p '$pl3nd1D' ssh -o 'StrictHostKeyChecking no' root@{rmIP} 'show manager inventory'"
    output = subprocess.check_output(cmd, shell=True)
    output = (output.decode())
    print (output)
    return output
 

def parse_output_to_data_list(output):
    lines = output.strip().split('\n')

    headers = lines[1].split('|')[1:-1]
    headers = [header.strip() for header in headers]

    data_list = []

    for line in lines[2:-2]:
        values = line.split('|')[1:-1]
        values = [value.strip() for value in values]

        row_data = dict(zip(headers, values))
        data_list.append(row_data)

    completion_code = lines[-2].split(':')[1].strip()

    for item in data_list:
        item["Completion Code"] = completion_code

    return data_list


def get_slot_id_value(rmIP,swPort, slotId):
    raw_id = ''

    for rawValue in range(189,183,-1):
        cmd = f"sshpass -p '$pl3nd1D' ssh -o 'StrictHostKeyChecking no' root@{rmIP} 'set system cmd -c raw 0x30 0xe1 {str(rawValue)} -i {swPort}'"
        output = (subprocess.check_output(cmd, shell=True)).decode()
        ipmi_response = grap_ipmi_response(output)
        if (ipmi_response):
            raw_id += ipmi_response[-1]
        else:
            print (f'Switch Port {swPort} is reading {slotId} for Slot ID')
            print (f'Was unable to successfully get the raw value of the Slot ID')

    
    print (f'Switch Port {swPort} is reading {slotId} for Slot ID')

    if (SLOTS_OF_BLADES[slotId] == raw_id ):
        print (f'Raw value of the Slot Id - {slotId}, {raw_id}, in Switch Port {swPort} MATCHES expected value, {SLOTS_OF_BLADES[slotId]} | The PMDU is opperating as expected \n' )
    else:
        print (f'Raw value of the Slot Id - {slotId}, {raw_id}, in Switch Port {swPort} DOES NOT MATCH expected value, {SLOTS_OF_BLADES[slotId]} | The PMDU is NOT opperating as expected \n')

    

def grap_ipmi_response(output):
    pattern = r"Ipmi Response: 00 (\S+)"
    match = re.search(pattern, output)

    if match:
        ipmi_response = match.group(1)
        return ipmi_response
    else:
        return
    

def is_pingable(ip_address):
    try:
        result = subprocess.run(["ping", "-c", "1", ip_address], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            return True
        else:
            return False
    except Exception as e:
        print("Error:", e)
        return False

if __name__ == '__main__':
    if len(sys.argv) > 1:
        rmIP = sys.argv[1]
    else:
        rmIP = input("Enter IP for RM: ")

    if (not is_pingable(rmIP)):
        print (f"Unable to ping {rmIP}. Please verify the IP Address and the connection")
        sys.exit()

    output = get_manager_inventory(rmIP)
    manager_info =  parse_output_to_data_list(output)
    
    slots_to_test = []

    for UUT in manager_info:
        if (UUT['Present'] == "True" and UUT['SW Port'] != UUT['Slot Id']):
            tempData = {'SW Port': UUT['SW Port'], 'Slot Id': UUT['Slot Id']}
            slots_to_test.append(tempData)
    print (slots_to_test)

    for slot in slots_to_test:
        get_slot_id_value(rmIP,slot['SW Port'], slot['Slot Id'])


 