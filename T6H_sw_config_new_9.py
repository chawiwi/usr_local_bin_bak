from multiprocessing import Process
from zeep import Client
import json
import xml.etree.ElementTree as ET
import sys
import os
import time 
import re
import subprocess
from datetime import datetime
api_url = 'http://192.168.66.20/AMA_L11/AMAService.svc?singleWsdl'
PXE_map = { "192.168.202.26": "Q9", "192.168.202.47": "Q8", "192.168.202.46": "Q7","192.168.202.21": "Q6","192.168.202.20": "Q5"}

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
VERSION			= "2.0.3"
EDITOR			= "An"
RELEASE_DATE	= "2024/04/04"

current_date = datetime.now()
g_model = "MODEL"
g_project = "T6H"
g_log_folder = "/RACKLOG/{0}/RM_logs".format(g_project.lower())
g_mainlog_file = "{0}/monitor.log".format(g_log_folder)
g_win_config_folder = "/WIN/{0}/response/config".format(g_project)

g_switch_config_files = ["sonic-aboot-broadcom-20201231.76.swi", "SW_Config.sh"]
g_ycable_files = ["AEC_VERMONT_MV_1.0_20220907.bin","mux_update_T6H_A_V710_20240628.py"]
g_script_folder = "/project/firmware/t6h/switch"

g_switch_update_folder = "/host/FW_Update/"
g_switch_firmware_folder = "/usr/share/sonic/firmware/"

g_cmd_search_ip_QMF = "grep -B8 -A1 {0} /var/lib/dhcpd/dhcpd.leases | grep lease"
g_cmd_ping = "ping -c 3 {0}"

g_switch_passwords = ["password","Temp123!"]

g_sshpass_cmd = "sshpass -p '{0}' ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null admin@{1} '{2}'"
g_sshpass_scp = "sshpass -p '{0}' scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null {1} admin@{2}:{3}"

def getPXE():
    cmd = "ip a"
    global PXE
    res = getresult(cmd)
    print(res)
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

def send_data_sf(start_time,message,log_type, sf_sn, location, station, log_file):

	st_file = "/home/Monitor_reconfig_CP/{0}.ST".format(sf_sn)
     
	head_location = '/WIN/'+g_project+'/'
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

def is_config(racksn):
    flag_path = g_log_folder + "/{0}/{0}.txt".format(racksn)
    flag_dir = g_log_folder + "/{0}/".format(racksn)
    updating_flag = g_log_folder + "/{0}/{1}.txt".format(racksn, "Updating")
    if os.path.exists(flag_path):
        print("{0} already configured".format(racksn))
        return True
    elif os.path.exists(updating_flag):
        print("{0} already configuring...".format(racksn))
        return True
    elif os.path.exists(flag_dir):
        return False
    else:
        os.mkdir(flag_dir)
        return False

def get_serial_numbers():
    serial_numbers = []
    WIP = getWIP()
    if len(WIP) < 1:
        return serial_numbers
    
    for rack in WIP:
        if not is_config(rack):
            print("{0} is not configured!".format(rack))
            servers = getServers(rack)
            serial_numbers.append(servers[0])
    return serial_numbers

