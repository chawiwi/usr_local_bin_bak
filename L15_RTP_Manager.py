from zeep import Client
import xml.etree.ElementTree as ET
import json
import time
from multiprocessing import Process
import subprocess
import threading
import queue
import requests
import glob
import os
import sys
import datetime
import re

api_url = 'http://192.168.66.20/AMA_L11/AMAService.svc?singleWsdl'
PXE = "Q2"
server_debug_loc = "/RACKLOG/l15/Debug/{0}"
rack_debug_loc = "/RACKLOG/l15/Debug/{0}"
curr_status_loc = "/WIN/L15/currstatus/"
rm_user = "root"
rm_pass = "$pl3nd1D"
execute_rm_cmd = "sshpass -p '{0}' ssh -o 'StrictHostKeyChecking no' {1}@{2} -c aes256-cbc '{3}'"
rack_off_cmd = "set manager port off -i 1,2,3,4,5"
rack_on_cmd = "set manager port on -i 1,2,3,4,5"
server_off_cmd = "set manager port off -i {0}"
server_on_cmd = "set manager port on -i {0}"
server_info_cmd = "show system info -i {0}"
g_cmd_ping = "ping -c 3 {0}"
server_loc_map = { "F05": "1", "F14": "2", "F21": "3", "F29": "4", "F38": "5"}
blacklist = []
PXE_map = { "192.168.202.24": "Q1", "192.168.202.20": "Q5", "192.168.202.21": "Q6", "192.168.202.46": "Q7", "192.168.202.52": "Q2", "192.168.202.53": "Q3", "192.168.218.3": "R1", "192.168.218.5": "R2", "192.168.218.6": "R3", "192.168.218.7": "R4" }

def getresult(arg1):
    p = subprocess.Popen(arg1, stdout=subprocess.PIPE, shell=True,encoding="utf-8")
    (text, err) = p.communicate()
    res = text
    return res

def getPXE():
    cmd = "ip a"
    global PXE
    res = getresult(cmd)
    for key in PXE_map:
        if key in res:
            PXE = PXE_map[key]
            print("We are in PXE: {0}".format(PXE))
            return 0
    return 1

def logFail(sn, fail, type="server"):
    server_dir = server_debug_loc.format(sn)
    rack_dir = rack_debug_loc.format(sn)
    if type == "server":
        if not os.path.exists(server_dir):
            # Create directory
            os.makedirs(server_dir)
        log_path = "{0}/fail.log".format(server_dir)
        with open(log_path, 'w') as file:
            file.write(fail)
    elif type == "rack" and fail == "NETTEST":
        if not os.path.exists(rack_dir):
            # Create directory
            os.makedirs(rack_dir)
        log_path = "{0}/fail.log".format(rack_dir)
        with open(log_path, 'a') as file:
            file.write(fail + "\n")
    elif type == "rack":
        if not os.path.exists(rack_dir):
            # Create directory
            os.makedirs(rack_dir)
        log_path = "{0}/fail.log".format(rack_dir)
        with open(log_path, 'w') as file:
            file.write(fail)
    else:
        print("{0} is not a valid fail type!".format(type))
        return None
    return 0

def checkFail(sn, fail="NETTEST", type="server"):
    server_dir = server_debug_loc.format(sn)
    rack_dir = rack_debug_loc.format(sn)
    if type == "server":
        if not os.path.exists(server_dir):
            print("Server {0} has no previous fail".format(sn))
            return 0
        log_path = "{0}/fail.log".format(server_dir)
        res = getresult("cat {0}".format(log_path))
        if fail in res:
            print("Server {0} failed again:{1}".format(sn,fail))
            return 1
        else:
            print("Server {0} failed with error:{1} for the first time".format(sn,fail))
            return 0
    if type == "rack" and fail == "NETTEST":
        log_path = "{0}/fail.log".format(rack_dir)
        print("Checking fail file at {0}".format(log_path))
        if not os.path.exists(log_path):
            print("Rack {0} has no previous fail for NETTEST".format(sn))
            return 0
        with open(log_path, 'r') as file:
            lines = file.readlines()
        if len(lines) < 3:
            print("Rack {0} has failed for {1} times for NETTEST".format(sn, len(lines)))
            return 0
        elif fail not in lines[0]:
            print("Rack {0} has no previous fail for NETTEST".format(sn))
            return 0
        else:
            print("Rack {0} has failed NETTEST more than 2 times!".format(sn))
            return 1
    elif type == "rack":
        if not os.path.exists(rack_dir):
            print("Rack {0} has no previous fail".format(sn))
            return 0
        log_path = "{0}/fail.log".format(rack_dir)
        res = getresult("cat {0}".format(log_path))
        if res == fail:
            print("Rack {0} failed again:{1}".format(sn,fail))
            return 1
        else:
            print("Rack {0} failed with error:{1} for the first time".format(sn,fail))
            return 0 
    print("{0} is not a valid fail type!".format(type))
    return None
    

