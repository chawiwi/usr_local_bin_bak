from multiprocessing import Process
from pexpect import pxssh

import sys
import os
import time 
import subprocess
from datetime import datetime, timedelta
import base64
import re

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
EDITOR			= "Edward"
RELEASE_DATE	= "2024/03/12"

current_date = datetime.now()
g_model = "MODEL"
g_project = "L15"
g_log_folder = "/RACKLOG/{0}/RM_logs".format(g_project.lower())
g_mainlog_file = "{0}/monitor.log".format(g_log_folder)
g_win_config_folder = "/WIN/{0}/response/config".format(g_project)

g_switch_config_files = ["sonic-aboot-broadcom-20201231.76.swi", "SW_Config.sh"]
g_ycable_files = ["AEC_VERMONT_MV_1.0_20220907.bin","mux_update_T6J_A.py"]
g_script_folder = "/project/edward/L15/"

g_switch_update_folder = "/host/FW_Update/"
g_switch_firmware_folder = "/usr/share/sonic/firmware/"

g_cmd_search_ip_QMF = "grep -B8 -A1 {0} /var/lib/dhcpd/dhcpd.leases | grep lease"
g_cmd_ping = "ping -c 3 {0}"

g_switch_passwords = ["password","Temp123!"]
g_mux_cable = ["Ethernet4", "Ethernet44", "Ethernet68", "Ethernet80", "Ethernet120"]


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

	# message = message.replace("'",'') #20230928 David add

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


def is_file_modified_within_24_hours(file_path):
    # Get the current time
    now = datetime.now()
    # Get the last modified time of the file
    last_modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
    # Calculate the difference
    time_difference = now - last_modified_time
    # Check if the difference is less than or equal to 24 hours
    return time_difference <= timedelta(hours=24)

def get_serial_numbers():
    serial_numbers = []
    for filename in os.listdir(g_win_config_folder):
        if ".txt" in filename:
            if is_file_modified_within_24_hours(g_win_config_folder+"/"+filename):
                print("Try open config file {0}".format(g_win_config_folder + "/" + filename))
                try:
                    with open(g_win_config_folder + "/" + filename,"r") as file:
                        contents = file.read()
                        if 'PARTN=C2189' in contents and 'STATION=PRETEST' in contents:
                            sn = filename[:-4]
                            serial_numbers.append(sn)
                except FileNotFoundError:
                    print("File:{0} not found.".format(filename))
                    return False
    return serial_numbers

def read_sn_info_from_config(file_name):	
    if ".txt" in file_name:
        SNdict = {
			"sn": "NA",
			"RACKSN": "NA",
			"switch_a_mac": "NA",
			"switch_b_mac": "NA",
            "STATION": "NA",
			"LOCATION": "NA",
            "RM": "NA"
		}
        file_path = "{0}/{1}".format(g_win_config_folder, file_name)
        if os.path.isfile(file_path):
            SNdict["sn"] = file_path.split('.')[0].strip().split('/')[-1].strip()
            f = open(file_path)
            for line in f:
                if "RACKSN" in line:
                    SNdict["RACKSN"] = line.split('=')[1].strip()

                if "SWITCHSMLC0" in line:
                    SNdict["switch_a_mac"] = line.split(',')[1].strip()

                if "SWITCHSMLC1" in line:
                    SNdict["switch_b_mac"] = line.split(',')[1].strip()
                if "STATION" in line:
                    SNdict["STATION"] = line.split('=')[1].strip()
                if "LOCATION" in line:
                    SNdict["LOCATION"] = line.split('=')[1].strip()
                if "RACK_MOUNT_MAC1" in line:
                    SNdict["RM"] = line.split('=')[1].strip()
            f.close()
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
    
def getresult(arg1):

	p = subprocess.Popen(arg1, stdout=subprocess.PIPE, shell=True,encoding="utf-8")
	(text, err) = p.communicate()
	res = text
	return res

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
				#sendlog(log,"PASS")
				#log = "Check RM Connection IP ={0}".format(line)
				if os.system(g_cmd_ping.format(line)) == 0:
					return line
			else:
				break
	return 1

