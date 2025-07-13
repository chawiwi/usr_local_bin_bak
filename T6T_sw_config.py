from multiprocessing import Process
from zeep import Client
import glob
import json
import xml.etree.ElementTree as ET
import sys
import os
import time 
import subprocess
from datetime import datetime
import concurrent.futures
api_url = 'http://192.168.66.20/AMA_L11/AMAService.svc?singleWsdl'
PXE_map = {"192.168.218.14": "R101","192.168.218.15": "R102", "192.168.218.16": "R111", "192.168.218.17":"R112"}

ESC_GREEN		= "\033[32m"
ESC_RED			= "\033[31m"
ESC_YELLOW_F	= "\033[33;1m"
ESC_YELLOW		= "\033[33m"
ESC_PINK		= "\033[35m"
ESC_LBLUE		= "\033[36m"
ESC_OFF			= "\033[0m"

GREEN			= 1
RED				= 2 
YELLOW			= 3
PINK			= 4
ORANGE			= 5
BLUE			= 6

PASS			= "PASS"
FAIL			= "FAIL"
VERSION			= "3.1.0"
EDITOR			= "Edward"
RELEASE_DATE	= "2025/05/01"

g_model = "T6T"

g_log_folder = "/RACKLOG/{0}/RM_logs"
g_mainlog_file = "/RACKLOG/monitor.log"
g_win_config_folder = "/WIN/{0}/response/config"

g_switch_config_files = ["sonic-aboot-broadcom-20201231.76.swi", "SW_Config.sh"]

g_T6T_script_folder = "/project/firmware/t6t/switch"

g_switch_update_folder = "/host/FW_Update/"

g_cmd_search_ip_QMF = "grep -B8 -A1 {0} /var/lib/dhcpd/dhcpd.leases | grep lease"
g_cmd_ping = "ping -c 3 {0}"

g_switch_passwords = ["password","Temp123!"]

g_sshpass_cmd = "sshpass -p '{0}' ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null admin@{1} '{2}'"
g_sshpass_scp = "sshpass -p '{0}' scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null {1} admin@{2}:{3}"

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



def sendlog(message = "", color = 0, logfile = ""):
	if color == 1 :
		ESC_color = ESC_GREEN
	elif color == 2 :
		ESC_color = ESC_RED
	elif color == 3 :
		ESC_color = ESC_YELLOW
	elif color == 4 :
		ESC_color = ESC_PINK
	elif color == 5 :
		ESC_color = ESC_YELLOW_F
	elif color == 6 :
		ESC_color = ESC_LBLUE
	else:
		ESC_color = ESC_OFF
		
	if color == PASS or color == FAIL:
		if color == PASS:
			ESC_color = ESC_GREEN
		else :
			ESC_color = ESC_RED
		print (str(message)+"........................."+ESC_color+"["+color+"]"+ESC_OFF)
		message = str(message) +"........................."+"["+color+"]"
	else:
		print (ESC_color+str(message)+ESC_OFF)

	if logfile != "":
		cmd = ("echo '{0} ====>> {1}' >>{2}".format(time.strftime("%m-%d-%y-%H:%M:%S"), message, logfile))
		os.system(cmd)
		
	cmd = ("echo '{0} ====>> {1}' >>{2}".format(time.strftime("%m-%d-%y-%H:%M:%S"), message, g_mainlog_file))
	os.system(cmd)

def send_data_sf(start_time,message,log_type, sf_sn, location, station, log_file, project):

	st_file = "/home/Monitor_reconfig_CP/{0}.ST".format(sf_sn)
     
	head_location = '/WIN/'+project+'/'
	win_st_file = "{0}status/{1}.ST".format(head_location, sf_sn)

	with open(st_file, mode="wt") as f:
			f.write("SERIAL={0}\n".format(sf_sn))
			f.write("ERRORS={0}\n".format(message))
			f.write("STATUS={0}\n".format(log_type))
			f.write("LOCATI={0}\n".format(location))
			f.write("STATIO={0}\n".format(station))
			f.write("LOGFIL={0}\n".format(log_file))
			f.write("STARTT={0}\n".format(start_time))
			f.close()

	os.system("cp -rf {0} {1}".format(st_file, win_st_file))
	retryc = 10
	count = 0
	if not os.path.exists(win_st_file) or count > retryc:
			#shutil.copyfile(st_file, win_st_file)
		os.system("cp -rf {0} {1}".format(st_file, win_st_file))
		count += 1
	os.system("cp -rf {0} {1}request/mac/{2}.ST".format(st_file, head_location, sf_sn))