def getWIP():
    client = Client(api_url)
    API_Type = "RackCheckInList"
    API_Station = 'QUERY'

    response = client.service.SendRequest(API_Station,'MSF',API_Type)
    response_text = str(response).replace("'", "\"").replace("None", "null")
    response_dict = json.loads(response_text)
    WIP = []
    for rack in response_dict['RackCheckIns']['RackCheckIn']:
        if PXE in rack['CUR_LOC'] and rack['CUR_RACK'] not in WIP:
            WIP.append(rack['CUR_RACK'])
    return WIP 

def getStation(sn):
    client = Client(api_url)
    API_Type = "SYSTEM"
    API_Station = 'QUERY'
    response = client.service.ReturnStatus(sn,API_Type)
    if response['Msg'] != "OK":
        return 1
    return response['Asset'][0]['Station']

def getServers(racksn):
    client = Client(api_url)
    API_Type = "RLT"
    API_Station = 'QUERY'
    response = client.service.SendRequest(API_Station,racksn,API_Type)
    data = json.loads(str(response).replace("'", "\"").replace("None", "null"))
    SN_list = []
    if data['Msg'] != "OK":
        return 1
    for i in data['Assets']['Asset']: 
        type = i['Type']
        if (type != 'SERVERS'):
            continue
        unit_sn =  i['Serial']
        if unit_sn[0] == 'P':
            if unit_sn in SN_list:
                continue
            SN_list.append(unit_sn)
    return (SN_list)

def getConfig(sn):
    client = Client(api_url)
    API_Type = "CONFIG"
    API_Station = 'QUERY'
    response = client.service.SendRequest(API_Station,sn,API_Type)
    data = json.loads(str(response).replace("'", "\"").replace("None", "null"))
    if data['Msg'] != "OK":
        print("Config not found for server {0}".format(sn))
        return 1
    return data['Configs']['Config']

def calculate_time_difference(file_path):
    # Get the last modification time of the file
    mod_time = os.path.getmtime(file_path)

    # Get the current time
    current_time = time.time()
    
    # Calculate the time difference in seconds
    time_diff_seconds = current_time - mod_time
    
    # Convert the time difference to a human-readable format
    #time_diff = str(datetime.timedelta(seconds=time_diff_seconds))
    
    return time_diff_seconds/60

def getStatus(sn):
    search_path = os.path.join(curr_status_loc, "*{0}*".format(sn))
    
    # Use glob to get all files matching the pattern
    files = glob.glob(search_path)
    
    # If no files are found, return None
    if not files:
        print("No status files found for {0}!".format(sn))
        return None,None
    
    # Find the file with the latest modification time
    latest_file = max(files, key=os.path.getmtime)
    print(latest_file)
    status = ""
    idle = None
    with open(os.path.join(curr_status_loc,latest_file), 'r') as file:
        for line in file:
            if line.startswith("ERRORS="):
                # Strip any leading/trailing whitespace and get the part after "ERRORS="
                status = line.strip().split("=", 1)[1].strip()
    idle = calculate_time_difference(os.path.join(curr_status_loc,latest_file))
    print("{0} status is: {1}, idle time is {2}".format(sn,status,idle))
    return status, idle

def extract_wait_time(log_string):
    # Regular expression to match the pattern and extract the number
    match = re.search(r"already wait (\d+) mins", log_string)
    
    # Check if a match was found
    if match:
        # Extract the number (group 1 from the regex match)
        wait_time = match.group(1)
        return int(wait_time)
    else:
        return None