def is_config(sn_info):
    flag_path = g_log_folder + "/{0}/{0}.txt".format(sn_info["RACKSN"])
    flag_dir = g_log_folder + "/{0}/".format(sn_info["RACKSN"])
    updating_flag = g_log_folder + "/{0}/{1}.txt".format(sn_info["RACKSN"], "Updating")
    if os.path.exists(flag_path):
        print("{0} already configured".format(sn_info["RACKSN"]))
        return True
    elif os.path.exists(updating_flag):
        filetime = os.path.getmtime(updating_flag)
        current_time = time.time()
        timeout = (current_time - filetime) / 60
        if timeout > 120:
            os.remove(updating_flag)
            return False 
        else:
            print("{0} already configuring...".format(sn_info["RACKSN"]))
            return True
    elif os.path.exists(flag_dir):
        return False
    else:
        os.mkdir(flag_dir)
        return False
    

def switch_password():
    global g_switch_passwords 
    g_switch_passwords = g_switch_passwords[::-1]

def login_to_switch(ip):
    for password in g_switch_passwords:
        try:
            ssh_object = pxssh.pxssh()
            ssh_object.login(ip,"admin",password, auto_prompt_reset=False)
            if password == g_switch_passwords[1]:
                 switch_password()
                 print("Password switched to: {0}".format(g_switch_passwords[0]))
            return ssh_object
        except pxssh.ExceptionPxssh as e:
            print("Failed to login to Switch")
            print(e)

    return None

def send_file_to_switch(ip,log):
    cmdstr = "sudo scp -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null root@10.0.3.254:/project/edward/L15/* /host/FW_Update/"
    ssh_object = login_to_switch(ip)
    if ssh_object == None:
        return None
    try:
        ssh_object.buffer = b""
        ssh_object.sendline(cmdstr)
        time.sleep(1)
        ssh_object.prompt()
        ssh_object.sendline('M1cr0$0ft')
        ssh_object.prompt()
        time.sleep(120)
        output = ssh_object.before.decode ('utf-8')
        print(output)
        with open(log, 'a') as file:
            # Write output to the file
            file.write(output + "\n")
        return 0
    except pxssh.ExceptionPxssh as e:
        print("Failed to run command")
        print(e)
        return None
    
def send_mux_firmware_to_switch(ip,log):
    cmdstr = "sudo scp -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null root@10.0.3.254:/project/edward/L15/*.bin /usr/share/sonic/firmware/"
    ssh_object = login_to_switch(ip)
    if ssh_object == None:
        return None
    try:
        ssh_object.buffer = b""
        ssh_object.sendline(cmdstr)
        time.sleep(4)
        ssh_object.prompt()
        ssh_object.sendline('M1cr0$0ft')
        ssh_object.prompt()
        time.sleep(30)
        output = ssh_object.before.decode ('utf-8')
        print(output)
        with open(log, 'a') as file:
            # Write output to the file
            file.write(output + "\n")
        return 0
    except pxssh.ExceptionPxssh as e:
        print("Failed to run command")
        print(e)
        return None

def check_switch_os_version(ip,log):
    ssh_object = login_to_switch(ip)
    if ssh_object == None:
        return None
    try:
        ssh_object.buffer = b""
        ssh_object.sendline("show version")
        time.sleep(3)
        ssh_object.prompt()
        output = ssh_object.before.decode ('utf-8')
        with open(log, 'a') as file:
            # Write output to the file
            file.write(output + "\n")
        print(output)
        if "SONiC Software Version: SONiC.20201231.76" not in output:
            print("Os need update")
            ssh_object.buffer = b""
            ssh_object.sendline("sudo mkdir /host/FW_Update")
            time.sleep(3)
            ssh_object.prompt()
            output = ssh_object.before.decode ('utf-8')
            print(output)
            with open(log, 'a') as file:
                # Write output to the file
                file.write(output + "\n")
            return 1
        print("Os already updated")
        return 0
    except pxssh.ExceptionPxssh as e:
        print("Failed to run command")
        print(e)
        return None