def is_done(sn):
    flag_path = g_log_folder.format("t6t") + "/{0}/{0}.txt".format(sn)
    flag_dir = g_log_folder.format("t6t") + "/{0}/".format(sn)
    if os.path.exists(flag_path):
        print("{0} already configured".format(sn))
        return True
    elif os.path.exists(flag_dir):
        return False
  

def get_serial_numbers():
    serial_numbers = []
    WIP = getWIP()
    if len(WIP) < 1:
        return serial_numbers
    
    for rack in WIP:
        if not is_done(rack):
            print("{0} is not configured!".format(rack))
            servers = getServers(rack)
            serial_numbers.append(servers[0])
    return serial_numbers

def is_config(racksn, switchsn, project):
    flag_path = g_log_folder.format(project) + "/{0}/{1}.txt".format(racksn, switchsn)
    updating_flag = g_log_folder.format(project) + "/{0}/{1}_updating.txt".format(racksn, switchsn)
    if os.path.exists(flag_path):
        print("Switch {0} already configured".format(switchsn))
        return True
    elif os.path.exists(updating_flag):
        print("{0} already configuring...".format(switchsn))
        return True
    else:
        return False

def is_ycable_update(racksn, project):
    if project.upper() == "T6T":
        return True
    flag_path = g_log_folder.format(project) + "/{0}/y_cable_finish.txt".format(racksn)
    updating_flag = g_log_folder.format(project) + "/{0}/y_cable_updating.txt".format(racksn)
    if os.path.exists(flag_path):
        print("Ycable already updated")
        return True
    elif os.path.exists(updating_flag):
        print("Ycable already updating...")
        return True
    else:
        return False

def delete_config(racksn, project):
    cmd = "grep -rl '{0}' /WIN/{1}/response/config | xargs rm -f".format(racksn,project)
    print(getresult(cmd))
    print("Deleting config files for {0}".format(racksn))

def read_sn_info_from_config(sn):	
    SNdict = {
        "sn": "NA",
        "RACKSN": "NA",
        "switch_a_sn": "NA",
        "switch_b_sn": "NA",
        "switch_c_sn": "NA",
        "switch_d_sn": "NA",
        "switch_a_mac": "NA",
        "switch_b_mac": "NA",
        "switch_c_mac": "NA",
        "switch_d_mac": "NA",
        "STATION": "NA",
        "LOCATION": "NA",
        "MODEL": "NA"
    }
    config = getConfig(sn)
    if config == 1:
        return 1
    
    SNdict["sn"] = sn
    SNdict["STATION"] = "PRETEST"
    switch = 0
    for line in config:
        if "RACKSN" in line['Parameter']:
            SNdict["RACKSN"] = line['Value'].strip()
        
        if "SWITCHSML" in line['Parameter']:
            if "Arista" in line['Value']:
                if switch == 0:
                    SNdict["switch_a_sn"] = line['Value'].split(',')[0].strip()
                    SNdict["switch_a_mac"] = line['Value'].split(',')[1].strip()
                    switch += 1
                elif switch == 1:
                    SNdict["switch_b_sn"] = line['Value'].split(',')[0].strip()
                    SNdict["switch_b_mac"] = line['Value'].split(',')[1].strip()
                    switch += 1
                elif switch == 2:
                    SNdict["switch_c_sn"] = line['Value'].split(',')[0].strip()
                    SNdict["switch_c_mac"] = line['Value'].split(',')[1].strip()
                    switch += 1
                elif switch == 3:
                    SNdict["switch_d_sn"] = line['Value'].split(',')[0].strip()
                    SNdict["switch_d_mac"] = line['Value'].split(',')[1].strip()
                    switch += 1
        if "LOCATION" in line['Parameter']:
            SNdict["LOCATION"] = line['Value'].strip()
        if "MODEL" in line['Parameter']:
            if line['Value'] != g_model:
                return 1
            SNdict['MODEL'] = line['Value'].strip()

    flag_dir = g_log_folder.format(SNdict['MODEL'].lower()) + "/" + SNdict['RACKSN']
    if not os.path.exists(flag_dir):
        os.mkdir(flag_dir)
    return SNdict