def read_sn_info_from_config(sn):	
    SNdict = {
        "sn": "NA",
        "RACKSN": "NA",
        "switch_a_mac": "NA",
        "switch_b_mac": "NA",
        "STATION": "NA",
        "LOCATION": "NA",
        "Supernova": True,
        "JIO": False
    }

    

    config = getConfig(sn)
    if config == 1:
        return 1
    
    SNdict["sn"] = sn
    SNdict["STATION"] = "PRETEST"
    for line in config:
        if line['Parameter'] == "RACK_MOUNT1_MAC1":
            SNdict["Supernova"] = False
        if line['Parameter'] == "PARTN" and line['Value'] != "C2398":
            return 1
        if line['Parameter'] == "SWITCHSMLC1":
            print(line['Value'])
            if re.search("MARVELL",line['Value']):
                SNdict["JIO"] = True

        
    for line in config:
        if line['Parameter'] == "RACKSN":
            SNdict["RACKSN"] = line['Value'].strip()
        if SNdict['JIO']:
            if line['Parameter'] == "SWITCHSMLC0":
                SNdict["switch_a_mac"] = line['Value'].split(',')[1].strip()
            if line['Parameter'] == "SWITCHSMLC2":
                SNdict["switch_b_mac"] = line['Value'].split(',')[1].strip()
        elif SNdict['Supernova']:
            if line['Parameter'] == "SWITCHSMLC0":
                SNdict["switch_a_mac"] = line['Value'].split(',')[1].strip()
            if line['Parameter'] == "SWITCHSMLC1":
                SNdict["switch_b_mac"] = line['Value'].split(',')[1].strip()
        else:
            if line['Parameter'] == "SWITCHSMLC1":
                SNdict["switch_a_mac"] = line['Value'].split(',')[1].strip()
            if line['Parameter'] == "SWITCHSMLC2":
                SNdict["switch_b_mac"] = line['Value'].split(',')[1].strip()

        if line['Parameter'] == "LOCATION":
            SNdict["LOCATION"] = line['Value'].strip()
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
    if "Permission denied" in ret:
        switch_password()
    return 0

def send_file_to_switch(ip,log):
    output = ""
    cmd = "sudo mkdir /host/FW_Update"
    ret = getresult(g_sshpass_cmd.format(g_switch_passwords[0],ip,cmd))
    output = output + ret
    print(ret)
    cmd = "sudo chmod 777 /host/FW_Update"
    ret = getresult(g_sshpass_cmd.format(g_switch_passwords[0],ip,cmd))
    output = output + ret
    print(ret)
    cmd = g_sshpass_scp.format(g_switch_passwords[0],"/project/firmware/t6h/switch/*", ip, "/host/FW_Update/")
    ret = getresult(cmd)
    output = output + ret
    print(ret)
    print("copying to switch")
    time.sleep(10)
    with open(log, 'a') as file:
        # Write output to the file
        file.write(output + "\n")
    return 0
    
def send_mux_firmware_to_switch(ip,log):
    output = ""
    cmd = "sudo chmod 777 /host/FW_Update"
    ret = getresult(g_sshpass_cmd.format(g_switch_passwords[0],ip,cmd))
    output = output + ret
    print(ret)
    cmd = g_sshpass_scp.format(g_switch_passwords[0],"/project/firmware/t6h/switch/*.bin", ip, "/host/FW_Update/")
    ret = getresult(cmd)
    output = output + ret
    print(ret)
    print("copying to switch")
    time.sleep(20)
    cmd = "sudo cp /host/FW_Update/*.bin /usr/shared/sonic/firmware/"
    ret = getresult(g_sshpass_cmd.format(g_switch_passwords[0],ip,cmd))
    output = output + ret
    print(ret)
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

def update_switch_os(ip,log):
    
    cmd = "sudo sonic-installer install /host/FW_Update/sonic-aboot-broadcom-20201231.76.swi -y"
    ret = getresult(g_sshpass_cmd.format(g_switch_passwords[0],ip,cmd))
    time.sleep(40)
    print(ret)
    with open(log, 'a') as file:
        # Write output to the file
        file.write(ret + "\n")
    cmd = "sshpass -p '{0}' ssh -o  StrictHostKeyChecking=no -o ConnectTimeout=10 -o UserKnownHostsFile=/dev/null admin@{1} 'sudo reboot'"
    getresult(cmd.format(g_switch_passwords[0],ip),5)
    time.sleep(60)
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

def run_y_cable_update(ip,log):
    cmd = "sshpass -p 'Temp123!' ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null admin@{0} 'sudo python3 /host/FW_Update/mux_update_T6H_A_V710_20240628.py'".format(ip)
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    output = result.stdout
    errors = result.stderr
    print(output)
    with open(log, 'a') as file:
        # Write output to the file
        file.write(output + "\n")
        if errors:
            file.write(errors + "\n")
            print(errors)
            return None
    return 0