def isNettest(racksn):
    servers = getServers(racksn)
    print(servers)
    if servers == 1:
        print("Servers not found for rack {0}".format(racksn))
        return False
    count = 0
    rack_map = {}
    for sn in servers:
        status,idle = getStatus(sn)
        if status == None:
            return False
        station = getStation(sn)
        rack_map[sn] = {"Status": status, "Idle": idle, "Station": station}
        print(station)
        if station == 1:
            print("Station not found for {0}".format(sn))
            return False
        if station != "NETTEST" and station != "MDAASWINDOWS":
            print("{0}:{1} not ready for NETTEST!".format(racksn,sn))
            return False
        elif station == "MDAASWINDOWS" and "MDAASWINDOWS FINISH" not in status:
            print("{0}:{1} not ready for NETTEST!".format(racksn,sn))
            return False
    for sn in servers:
        if "FST" in rack_map[sn]['Status']:
            return False
        if rack_map[sn]['Station'] == "NETTEST" and rack_map[sn]['Idle'] > 60:
            return True
        elif rack_map[sn]['Station'] == "NETTEST":
            idle = extract_wait_time(rack_map[sn]['Status'])
            if idle == None:
                print("{0}:{1} has started NETTEST!".format(racksn,sn))
                count = count + 1
                continue
            if idle > 60:
                return True
            print("{0}:{1} has started NETTEST!".format(racksn,sn))
            count = count + 1
    if count > 0:
        return False
    else:
        return True

def getRM(sn):
    config = getConfig(sn)
    for entry in config:
        if entry['Parameter'] == "RACK_MOUNT_MAC1":
            return entry['Value']
    print("RM not found for {0}".format(sn))
    return None

def getIP(mac):
    ip = "" 
    log = "get_rm_ip"
    mac_trans = (mac[:2]+':'+mac[2:4]+':'+mac[4:6]+':'+mac[6:8]+':'+mac[8:10]+':'+mac[10:12])
    mac_trans = mac_trans.lower()

    search_ip_cmd = "grep -B9 -A1 -i {0} /var/lib/dhcpd/dhcpd.leases | grep lease".format(mac_trans)
    ip = getresult(search_ip_cmd)
    log = "Get_IP MAC = {0} IP = {1:.<12}".format(mac_trans,ip)
    if len(ip) >= 1 : 
        if  "{" in ip:
            ip =  ip.strip().split("{")
    
        for line in ip:
            if line != "" :
                if " " in line:
                    line = line.split(" ")[1]
                log = "Get_ip MAC = {0} IP = {1}".format(mac_trans,line)
                #sendlog(log,"PASS")
                #log = "Check RM Connection IP ={0}".format(line)
                if os.system(g_cmd_ping.format(line)) == 0:
                    print("Get_IP MAC = {0} IP = {1:.<12}".format(mac_trans,line))
                    return line
            else:
                break
    return 1

def getServerLoc(sn):
    config = getConfig(sn)
    for entry in config:
        if entry['Parameter'] == "LOCATION":
            return entry['Value']
    print("Location not found for {0}".format(sn))
    return None

def checkSystemInfo(sn,ip,loc=""):
    if loc == "":
        location = server_loc_map[getServerLoc(sn)]
    else:
        location = loc
    rm_cmd = server_info_cmd.format(location)
    cmd = execute_rm_cmd.format(rm_pass,rm_user,ip,rm_cmd)
    print(cmd)
    res = getresult(cmd)
    print(res)
    if sn not in res:
        return False
    return True
            
def checkReality(racksn,ip):
    servers = getServers(racksn)
    for sn in servers:
        if checkSystemInfo(sn,ip) == False:
            print("{0} is not on rack:{1}".format(sn,racksn))
            return False
    print("All servers present on rack:{0}".format(racksn))
    return True

def ACRack(racksn,ip):
    cmd = execute_rm_cmd.format(rm_pass,rm_user,ip,rack_off_cmd)
    print(cmd)
    res = getresult(cmd)
    print(res)
    if "Success" not in res:
        print("Failed to turn off rack:{0}".format(racksn))
        return 1
    time.sleep(60)
    cmd = execute_rm_cmd.format(rm_pass,rm_user,ip,rack_on_cmd)
    print(cmd)
    res = getresult(cmd)
    print(res)
    if "Success" not in res:
        print("Failed to turn on rack:{0}".format(racksn))
        return 1
    print("Successfully AC'd rack:{0}".format(racksn))

def ACServer(sn,ip,loc):
    if checkSystemInfo(sn,ip,loc) == False:
        print("{0} is not on rack".format(sn))
        return False
    off_cmd = server_off_cmd.format(loc)
    cmd = execute_rm_cmd.format(rm_pass,rm_user,ip,off_cmd)
    print(cmd)
    res = getresult(cmd)
    print(res)
    if "Success" not in res:
        print("Failed to turn off server:{0}".format(sn))
        return 1
    time.sleep(120)
    on_cmd = server_on_cmd.format(loc)
    cmd = execute_rm_cmd.format(rm_pass,rm_user,ip,on_cmd)
    print(cmd)
    res = getresult(cmd)
    print(res)
    if "Success" not in res:
        print("Failed to turn on server:{0}".format(sn))
        return 1
    print("Successfully AC'd server:{0}".format(sn))
    