def update_switch_os(ip,log):
    ssh_object = login_to_switch(ip)
    if ssh_object == None:
        return None
    try:
        ssh_object.buffer = b""
        ssh_object.sendline("sudo sonic-installer install /host/FW_Update/sonic-aboot-broadcom-20201231.76.swi -y")
        time.sleep(60)
        ssh_object.prompt()
        output = ssh_object.before.decode ('utf-8')
        print(output)
        with open(log, 'a') as file:
            # Write output to the file
            file.write(output + "\n")
        ssh_object.buffer = b""
        ssh_object.sendline("sudo reboot")
        output = ssh_object.before.decode ('utf-8')
        print(output)
        with open(log, 'a') as file:
            # Write output to the file
            file.write(output + "\n")
        time.sleep(200)
        return 0
		
    except pxssh.ExceptionPxssh as e:
        print("Failed to run command")
        print(e)
        return None

def run_SW_Config(ip,log):
    ssh_object = login_to_switch(ip)
    if ssh_object == None:
        return None
    try:
        ssh_object.buffer = b""
        print("sudo bash /host/FW_Update/SW_Config.sh")
        ssh_object.sendline("sudo bash /host/FW_Update/SW_Config.sh")
        time.sleep(500)
        ssh_object.prompt()
        output = ssh_object.before.decode ('utf-8')
        print(output)
        with open(log, 'a') as file:
            # Write output to the file
            file.write(output + "\n")
        return 0
    except pxssh.ExceptionPxssh as e:
        print("Failed to run command")
        print(e)
        return None

def checkInterfaceStatus(ip,log):
    ssh_object = login_to_switch(ip)
    if ssh_object == None:
        return None
    try:
        time.sleep(5)
        ssh_object.buffer = b""
        ssh_object.sendline("show interface status")
        time.sleep(20)
        ssh_object.prompt()
        output = ssh_object.before.decode ('utf-8')
        print(output)
        with open(log, 'a') as file:
            # Write output to the file
            file.write(output + "\n")
        if 'Ethernet24' not in output:
            print("Switch interface not found, FAILED to CONFIG")
            return False
        return True
    except pxssh.ExceptionPxssh as e:
        print("Failed to run command")
        print(e)
        return None

def check_mux_firmware(ip,log):
    ssh_object = login_to_switch(ip)
    if ssh_object == None:
        return None
    try:
        for eth in g_mux_cable:
            ssh_object.buffer = b""
            ssh_object.sendline("show mux firmware version {0}".format(eth))
            time.sleep(20)
            ssh_object.prompt()
            output = ssh_object.before.decode ('utf-8')
            print(output)

            with open(log, 'a') as file:
                # Write output to the file
                file.write(output + "\n")
            if 'version_nic_active": "N/A' in output:
                return 2
            if '"version_nic_active": "1.0MV",' not in output or '"version_peer_active": "1.0MV",' not in output:
                return 1
        return 0
    except pxssh.ExceptionPxssh as e:
        print("Failed to run command")
        print(e)
        return None
    
def check_fpga_firmware(ip,log):
    ssh_object = login_to_switch(ip)
    if ssh_object == None:
        return None
    try:
        for eth in g_mux_cable:
            ssh_object.buffer = b""
            ssh_object.sendline("cat /proc/scd")
            time.sleep(5)
            ssh_object.prompt()
            output = ssh_object.before.decode ('utf-8')

            with open(log, 'a') as file:
                # Write output to the file
                file.write(output + "\n")
            if "0x70001" in output:
                print("Switch FPGA FW incorrect")
                return 1
        return 0
    except pxssh.ExceptionPxssh as e:
        print("Failed to run command")
        print(e)
        return None
    