def disable_uplink(sn_info):
    ip = get_ip(sn_info["switch_a_mac"])
    if ip != 1:
        checkSwitch(ip)
        cmd = "sudo portconfig -p Ethernet24 -s 40000"
        ret = getresult(g_sshpass_cmd.format(g_switch_passwords[0],ip,cmd))
    ip = get_ip(sn_info["switch_b_mac"])
    if ip != 1:
        checkSwitch(ip)
        cmd = "sudo portconfig -p Ethernet24 -s 40000"
        ret = getresult(g_sshpass_cmd.format(g_switch_passwords[0],ip,cmd))
    return 0

def enable_uplink(sn_info):
    ip = get_ip(sn_info["switch_a_mac"])
    if ip != 1:
        checkSwitch(ip)
        cmd = "sudo portconfig -p Ethernet24 -s 100000"
        ret = getresult(g_sshpass_cmd.format(g_switch_passwords[0],ip,cmd))
    ip = get_ip(sn_info["switch_b_mac"])
    if ip != 1:
        checkSwitch(ip)
        cmd = "sudo portconfig -p Ethernet24 -s 100000"
        ret = getresult(g_sshpass_cmd.format(g_switch_passwords[0],ip,cmd))
    return 0

def config_switch(sn_info, switch):
    if switch == 0:
        ip = get_ip(sn_info["switch_a_mac"])
        tor = "A"
        log = "/RACKLOG/t6h/RM_logs/{0}/TOR_{1}.log".format(sn_info["RACKSN"],tor)
    else:
        ip = get_ip(sn_info["switch_b_mac"])
        tor = "B"
        log = "/RACKLOG/t6h/RM_logs/{0}/TOR_{1}.log".format(sn_info["RACKSN"],tor)
    if ip == 1:
        print("Could not get switch {0} IP".format(switch))
        log_type="WARNING"
        message = "TOR-SWITCH-{0}-IP-CHECK-FAIL".format(tor)
        start_time=time.strftime("%Y%m%d%H%M%S")
        log_file =""
        send_data_sf(start_time,message, log_type, sn_info["sn"], sn_info["LOCATION"], sn_info["STATION"], log_file)
        return 1
    print(getresult("ssh-keygen -f '/root/.ssh/known_hosts' -R '{0}'".format(ip)))
    time.sleep(10)
    checkSwitch(ip)
    res = check_switch_os_version(ip,log)
    if res == None:
        print("Failed to check switch OS version")
        time.sleep(10)
        log_type="WARNING"
        message = "TOR-SWITCH-{0}-OS-CHECK-FAIL".format(tor)
        start_time=time.strftime("%Y%m%d%H%M%S")
        log_file =""
        send_data_sf(start_time,message, log_type, sn_info["sn"], sn_info["LOCATION"], sn_info["STATION"], log_file)
        return 1
    if res == 1:
        if send_file_to_switch(ip,log) == None:
            print("Failed to get switch update files")
            time.sleep(10)
            log_type="WARNING"
            message = "SWITCH-FILE-UPLOAD-FAIL"
            start_time=time.strftime("%Y%m%d%H%M%S")
            log_file =""
            send_data_sf(start_time,message, log_type, sn_info["sn"], sn_info["LOCATION"], sn_info["STATION"], log_file)
            return 1
        if update_switch_os(ip,log) == None:
            print("Failed to update switch OS")
            time.sleep(20)
            log_type="WARNING"
            message = "TOR-SWITCH-{0}-OS-UPDATE-FAIL".format(tor)
            start_time=time.strftime("%Y%m%d%H%M%S")
            log_file =""
            send_data_sf(start_time,message, log_type, sn_info["sn"], sn_info["LOCATION"], sn_info["STATION"], log_file)
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
    if send_file_to_switch(ip,log) == None:
        print("Failed to get switch update files")
        time.sleep(10)
        log_type="WARNING"
        message = "SWITCH-FILE-UPLOAD-FAIL"
        start_time=time.strftime("%Y%m%d%H%M%S")
        log_file =""
        send_data_sf(start_time,message, log_type, sn_info["sn"], sn_info["LOCATION"], sn_info["STATION"], log_file)
        return 1
    if run_SW_Config(ip,log) == None:
        print("Failed to run SW_config.sh")
        log_type="WARNING"
        message = "TOR-SWITCH-{0}-CONFIG-FAIL".format(tor)
        start_time=time.strftime("%Y%m%d%H%M%S")
        log_file =""
        send_data_sf(start_time,message, log_type, sn_info["sn"], sn_info["LOCATION"], sn_info["STATION"], log_file)
        return 1
    checkSwitch(ip)
    if switch == 1:
        if send_mux_firmware_to_switch(ip,log) == None:
            print("Failed to get Y-cable firmware file")
            return 1
        if run_y_cable_update(ip,log) == None:
            print("Failed to run y-cable update script")
    print("Switch config for {0} complete".format(ip))
    return 0