def createMDAASflag(sn):
    mdaas_flag = "/WIN/L15/MDAAS/{0}.txt".format(sn)
    if os.path.exists(mdaas_flag):
        return 0
    config = getConfig(sn)
    for entry in config:
        if "ETH0" in entry['Parameter']:
            eth0 = entry['Value']
            mac_raw = eth0.split('=')[1].split(',')[0]
            formatted_mac = ':'.join(mac_raw[i:i+2] for i in range(0, len(mac_raw), 2)).lower()
            formatted_eth0 = formatted_mac.lower()
            with open(mdaas_flag, 'w') as output_file:
                output_file.write(formatted_eth0 + '\n')
            return 0
    return 1

def manageNettest(racksn):
    global blacklist
    if isNettest(racksn):
        print("{0} is ready for NETTEST!".format(racksn))
        blacklist.append(racksn)
        servers = getServers(racksn)
        rm_mac = getRM(servers[0])
        print("{0} RM MAC:{1}".format(racksn,rm_mac))
        rm_ip = getIP(rm_mac)
        print("{0} RM MAC:{1}, RM IP:{2}".format(racksn,rm_mac,rm_ip))
        if checkReality(racksn,rm_ip):
            blacklist.append(racksn)
            retest = checkFail(racksn, "NETTEST", "rack")
            if retest == 0:
                logFail(racksn, "NETTEST", "rack")
                ACRack(racksn,rm_ip)
    else:
        return 0