def downgrade_fpga_firmware(ip,log):
    #WIP 
    ssh_object = login_to_switch(ip)
    if ssh_object == None:
        return None
    try:
        ssh_object.buffer = b""
        ssh_object.sendline("cd /host")
        time.sleep(5)
        ssh_object.prompt()
        ssh_object.sendline("sudo scp -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null root@10.0.3.254:/project/edward/*.deb .")
        time.sleep(10)
        ssh_object.prompt()

        ssh_object.sendline("M1cr0$0ft")
        time.sleep(20)
        ssh_object.prompt()

        ssh_object.sendline("sudo dpkg -i libcrypt1_4.4.18-4_amd64.deb")
        time.sleep(25)
        ssh_object.prompt()

        ssh_object.sendline("echo 'deb [arch=amd64] http://ftp.us.debian.org/debian sid main' | sudo tee -a /etc/apt/sources.list")
        time.sleep(8)
        ssh_object.prompt()

        ssh_object.sendline("sudo apt-get update")
        time.sleep(40)
        ssh_object.prompt()

        ssh_object.sendline("sudo apt-get -f install libgcc-s1 -y")
        time.sleep(30)
        ssh_object.prompt()
        ssh_object.sendline("yes")
        time.sleep(20)
        ssh_object.prompt()

        ssh_object.sendline("sudo dpkg -i arista-firmware-tools_1.0.0_amd64.deb")
        time.sleep(25)
        ssh_object.prompt()

        ssh_object.sendline("sudo dpkg -i arista-firmware-images_1.0.0_amd64.deb")
        time.sleep(25)
        ssh_object.prompt()

        ssh_object.sendline("sudo touch /host/forceFpgaUpgrade")
        time.sleep(10)
        ssh_object.prompt()

        ssh_object.sendline("sudo apt-get install --reinstall openssh-server -y")
        time.sleep(30)
        ssh_object.prompt()
        ssh_object.sendline("2")
        time.sleep(20)
        ssh_object.prompt()

        output = ssh_object.before.decode ('utf-8')
        print(output)
        with open(log, 'a') as file:
            # Write output to the file
            file.write(output + "\n")
        print("Rebooting...")
        ssh_object.buffer = b""
        ssh_object.sendline("sudo reboot")
        time.sleep(200)
        return 0
    except pxssh.ExceptionPxssh as e:
        print("Failed to run command")
        print(e)
        return None

def post_downgrade_clean(ip,log):
    ssh_object = login_to_switch(ip)
    if ssh_object == None:
        return None
    try:
        ssh_object.buffer = b""
        ssh_object.sendline("sudo rm /host/forceFpgaUpgrade")
        time.sleep(10)                                                 
        ssh_object.prompt()

        ssh_object.sendline("sudo dpkg -P arista-firmware-tools arista-firmware-images")
        time.sleep(20)                                                 
        ssh_object.prompt()
        output = ssh_object.before.decode ('utf-8')
        print(output)
        with open(log, 'a') as file:
            # Write output to the file
            file.write(output + "\n")
        return 0
    except pxssh.ExceptionPxssh as e:
        print("Failed to run command")
        print(e)
        return None
    
def run_y_cable_update(ip,log):
    cmd = "sshpass -p 'Temp123!' ssh admin@{0} 'sudo python3 /host/FW_Update/mux_update_T6J_A.py'".format(ip)
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