def check_ping(ip_address):
    # Construct the ping command
    command = ['ping', '-c', '3', ip_address]

    # Execute the ping command
    try:
        output = subprocess.check_output(command, timeout=8, stderr=subprocess.STDOUT, universal_newlines=True)
        print(output)
        return True
    except subprocess.CalledProcessError:
        return False
    except subprocess.TimeoutExpired:
        return False
    
def getresult(arg1, t=None):
    print("execute cmd: " + arg1)
    p = subprocess.Popen(arg1, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True,encoding="utf-8")
    if t == None:
        (text, err) = p.communicate()
        res = text + err
        return res
    else:
        try:
            subprocess.run(arg1, shell=True, timeout=t)
        except subprocess.TimeoutExpired:
            print("Connection closed after sending the reboot command.")
    return None

def get_ip(mac_addr):
	ip = "" 
	mac_trans = (mac_addr[:2]+':'+mac_addr[2:4]+':'+mac_addr[4:6]+':'+mac_addr[6:8]+':'+mac_addr[8:10]+':'+mac_addr[10:12])
	mac_trans = mac_trans.lower()
	search_ip_cmd = g_cmd_search_ip_QMF.format(mac_trans)
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
	
				if os.system(g_cmd_ping.format(line)) == 0:
					return line
			else:
				break
	return 1    

def switch_password():
    global g_switch_passwords 
    g_switch_passwords = g_switch_passwords[::-1]

def checkSwitch(ip):
    cmd = g_sshpass_cmd.format(g_switch_passwords[0], ip,"exit")
    ret = getresult(cmd)
    time.sleep(2)
    if "Permission denied" in ret:
        switch_password()
        time.sleep(2)
    return 0

def send_file_to_switch(ip,log, project):
    output = ""
    cmd = "sudo mkdir /host/FW_Update"
    ret = getresult(g_sshpass_cmd.format(g_switch_passwords[0],ip,cmd))
    output = output + ret
    print(ret)
    cmd = "sudo chmod 777 /host/FW_Update"
    ret = getresult(g_sshpass_cmd.format(g_switch_passwords[0],ip,cmd))
    output = output + ret
    print(ret)
    cmd = g_sshpass_scp.format(g_switch_passwords[0],"/project/firmware/t6t/switch/*", ip, "/host/FW_Update/")

    ret = getresult(cmd)
    output = output + ret
    print(ret)
    print("copying to switch")
    time.sleep(10)
    with open(log, 'a') as file:
        # Write output to the file
        file.write(output + "\n")
    return 0

def check_switch_os_version(ip,log):
    cmd = "show version"
    ret = getresult(g_sshpass_cmd.format(g_switch_passwords[0],ip,cmd))
    time.sleep(3)
    print(ret)
    with open(log, 'a') as file:
        # Write output to the file
        file.write(ret + "\n")
    if "SONiC Software Version: SONiC.20201231.76" not in ret:
        print("Os need update")
        cmd = "sudo mkdir /host/FW_Update"
        ret = getresult(g_sshpass_cmd.format(g_switch_passwords[0],ip,cmd))
        time.sleep(3)
        print(ret)
        with open(log, 'a') as file:
            # Write output to the file
            file.write(ret + "\n")
        return 1
    print("Os already updated")
    return 0