def auto_config_switches(sn_info):
    #create updating flag
    updating_flag = g_log_folder + "/{0}/{1}.txt".format(sn_info["RACKSN"], "Updating")
    with open(updating_flag, 'w') as file:
        file.write("updating...")
    if not os.path.exists("/RACKLOG/t6h/RM_logs/{0}/".format(sn_info["sn"])):
        os.makedirs("/RACKLOG/t6h/RM_logs/{0}/".format(sn_info["sn"]))
    with open("/RACKLOG/t6h/RM_logs/{0}/{0}_updating.log".format(sn_info["sn"]), 'w') as file:
        file.write("updating...")
    log_type="START"
    message = "START-SWITCH-A-UPDATE-AND-CONFIG"
    start_time=time.strftime("%Y%m%d%H%M%S")
    log_file =""
    send_data_sf(start_time,message, log_type, sn_info["sn"], sn_info["LOCATION"], sn_info["STATION"], log_file)

    resultA = config_switch(sn_info,0)

    if resultA == 1:
        time.sleep(60)        

    log_type="START"
    message = "START-SWITCH-B-UPDATE-AND-CONFIG"
    start_time=time.strftime("%Y%m%d%H%M%S")
    log_file =""
    send_data_sf(start_time,message, log_type, sn_info["sn"], sn_info["LOCATION"], sn_info["STATION"], log_file)

    resultB = config_switch(sn_info,1)

    print("Switch A result:{0}".format(resultA))
    print("Switch B result:{0}".format(resultB))
    if resultA == 1 or resultB == 1:
        print("Switch Auto Config fail for {0}!".format(sn_info["RACKSN"]))
        disable_uplink(sn_info)
        print("Deleting updating flag...")
        os.remove(updating_flag)
        return 1
    os.remove(updating_flag)
    print("Creating switch update complete flag")
    enable_uplink(sn_info)
    finish_flag = g_log_folder + "/{0}/{0}.txt".format(sn_info["RACKSN"])
    with open(finish_flag, 'w') as file:
        file.write("done")
    log_type="FINISH"
    message = "SWITCH-UPDATE-AND-CONFIG-FINISH"
    start_time=time.strftime("%Y%m%d%H%M%S")
    log_file =""
    send_data_sf(start_time,message, log_type, sn_info["sn"], sn_info["LOCATION"], sn_info["STATION"], log_file)
    if os.path.exists("/RACKLOG/t6h/RM_logs/{0}/{0}_updating.log".format(sn_info["sn"])):
        os.remove("/RACKLOG/t6h/RM_logs/{0}/{0}_updating.log".format(sn_info["sn"]))
    return 0

def main():
    # retrieve serial numbers
    if getPXE() == 1:
        return 1
    serial_numbers = get_serial_numbers()
    print(serial_numbers)
    processes = []

    for sn in serial_numbers:
        #get config info
        sn_info = read_sn_info_from_config(sn)
        if sn_info == 1:
            continue
        print(sn_info)
        p = Process(target=auto_config_switches, args=(sn_info,))
        p.start()
        processes.append(p)
        time.sleep(5)
    time.sleep(8000)

    for p in processes:
        p.join()
        print("finished")
        time.sleep(60)

    return 0

if __name__ == "__main__":
    main()
    print("Done")