def config_switch(sn_info, switch):
    if switch == 0:
        ip = get_ip(sn_info["switch_a_mac"])
        tor = "A"
        mac = sn_info["switch_a_mac"]
        log = "/RACKLOG/l15/RM_logs/{0}/TOR_{1}.log".format(sn_info["RACKSN"],tor)
    else:
        ip = get_ip(sn_info["switch_b_mac"])
        tor = "B"
        mac = sn_info["switch_b_mac"]
        log = "/RACKLOG/l15/RM_logs/{0}/TOR_{1}.log".format(sn_info["RACKSN"],tor)
    if ip == 1:
        print("Could not get switch {0} IP".format(switch))
        log_type="WARNING"
        message = "TOR-SWITCH-{0}-IP-CHECK-UNSUCCESSFUL".format(tor)
        start_time=time.strftime("%Y%m%d%H%M%S")
        log_file =""
        send_data_sf(start_time,message, log_type, sn_info["sn"], sn_info["LOCATION"], sn_info["STATION"], log_file)
        return 1
    print(getresult("ssh-keygen -f '/root/.ssh/known_hosts' -R '{0}'".format(ip)))
    time.sleep(10)
    res = check_switch_os_version(ip,log)
    time.sleep(20)
    if res == None:
        print("Failed to check switch OS version")
        time.sleep(30)
        log_type="WARNING"
        message = "TOR-SWITCH-{0}-OS-CHECK-UNSUCCESSFUL".format(tor)
        start_time=time.strftime("%Y%m%d%H%M%S")
        log_file =""
        send_data_sf(start_time,message, log_type, sn_info["sn"], sn_info["LOCATION"], sn_info["STATION"], log_file)
        return 1
    if send_file_to_switch(ip,log) == None:
        print("Failed to get switch update files")
        time.sleep(20)
        log_type="WARNING"
        message = "SWITCH-FILE-UPLOAD-UNSUCCESSFUL"
        start_time=time.strftime("%Y%m%d%H%M%S")
        log_file =""
        send_data_sf(start_time,message, log_type, sn_info["sn"], sn_info["LOCATION"], sn_info["STATION"], log_file)
        return 1
    if res == 1:
        if update_switch_os(ip,log) == None:
            print("Failed to update switch OS")
            time.sleep(20)
            log_type="WARNING"
            message = "TOR-SWITCH-{0}-OS-UPDATE-UNSUCCESSFUL".format(tor)
            start_time=time.strftime("%Y%m%d%H%M%S")
            log_file =""
            send_data_sf(start_time,message, log_type, sn_info["sn"], sn_info["LOCATION"], sn_info["STATION"], log_file)
            return 1
        time.sleep(100)
        print(getresult("ssh-keygen -f '/root/.ssh/known_hosts' -R '{0}'".format(ip)))
        time.sleep(10)
        res = check_switch_os_version(ip,log)
        if res == 0:
            print("OS upgrade successful")
        else:
            print("OS upgrade failed!")
            return 1

    if run_SW_Config(ip,log) == None:
        print("Failed to run SW_Config.sh")
        log_type="WARNING"
        message = "TOR-SWITCH-{0}-CONFIG-UNSUCCESSFUL".format(tor)
        start_time=time.strftime("%Y%m%d%H%M%S")
        log_file =""
        send_data_sf(start_time,message, log_type, sn_info["sn"], sn_info["LOCATION"], sn_info["STATION"], log_file)
        return 1
        
    time.sleep(10)
    if checkInterfaceStatus(ip,log) == False:
        if check_fpga_firmware(ip,log) == 1:
            if downgrade_fpga_firmware(ip,log) == 1:
                print("Failed to downgrade switch fpga FW")
                log_type="WARNING"
                message = "TOR-SWITCH-{0}-FPGA-FW-DOWNGRADE-UNSUCCESSFUL".format(tor)
                start_time=time.strftime("%Y%m%d%H%M%S")
                log_file =""
                send_data_sf(start_time,message, log_type, sn_info["sn"], sn_info["LOCATION"], sn_info["STATION"], log_file)
                return 1
            time.sleep(120)
            if check_fpga_firmware(ip,log) == 1:
                print("Failed to downgrade switch fpga FW")
                log_type="WARNING"
                message = "TOR-SWITCH-{0}-FPGA-FW-DOWNGRADE-UNSUCCESSFUL".format(tor)
                start_time=time.strftime("%Y%m%d%H%M%S")
                log_file =""
                send_data_sf(start_time,message, log_type, sn_info["sn"], sn_info["LOCATION"], sn_info["STATION"], log_file)
                return 1
            time.sleep(5)
            if post_downgrade_clean(ip,log) == 1:
                print("Failed to clean switch after downgrade")
                log_type="WARNING"
                message = "TOR-SWITCH-{0}-POST-DOWNGRADE-UNSUCCESSFUL".format(tor)
                start_time=time.strftime("%Y%m%d%H%M%S")
                log_file =""
                send_data_sf(start_time,message, log_type, sn_info["sn"], sn_info["LOCATION"], sn_info["STATION"], log_file)
                return 1
                       

    if switch == 1:
        mux =  check_mux_firmware(ip,log)
        if mux == 1:    
            print("y-cable need update")
            time.sleep(5)
            if send_mux_firmware_to_switch(ip,log) == None:
                print("Failed to get Y-cable firmware file")
                return 1
            time.sleep(5)
            if run_y_cable_update(ip,log) == None:
                print("y-cable update failed!")
                log_type="WARNING"
                message = "Y-CABLE-UPDATE-UNSUCCESSFUL-TO-RUN-PLEASE-CHECK"
                start_time=time.strftime("%Y%m%d%H%M%S")
                log_file =""
                send_data_sf(start_time,message, log_type, sn_info["sn"], sn_info["LOCATION"], sn_info["STATION"], log_file)
                return 1
            if check_mux_firmware(ip,log) == 1:
                print("y-cable update failed!")
                log_type="WARNING"
                message = "Y-CABLE-UPDATE-UNSUCCESSFUL-PLEASE-CHECK"
                start_time=time.strftime("%Y%m%d%H%M%S")
                log_file =""
                send_data_sf(start_time,message, log_type, sn_info["sn"], sn_info["LOCATION"], sn_info["STATION"], log_file)
                return 1
        elif mux == 2:
            print("Y-cable connection missing!")
        else:
            print("y-cable does not need update")
    print("Switch config for {0}:{1} complete".format(mac,ip))
    with open(log, 'a') as file:
        # Write output to the file
        file.write("Switch config for {0}:{1} complete".format(mac,ip) + "\n")
    return 0