def update_switch_os(ip,log,model):
    os = "sonic-aboot-broadcom-20201231.76.swi"
    cmd = "sudo sonic-installer install /host/FW_Update/{0} -y".format(os)
    ret = getresult(g_sshpass_cmd.format(g_switch_passwords[0],ip,cmd))
    time.sleep(40)
    print(ret)
    with open(log, 'a') as file:
        # Write output to the file
        file.write(ret + "\n")
    cmd = "sshpass -p '{0}' ssh -o  StrictHostKeyChecking=no -o ConnectTimeout=10 -o UserKnownHostsFile=/dev/null admin@{1} 'sudo reboot'"
    getresult(cmd.format(g_switch_passwords[0],ip),5)
    time.sleep(50)
    with open(log, 'a') as file:
        # Write output to the file
        file.write(ret + "\n")
    return 0


def run_SW_Config(ip,log):
    cmd = "sudo bash /host/FW_Update/SW_Config.sh"
    ret = getresult(g_sshpass_cmd.format(g_switch_passwords[0],ip,cmd))
    time.sleep(10)
    print(ret)
    with open(log, 'a') as file:
        # Write output to the file
        file.write(ret + "\n")
    return 0

def disable_tor(ip,switch,log):
    ret = ""
    if switch == "A":
        cmds = ["sudo config interface shutdown Ethernet0","sudo config interface shutdown Ethernet4","sudo config interface shutdown Ethernet8",
                "sudo config interface shutdown Ethernet12","sudo config interface shutdown Ethernet16","sudo config interface shutdown Ethernet20",
                "sudo config interface shutdown Ethernet40","sudo config interface shutdown Ethernet44","sudo config interface shutdown Ethernet48"]
        for cmd in cmds:
            ret += getresult(g_sshpass_cmd.format(g_switch_passwords[0],ip,cmd))
        ret += getresult(g_sshpass_cmd.format(g_switch_passwords[0],ip,"sudo config save -y"))
        time.sleep(15)
        print(ret)
        with open(log, 'a') as file:
            # Write output to the file
            file.write(ret + "\n")
        return 0
    elif switch == "C":
        cmds = ["sudo config interface shutdown Ethernet76","sudo config interface shutdown Ethernet80","sudo config interface shutdown Ethernet84",
                "sudo config interface shutdown Ethernet104","sudo config interface shutdown Ethernet108","sudo config interface shutdown Ethernet112",
                "sudo config interface shutdown Ethernet116","sudo config interface shutdown Ethernet120","sudo config interface shutdown Ethernet124"]
        for cmd in cmds:
            ret += getresult(g_sshpass_cmd.format(g_switch_passwords[0],ip,cmd))
        ret += getresult(g_sshpass_cmd.format(g_switch_passwords[0],ip,"sudo config save -y"))
        time.sleep(15)
        print(ret)
        with open(log, 'a') as file:
            # Write output to the file
            file.write(ret + "\n")
        return 0
    else:
        print("Switch {0} is not meant to be disabled!".format(switch))
        return None