def manageFail(sn,ip):
    status,idle = getStatus(sn)
    if status == None:
        return False
    station = getStation(sn)
    serverState = {"Status": status, "Idle": idle, "Station": station}
    print(serverState)
    if station == 1:
        print("Station not found for {0}".format(sn))
        return False
    loc = server_loc_map[getServerLoc(sn)]
    #CP config
    if "CP reconfig FINISH" in status and idle > 60:
        if checkFail(sn,"CP reconfig FINISH") == 0:
            ACServer(sn,ip,loc)
            logFail(sn,"CP reconfig FINISH")
    elif "CP update FINISH" in status and idle > 50:
        if checkFail(sn,"CP update FINISH") == 0:
            cmd = "rm -f /RACKLOG/l15/RM_logs/{0}/*".format(sn)
            res = getresult(cmd)
            print(cmd)
            print(res)
            logFail(sn,"CP update FINISH")
    elif "Start to do CP reconfig" in status and idle > 50:
        if checkFail(sn,"Start to do CP reconfig") == 0:
            cmd = "rm -f /RACKLOG/l15/RM_logs/{0}/*".format(sn)
            res = getresult(cmd)
            print(cmd)
            print(res)
            logFail(sn,"Start to do CP reconfig")
    elif "CP provision finish!" in status and idle > 50:
        if checkFail(sn,"CP provision finish!") == 0:
            cmd = "rm -f /RACKLOG/l15/RM_logs/{0}/*".format(sn)
            res = getresult(cmd)
            print(cmd)
            print(res)
            logFail(sn,"CP provision finish!")
    elif "record CP golden image version FAIL" in status:
        if checkFail(sn,"record CP golden image version FAIL") == 0:
            cmd = "rm -f /RACKLOG/l15/RM_logs/{0}/*".format(sn)
            res = getresult(cmd)
            print(cmd)
            print(res)
            logFail(sn,"record CP golden image version FAIL")
    elif "remove_auto_reconfig_file FAIL" in status:
        if checkFail(sn,"remove auto reconfig file") == 0:
            set_bootmode_cmd = "set system boot -i {0} -b 1 -t 6".format(loc)
            cmd = execute_rm_cmd.format(rm_pass,rm_user,ip,set_bootmode_cmd)
            res = getresult(cmd)
            print(cmd)
            print(res)
            logFail(sn,"remove auto reconfig file")
    elif "SWITCH-UPDATE-AND-CONFIG-FINISH" in status and idle > 60:
        if checkFail(sn, "SWITCH-UPDATE-AND-CONFIG-FINISH") == 0:
            cmd = "rm -f /RACKLOG/l15/RM_logs/{0}/*".format(sn)
            res = getresult(cmd)
            print(cmd)
            print(res)
            logFail(sn,"SWITCH-UPDATE-AND-CONFIG-FINISH") 
    #PRETEST
    elif "Get server_ID=[NA]" in status:
        if checkFail(sn,"Get server_ID=[NA]") == 0:
            ACServer(sn,ip,loc)
            logFail(sn,"Get server_ID=[NA]")
    elif "Redfish return failed" in status:
        if checkFail(sn, "Redfish return failed") == 0:
            ACServer(sn,ip,loc)
            logFail(sn,"Redfish return failed")
    elif "L15 RTP Windows test start" in status and idle > 60:
        if checkFail(sn, "L15 RTP Windows test start") == 0:
            ACServer(sn,ip,loc)
            logFail(sn,"L15 RTP Windows test start")
    elif "fpga, Celestialpeak check===L15 PRETEST test FAIL" in status:
        if checkFail(sn, "L15 PRETEST fpga test FAIL") == 0:
            ACServer(sn,ip,loc)
            logFail(sn,"L15 PRETEST fpga test FAIL")
    elif "PRETEST FINISH" in status and idle > 120:
        if checkFail(sn,"PRETEST FINISH") == 0:
            ACServer(sn,ip,loc)
            logFail(sn,"PRETEST FINISH")
    # elif "Failed in read FPGA" in status:
    #     ACServer(sn,ip,loc)
    # #MDAAS
    elif "MDAAS test 500 Server Error" in status:
        if checkFail(sn,"MDAAS test 500 Server Error") == 0:
            ACServer(sn,ip,loc)
            logFail(sn,"MDAAS test 500 Server Error")
    elif "MDAAS test , 0/0" in status:
        if checkFail(sn, "MDAAS 0/0") == 0:
            ACServer(sn,ip,loc)
            logFail(sn, "MDAAS 0/0")
    elif "MDAAS test" in status and "ConnectionResetError" in status:
        if checkFail(sn,"MDAAS test ConnectionResetError 104") == 0:
            ACServer(sn,ip,loc)
            logFail(sn,"MDAAS test ConnectionResetError 104")

    # #FST
    elif "bootmode get 0 fail" in status:
        ACServer(sn,ip,loc)
    elif "[CCRMaster] [CCR]Unexpected error:" in status:
        ACServer(sn,ip,loc)
    elif "Reboot System" in status and idle > 55:
        if checkFail(sn,"Reboot System") == 0:
            ACServer(sn,ip,loc)
            logFail(sn,"Reboot System")
    elif "FST CP Log Check FAIL" in status:
        if checkFail(sn,"FST CP Log Check FAIL") == 0:
            ACServer(sn,ip,loc)
            logFail(sn,"FST CP Log Check FAIL")
    elif "SDR Check FAIL" in status:
        if checkFail(sn,"SDR Check FAIL") == 0:
            ACServer(sn,ip,loc)
            logFail(sn,"SDR Check FAIL")
    elif "HPET Check" in status and idle > 50:
        if checkFail(sn, "HPET Check") == 0:
            ACServer(sn,ip,loc)
            logFail(sn,"HPET Check")
    # #generate MDAAS flag
    if station == "MDAASGENCONFIG" or station == "MDAASSHC" or station == "MDAASLINUX" or station == "MDAASWINDOWS":
       if "MDAASWINDOWS FINISH" not in status and idle > 60:
            createMDAASflag(sn)
    return 0


def manageRack(racksn):
    servers = getServers(racksn)
    if servers == 1:
        print("Servers not found for rack {0}".format(racksn))
        return 1
    rm_mac = getRM(servers[0])
    rm_ip = getIP(rm_mac)
    print("{0} RM MAC:{1}, RM IP:{2}".format(racksn,rm_mac,rm_ip))
    if rm_ip == 1:
        print("Failed to get RM IP for rack:{0}".format(racksn))
        return 1
    for server in servers:
        manageFail(server,rm_ip)

if __name__ == '__main__':
    if getPXE() == 1:
        print("PXE ip not recognized")
        sys.exit(0)
    print(PXE)

    wip = getWIP()
    processes = []
    print(wip)
    if len(wip) == 0:
        print("No WIP in line {0}".format(PXE))
        sys.exit(0)
    for rack in wip:
        manageNettest(rack)
    print("Blacklist is {0}".format(blacklist))
    for rack in wip:
        if rack not in blacklist:
            p = Process(target=manageRack, args=(rack,))
            p.start()
            processes.append(p)
            time.sleep(5)

    