def auto_config_switches(sn_info):
    if get_ip(sn_info["RM"]) == 1:
        print("Rack Not on Line")
        return 1
    #create updating flag
    updating_flag = g_log_folder + "/{0}/{1}.txt".format(sn_info["RACKSN"], "Updating")
    with open(updating_flag, 'w') as file:
        file.write("updating...")
    if not os.path.exists("/RACKLOG/l15/RM_logs/{0}/".format(sn_info["sn"])):
        os.makedirs("/RACKLOG/l15/RM_logs/{0}/".format(sn_info["sn"]))
    with open("/RACKLOG/l15/RM_logs/{0}/{0}_updating.log".format(sn_info["sn"]), 'w') as file:
        file.write("updating...")
    #Update switch A
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
        print("Deleting updating flag...")
        os.remove(updating_flag)
        return 1
    os.remove(updating_flag)
    print("Creating switch update complete flag")
    finish_flag = g_log_folder + "/{0}/{0}.txt".format(sn_info["RACKSN"])
    with open(finish_flag, 'w') as file:
        file.write("done")
    log_type="FINISH"
    message = "SWITCH-UPDATE-AND-CONFIG-FINISH"
    start_time=time.strftime("%Y%m%d%H%M%S")
    log_file =""
    send_data_sf(start_time,message, log_type, sn_info["sn"], sn_info["LOCATION"], sn_info["STATION"], log_file)
    if os.path.exists("/RACKLOG/l15/RM_logs/{0}/{0}_updating.log".format(sn_info["sn"])):
        os.remove("/RACKLOG/l15/RM_logs/{0}/{0}_updating.log".format(sn_info["sn"]))
    return 0

def main():
    # retrieve serial numbers
    print(current_date.date())
    serial_numbers = get_serial_numbers()
    print(serial_numbers)
    processes = []

    for sn in serial_numbers:
        #get config info
        sn_info = read_sn_info_from_config(sn +".txt")
        print(sn_info)
        if not is_config(sn_info):
            print("Not config")
            p = Process(target=auto_config_switches, args=(sn_info,))
            p.start()
            processes.append(p)
            time.sleep(5)
        else:
            print("Is config")
    time.sleep(100)
    for p in processes:
         p.join()
         print("finished")
         time.sleep(60)

    return 0

if __name__ == "__main__":
    main()
    print("Done")