def config_nokia(sn_info, switch):
    ip = get_ip(sn_info["switch_a_mac"])
    if ip == 1:
        print("Could not get switch {0} IP".format(switch))
        log_type="WARNING"
        message = "TOR-SWITCH-{0}-IP-CHECK-FAIL".format(switch)
        start_time=time.strftime("%Y%m%d%H%M%S")
        log_file =""
        send_data_sf(start_time,message, log_type, sn_info["sn"], sn_info["LOCATION"], sn_info["STATION"], log_file, sn_info['MODEL'])
        return 1
    os.system("touch /RACKLOG/t6t/RM_logs/{0}/nokia_updating.txt".format(sn_info["RACKSN"]))

    checkSwitch(ip)
    log = "/RACKLOG/t6t/RM_logs/{0}/nokia.log".format(sn_info["RACKSN"])

    send_file_to_switch(ip,log,"T6T")

    ret = getresult(g_sshpass_cmd.format("Temp123!",ip,"sudo python3 /host/FW_Update/nokia_sw_config.py"))
    time.sleep(900)
    print(ret)

    
    with open(log, 'a') as file:
        # Write output to the file
        file.write(ret + "\n")
    
    cmd = '[ -f "/host/FW_Update/nokia.finished" ] && echo "Exists" || echo "Not exists"'
    if "Not exists" in getresult(g_sshpass_cmd.format("Temp123!",ip,cmd)):
        print("Nokia switch update failed")
    else:
        print("Nokia switch update finished")
        os.system("touch /RACKLOG/t6t/RM_logs/{0}/nokia.txt".format(sn_info["RACKSN"]))


    ret = getresult(g_sshpass_cmd.format("Temp123!",ip,"cat /host/FW_Update/status.txt"))
    log_type="WARNING"
    if ret == "Nokia switch update and config finish":
        log_type = "FINISH"
    start_time=time.strftime("%Y%m%d%H%M%S")
    log_file =""
    send_data_sf(start_time,ret, log_type, sn_info["sn"], sn_info["LOCATION"], sn_info["STATION"], log_file, sn_info['MODEL'])
    ret = getresult("sshpass -p '{0}' scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null admin@{1}:{2} {3}".format("Temp123!", ip, "/host/FW_Update/nokia_config.log", f"/RACKLOG/t6t/RACKLOG/{sn_info['RACKSN']}/"))
    os.system("rm /RACKLOG/t6t/RM_logs/{0}/nokia_updating.txt".format(sn_info["RACKSN"]))

def config_switch(sn_info, switch):
    ip = get_ip(sn_info[f"switch_{switch.lower()}_mac"])
    print("switch {0} ip is {1}".format(switch,ip))
    log = "/RACKLOG/{0}/RM_logs/{1}/TOR_{2}.log".format(sn_info['MODEL'].lower(),sn_info["RACKSN"],switch)
    if ip == 1:
        print("Could not get switch {0} IP".format(switch))
        log_type="WARNING"
        message = "TOR-SWITCH-{0}-IP-CHECK-FAIL".format(switch)
        start_time=time.strftime("%Y%m%d%H%M%S")
        log_file =""
        send_data_sf(start_time,message, log_type, sn_info["sn"], sn_info["LOCATION"], sn_info["STATION"], log_file, sn_info['MODEL'])
        return 1
    print(getresult("ssh-keygen -f '/root/.ssh/known_hosts' -R '{0}'".format(ip)))
    time.sleep(10)
    checkSwitch(ip)
    res = check_switch_os_version(ip,log)
    if res == None:
        print("Failed to check switch OS version")
        time.sleep(20)
        log_type="WARNING"
        message = "TOR-SWITCH-{0}-OS-CHECK-FAIL".format(switch)
        start_time=time.strftime("%Y%m%d%H%M%S")
        log_file =""
        send_data_sf(start_time,message, log_type, sn_info["sn"], sn_info["LOCATION"], sn_info["STATION"], log_file, sn_info['MODEL'])
        return 1
    if res == 1:
        if send_file_to_switch(ip,log, sn_info['MODEL']) == None:
            print("Failed to get switch update files")
            time.sleep(20)
            log_type="WARNING"
            message = "SWITCH-FILE-UPLOAD-FAIL"
            start_time=time.strftime("%Y%m%d%H%M%S")
            log_file =""
            send_data_sf(start_time,message, log_type, sn_info["sn"], sn_info["LOCATION"], sn_info["STATION"], log_file, sn_info['MODEL'])
            return 1
        if update_switch_os(ip,log, sn_info['MODEL']) == None:
            print("Failed to update switch OS")
            time.sleep(20)
            log_type="WARNING"
            message = "TOR-SWITCH-{0}-OS-UPDATE-FAIL".format(switch)
            start_time=time.strftime("%Y%m%d%H%M%S")
            log_file =""
            send_data_sf(start_time,message, log_type, sn_info["sn"], sn_info["LOCATION"], sn_info["STATION"], log_file, sn_info['MODEL'])
            return 1
        time.sleep(20)
        print(getresult("ssh-keygen -f '/root/.ssh/known_hosts' -R '{0}'".format(ip)))
        time.sleep(10)
        res = check_switch_os_version(ip,log)
        if res == 0:
            print("OS upgrade successful")
        else:
            print("OS upgrade failed!")
            return 1
    checkSwitch(ip)
    print("Moving files to switch again")
    if send_file_to_switch(ip,log,sn_info['MODEL']) == None:
        print("Failed to get switch update files")
        time.sleep(10)
        log_type="WARNING"
        message = "SWITCH-FILE-UPLOAD-FAIL"
        start_time=time.strftime("%Y%m%d%H%M%S")
        log_file =""
        send_data_sf(start_time,message, log_type, sn_info["sn"], sn_info["LOCATION"], sn_info["STATION"], log_file, sn_info['MODEL'])
        return 1
    if run_SW_Config(ip,log) == None:
        print("Failed to run SW_config.sh")
        log_type="WARNING"
        message = "TOR-SWITCH-{0}-CONFIG-FAIL".format(switch)
        start_time=time.strftime("%Y%m%d%H%M%S")
        log_file =""
        send_data_sf(start_time,message, log_type, sn_info["sn"], sn_info["LOCATION"], sn_info["STATION"], log_file, sn_info['MODEL'])
        return 1
    checkSwitch(ip)
    if switch == "A" or switch == "C":
        if disable_tor(ip,switch,log) == None:
            print("Failed to disable ports")
            log_type="WARNING"
            message = "TOR-SWITCH-{0}-DISABLE-FAIL".format(switch)
            start_time=time.strftime("%Y%m%d%H%M%S")
            log_file =""
            send_data_sf(start_time,message, log_type, sn_info["sn"], sn_info["LOCATION"], sn_info["STATION"], log_file, sn_info['MODEL'])
            return 1     
    return 0

def auto_config_switches(sn_info, switchsn):
    #create updating flag
    updating_flag = g_log_folder.format(sn_info['MODEL'].lower()) + "/{0}/{1}_updating.txt".format(sn_info["RACKSN"], switchsn)
    with open(updating_flag, 'w') as file:
        file.write("updating...")
    switch = ""
    if switchsn == sn_info['switch_a_sn']:
        switch = "A"
    elif switchsn == sn_info['switch_b_sn']:
        switch = "B"
    elif switchsn == sn_info['switch_c_sn']:
        switch = "C"
    elif switchsn == sn_info['switch_d_sn']:
        switch = "D"
    else:
        print("Something is VERY WRONG!")
        return 1
    
    log_type="START"
    message = "START-SWITCH-{0}-UPDATE-AND-CONFIG".format(switch)
    start_time=time.strftime("%Y%m%d%H%M%S")
    log_file =""
    send_data_sf(start_time,message, log_type, sn_info["sn"], sn_info["LOCATION"], sn_info["STATION"], log_file, sn_info['MODEL'])

    result = config_switch(sn_info,switch)

    if result == 1:
        print("Switch Auto Config fail for RACK: {0}, SWITCH {1}!".format(sn_info["RACKSN"], switchsn))
        print("Deleting updating flag...")
        os.remove(updating_flag)
        return 1
    print("Switch update successful")
    os.remove(updating_flag)
    print("Creating switch update complete flag")
    finish_flag = g_log_folder.format(sn_info['MODEL'].lower()) + "/{0}/{1}.txt".format(sn_info["RACKSN"], switchsn)

    with open(finish_flag, 'w') as file:
        file.write("done")
    log_type="FINISH"
    message = "SWITCH-{0}-UPDATE-AND-CONFIG-FINISH".format(switch)
    start_time=time.strftime("%Y%m%d%H%M%S")
    log_file =""
    send_data_sf(start_time,message, log_type, sn_info["sn"], sn_info["LOCATION"], sn_info["STATION"], log_file, sn_info['MODEL'])
    
    if switch == "A":
        ret = config_nokia(sn_info,"nokia")
    return 0

def check_complete(sn_info):
    switch_a_finish_flag = g_log_folder.format(sn_info['MODEL'].lower()) + "/{0}/{1}.txt".format(sn_info['RACKSN'], sn_info['switch_a_sn'])
    switch_b_finish_flag = g_log_folder.format(sn_info['MODEL'].lower()) + "/{0}/{1}.txt".format(sn_info['RACKSN'], sn_info['switch_b_sn'])
    switch_c_finish_flag = g_log_folder.format(sn_info['MODEL'].lower()) + "/{0}/{1}.txt".format(sn_info['RACKSN'], sn_info['switch_c_sn'])
    switch_d_finish_flag = g_log_folder.format(sn_info['MODEL'].lower()) + "/{0}/{1}.txt".format(sn_info['RACKSN'], sn_info['switch_d_sn'])
    nokia_finish_flag = g_log_folder.format(sn_info['MODEL'].lower()) + "/{0}/{1}.txt".format(sn_info['RACKSN'], "nokia")
    if os.path.exists(switch_a_finish_flag) and os.path.exists(switch_b_finish_flag) and os.path.exists(switch_c_finish_flag) and os.path.exists(switch_d_finish_flag) and os.path.exists(nokia_finish_flag): 
        finish_flag = g_log_folder.format(sn_info['MODEL'].lower()) + "/{0}/{0}.txt".format(sn_info["RACKSN"])
        with open(finish_flag, 'w') as file:
            file.write("done")

def main():
    # retrieve serial numbers
    if getPXE() == 1:
        return 1
    serial_numbers = get_serial_numbers()
    print(serial_numbers)
    processes = []
    sn_infos = []
    for sn in serial_numbers:
        #get config info
        sn_info = read_sn_info_from_config(sn)
        if sn_info == 1:
            continue
        print(sn_info)
        sn_infos.append(sn_info)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for sn_info in sn_infos:
            delete = "no"
            switch_a = sn_info['switch_a_sn']
            switch_b = sn_info['switch_b_sn']
            switch_c = sn_info['switch_c_sn']
            switch_d = sn_info['switch_d_sn']
            switch_a_complete = g_log_folder.format(sn_info['MODEL'].lower()) + "/{0}/{1}.txt".format(sn_info['RACKSN'], sn_info['switch_a_sn'])
            print("switch A sn: {0}".format(switch_a))
            print("switch B sn: {0}".format(switch_b))
            print("switch C sn: {0}".format(switch_c))
            print("switch D sn: {0}".format(switch_d))
            if not is_config(sn_info['RACKSN'], switch_a, sn_info['MODEL'].lower()):
                print("Starting switch A config")
                futures.append(executor.submit(auto_config_switches, sn_info, switch_a))
            if not is_config(sn_info['RACKSN'], switch_b, sn_info['MODEL'].lower()):
                print("Starting switch B config")
                futures.append(executor.submit(auto_config_switches, sn_info, switch_b))
            if not is_config(sn_info['RACKSN'], switch_c, sn_info['MODEL'].lower()):
                print("Starting switch C config")
                futures.append(executor.submit(auto_config_switches, sn_info, switch_c))
            if not is_config(sn_info['RACKSN'], switch_d, sn_info['MODEL'].lower()):
                print("Starting switch D config")
                futures.append(executor.submit(auto_config_switches, sn_info, switch_d))
            if os.path.exists(switch_a_complete) and not is_config(sn_info['RACKSN'], "nokia", sn_info['MODEL'].lower()):
                print("Starting nokia switch config")
                futures.append(executor.submit(config_nokia, sn_info, "nokia"))

        # Wait for all tasks to complete and gather the results
        for future in concurrent.futures.as_completed(futures):
            print(future.result()) 
    
    for sn_info in sn_infos:
        check_complete(sn_info)
    return 0

if __name__ == "__main__":
    main()
    print("Done")
