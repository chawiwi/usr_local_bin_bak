from multiprocessing import Process
from pyexpat import model
from pexpect import pxssh
import sys
import os
import time 
import subprocess
import configparser
import shutil
import errno

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

g_Model = "MODEL"
g_project = "t6j"
g_log_folder = "/RACKLOG/{}/RM_logs".format(g_project) #QMF
#g_log_folder = "/mnt/test_log/{}/RM_logs".format(g_project) #QTMC
#g_log_folder = "log"
# g_sf_config_folder = "/WIN/NetApp/Response/" #QMF
g_sf_config_folder = "/WIN/{}/sfconfig/".format(g_project) #QMF2
#g_sf_config_folder = "/win/monitor/Manual/" #QTMC
#g_sf_config_folder = "monitor/" #QCI
g_DHCP_folder = ""
g_PXE_grub_folder = "/tftpboot/pxelinux.cfg"
g_tftp_ip = "10.0.3.254"
g_tftp_user = "root"
g_tftp_passwd = "M1cr0$0ft"
#build_side = "QTMC"
#build_side = "QCI"
build_side = "QMF"

g_cp_FPGA_firmware="CelestialPeak_SysInt_4.1.1-70c6abd1_jic.rpd"
g_cp_FPGA_firmware_loc="/project/firmware/{}/cp/{}".format(g_project,g_cp_FPGA_firmware)
g_overlake_image_path = "/tftpboot/firmware/Celestial_Peak/dropcp-2.15FW-stos2008.4.23031201/rMedia/"
upgrade_image = "overlake-2008.4.23031201-prod.img"
# g_cp_Cerberus_fw="cerberus_v2.4.11.4.bin"
# g_cp_Cerberus_fw_loc="/project/firmware/{}/cp/{}".format(g_project,g_cp_Cerberus_fw)

###############
##BMC command define
###############
g_bmc_username		= "admin"
g_bmc_password 		= "admin"
g_bmc_port_to_CP	= "8295"

#############################
# SoC Update Command Define #
#############################
g_cmd_get_soc_firmware_ver = "cat /proc/device-tree/firmware/version"
g_cmd_get_soc_nitro_firmware_ver = "cat /proc/device-tree/firmware/nitro-version"
g_cmd_get_soc_cerberus_firmware_ver = "cerberus_utility fwversion"
g_cmd_copy_image_to_rm = "set manager tftp get -s {0} -f {1}{2}"
g_cmd_mount_image_on_soc = "set system remotedrive mount -i {0} -b 1 -n {1}"
g_cmd_check_sda_exist = "lsblk | grep -i 'sda'"
g_cmd_set_bootmode_to_two = "bootmode set 2"
g_cmd_reboot = "reboot"
g_cmd_socflash = "socflash"
g_os_path = "firmware/{}/stos/Image_rsa.img".format(g_project)
g_cmd_emmcflash = "emmcflash -t {0} -a {1} -b {1} -s".format(g_tftp_ip, g_os_path)
g_cmd_mkdir_usb_folder = "mkdir -p /tmp/usb"
g_cmd_mount_usb_folder = "mount /dev/sda1 /tmp/usb"
g_cmd_check_bin_file_exist = "ls -al /tmp/usb"
#fip_pfm_file  = "A2040.FIP.PFM.46.bin"
fip_fw_file = "fip.bin"
#nitro_pfm_file = "A2040.NITRO.PFM.46.bin"
nitro_fw_file = "nitro.img"
g_cmd_update_sop = [#"cerberus_utility pfmupdate 0 /tmp/usb/{} 0".format(fip_pfm_file), #T6G not PFM activate
					"cerberus_utility socfwupdate 0 /tmp/usb/fip.bin 1",
		#			"cerberus_utility pfmupdate 1 /tmp/usb/{} 0".format(nitro_pfm_file), #T6G not PFM activate
					"cerberus_utility socfwupdate 1 /tmp/usb/nitro.img"]

g_cmd_set_bootmode_to_zero = "bootmode set 0"
g_cmd_reset_soc = "cerberus_utility socreset"
g_cmd_update_fpga = "fpgadiagnostics -writeFlashjic {0}"
g_cmd_cerberus_prov_chk = "cerberus_utility getcertstate"
g_cmd_cerberus_pfm_chk = "cerberus_utility pfmid {0} 0"
g_cmd_cerberus_exportcsr = "cerberus_utility exportcsr /tmp/{0}"
g_cmd_cerberus_prov_import = "cerberus_utility importsignedcert {0} /tmp/{1}"


#*****************************************************************************
# Function   : getresult
# Description: Get the return value, stdout, stderr from input system command 
# Inputs     : arg1: the command tobe execute
# Outputs    : return value, stdout, stderr from the result of input command
# Notice     : use subprocess.Popen(), no command result will show on screen
#*****************************************************************************
def getresult(arg1):

	p = subprocess.Popen(arg1, stdout=subprocess.PIPE, shell=True,encoding="utf-8")
	(text, err) = p.communicate()
	res = text
	
	return res
	
#*****************************************************************************
# Function   : sendlog
# Description: Get log message then input to log file
# Inputs     : message: log message, color: defult white, file: log file name
# Outputs    : NA
# Notice     : NA
#*****************************************************************************
#def sendlog(message = "", color = 0, file = "/RACKLOG/t6g/RM_logs/monitor.log"):
def sendlog(message = "", color = 0, file = "log/monitor.log"):
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
	cmd = ("echo '{0} ====>> {1}' >>{2}".format(time.strftime("%m-%d-%y-%H:%M:%S"), message, file))
	
	os.system(cmd)
	
#*****************************************************************************
# Function   : show_info
# Description: show Monitor version history
# Inputs     : NA
# Outputs    : NA
# Notice     : V0.3 modify get_ip() function log message
#*****************************************************************************
def show_info():
	sendlog ("\n")
	sendlog ("\033[1;36;40m**********************************************************************\033[0m")
	sendlog ("\033[1;36;40m*\033[1;33;40m MSFT_Monitor_Reconfig_CP  -\033[0m  V0.2 2021/08/12 Release By Ed \033[1;36;40m*\033[0m")
	sendlog ("\033[1;36;40m*\033[1;33;40m MSFT_Monitor_Reconfig_CP  -\033[0m  V0.3 2021/08/30 Release By Ed \033[1;36;40m*\033[0m")
	sendlog ("\033[1;36;40m*\033[1;33;40m MSFT_Monitor_Reconfig_CP  -\033[0m  V0.4 2022/08/29 Release By David \033[1;36;40m*\033[0m")
	sendlog ("\033[1;36;40m*\033[1;33;40m MSFT_Monitor_Reconfig_CP  -\033[0m  V0.5 2022/10/07 Release By David \033[1;36;40m*\033[0m")
	sendlog ("\033[1;36;40m*\033[1;33;40m MSFT_Monitor_Reconfig_CP  -\033[0m  V0.6 2022/12/23 Release By David \033[1;36;40m*\033[0m")
	sendlog ("\033[1;36;40m*\033[1;33;40m MSFT_Monitor_Reconfig_CP  -\033[0m  V0.7 2022/12/24 Release By David \033[1;36;40m*\033[0m")
	sendlog ("\033[1;36;40m*\033[1;33;40m MSFT_Monitor_Reconfig_CP  -\033[0m  V0.8 2023/05/22 Release By David \033[1;36;40m*\033[0m")
	sendlog ("\033[1;36;40m*\033[1;33;40m MSFT_Monitor_Reconfig_CP  -\033[0m  V0.9 2023/06/06 Release By David \033[1;36;40m*\033[0m")
	sendlog ("\033[1;36;40m*\033[1;33;40m MSFT_Monitor_Reconfig_CP  -\033[0m  V0.10 2023/07/07 Release By David \033[1;36;40m*\033[0m")
	sendlog ("\033[1;36;40m*\033[1;33;40m MSFT_Monitor_Reconfig_CP  -\033[0m  V0.11 2023/07/14 Release By David \033[1;36;40m*\033[0m")
	sendlog ("\033[1;36;40m*\033[1;33;40m MSFT_Monitor_Reconfig_CP  -\033[0m  V0.12 2023/08/08 Release By An \033[1;36;40m*\033[0m")
	sendlog ("\033[1;36;40m*\033[1;33;40m MSFT_Monitor_Reconfig_CP  -\033[0m  V0.13 2023/08/16 Release By David \033[1;36;40m*\033[0m")
	sendlog ("\033[1;36;40m*\033[1;33;40m MSFT_Monitor_Reconfig_CP  -\033[0m  V0.14 2023/09/02 Release By David \033[1;36;40m*\033[0m")
	sendlog ("\033[1;36;40m*\033[1;33;40m MSFT_Monitor_Reconfig_CP  -\033[0m  V0.15 2024/03/28 Release By David \033[1;36;40m*\033[0m")
	sendlog ("\033[1;36;40m***********************************************************************\033[0m")
	sendlog ("\n")

#*****************************************************************************
# Function   : get_ip
# Description: change SF mac address format to dhcp.lease format, then search ip in dhcp.lease
# Inputs     : mac_addr: SF mac address format
# Outputs    : line: ip address
#            : 1: can not found ip in dhcp.lease
# Notice     : Make sure dhcp.lease location is correct
#*****************************************************************************
def get_ip(mac_addr):
	print ('mac address is : {}'.format(mac_addr))
	ip = "" 
	log = "get_rm_ip"
	mac_trans = (mac_addr[:2]+':'+mac_addr[2:4]+':'+mac_addr[4:6]+':'+mac_addr[6:8]+':'+mac_addr[8:10]+':'+mac_addr[10:12])
	mac_trans = mac_trans.lower()
	if build_side == "QTMC" or build_side == "QMF":
		search_ip_cmd = "grep -B7 -A1 {0} /var/lib/dhcpd/dhcpd.leases | grep lease".format(mac_trans)
		ip = getresult(search_ip_cmd)
		log = "get_ip MAC = {0}  IP ={1}".format(mac_trans,ip)
		if len(ip) >= 1 : 
			ip =  ip.strip().split("{")
			for line in ip:
				if line != "" :
					line = line.split(" ")[1]
					log = "get_ip MAC = {0} IP ={1}".format(mac_trans,line)
					# sendlog(log,"PASS")
					# log = "Check RM Connection IP ={}".format(line)
					cmd = "ping -c 3 {0}".format(line)
					if os.system(cmd) == 0:
						log = "get_ip MAC = {0} IP ={1}".format(mac_trans,line)
						sendlog(log,"PASS")
						return line
				else:
					break
		sendlog(log,"FAIL")
		return 1
	elif build_side == "QCI":
		#search_ip_cmd = "grep -B2 -A1 {0} /mnt/tftpboot/__DHCP/dhcp.txt | grep \"^192\" | awk -F \":\" '{{print $1}}'".format(mac_trans)
		search_ip_cmd = "grep -B2 -A1 {0} dhcp.txt | grep \"^192\" | awk -F \":\" '{{print $1}}'".format(mac_trans)
		ip = getresult(search_ip_cmd)
		ip = ip.split("\n")
		for i in range(len(ip)):
			tmp = ip[i].strip()
			if tmp == "":
				continue
			cmd = "ping -c 3 {0}".format(tmp)
			ret = os.system(cmd)
			if ret == 0:
				log = "get_ip MAC = {0} IP ={1}".format(mac_trans,tmp)
				sendlog(log,"PASS")
				return tmp
		log = "get_ip  MAC = {0} IP ={1}".format(mac_trans,ip)
		sendlog(log,"FAIL")
		return 1
	else:
		msg = "unknown build side"
		sendlog(msg,"FAIL")
		return 1

#*****************************************************************************
# Function   : get_mbsn_info_from_config
# Description: get all MBSN info from SF config files
# Inputs     : mbsn_info_list: an empty array for storing SN info
# Outputs    : 0: PASS
#            : 1: FAIL
# Notice     : NA
#*****************************************************************************
def get_mbsn_info_from_sf_folder(mbsn_info_list):
	if not os.path.isdir(g_sf_config_folder):
		msg = "{0} not found.".format(g_sf_config_folder)
		sendlog(msg, RED)
		return 1
	
	info = os.listdir(g_sf_config_folder)
	
	mbsn_list = []
	#get mbsn from file name
	for file_name in info:
		if ".txt" in file_name:
			file_path = "{0}/{1}".format(g_sf_config_folder, file_name)
			if os.path.isfile(file_path):
				mbsn = file_name.split('.')[0].split('_')[0].strip()
				mbsn_list.append(mbsn)
	mbsn_list = set(mbsn_list)
	for mbsn in mbsn_list:
		print ("mbsn = {0}".format(mbsn))
		MBSNdict = {
			"mbsn": "",
			"bmc_mac_addr": "",
			"bmc_ip": "",
			"nic_mac_addr": "",
			"nic_ip": "",
			"cp_mac_addr": "",
			"cp_ip": "",
			"is_reconfig": True,
			"CP_CERBERUS_FW": "",
			"CP_GOLDEN_IMAGE": "",
			"CP_FACTORY_IMAGE": "",
			"CP_SOC_OS_FW": "",
			"CP_SOC_FIP_FW": "",
			"CP_SOC_NITRO_FW": "",
			"CP_SOC_DRIVER": "",
			"CP_SN": "" # 20240328 David add CP SN
		}
		bmc_mac_addr = ""
		nic_mac_addr = ""
		model_name = ""
		cp_mac_addr = ""
		real_mbsn = ""
		cp_cerberus_fw = ""
		cp_golden_image = ""
		cp_soc_os_fw = ""
		cp_soc_fip_fw = ""
		cp_soc_nitro_fw = ""
		cp_sn = "" # 20240328 David add CP SN
		for file_name in info:
			if ".txt" in file_name and mbsn in file_name:
				print ("file_name = {0}".format(file_name))
				file_path = "{0}/{1}".format(g_sf_config_folder, file_name)
				f = open(file_path)
				for line in f:
					line = line.upper()
					#for link.ini
					if "BMC,MEMAC" in line:
						print ("line = {0}".format(line))
						bmc_mac_addr = line.split('=')[1].strip()
					#20220121 Marty : For T6G
					#if "MAC,MEMAC_100G_1_1" in line:
					if "MAC,MEMAC_100G_0_2" in line:
						print ("line = {0}".format(line))
						nic_mac_addr = line.split('=')[1].strip()
					#for UUTconfig2.ini
					if "BMCMAC" in line:
						print ("line = {0}".format(line))
						bmc_mac_addr = line.split('=')[1].strip()
					#20220121 Marty : For T6G
					if "ETH0" in line: # 20220829 David fix
					#if "ETH1" in line:
						print ("line = {0}".format(line))
						nic_mac_addr = line.split('=')[1].split(',')[0].strip()
					
					if "MODEL" in line: # 20221007 David add
						print ("line = {0}".format(line))
						model_name = line.split('=')[1].strip()

					if "ETH" in line and "MICROSOFT" in line: # 20221223 David add CP MAC
					#if "ETH1" in line:
						print ("line = {0}".format(line))
						cp_mac_addr = line.split('=')[1].split(',')[0].strip()
					
					if "MBSN" in line: #20221224 David add real MB SN
						print ("line = {0}".format(line))
						real_mbsn = line.split('=')[1].strip()
					if "CP_CERBERUS_FW" in line:
						print ("line = {0}".format(line.lower()))
						cp_cerberus_fw = line.lower().split('=')[1].strip()
					if "CP_GOLDEN_IMAGE" in line:
						print ("line = {0}".format(line.lower()))
						cp_golden_image = line.lower().split('=')[1].strip()
					if "CP_SOC_OS_FW" in line:
						print ("line = {0}".format(line.lower()))
						cp_soc_os_fw = line.lower().split('=')[1].strip()
					if "CP_SOC_FIP_FW" in line:
						print ("line = {0}".format(line.lower()))
						cp_soc_fip_fw = line.lower().split('=')[1].strip()
					if "CP_SOC_NITRO_FW" in line:
						print ("line = {0}".format(line.lower()))
						cp_soc_nitro_fw = line.lower().split('=')[1].strip()
					if "FPGA0" in line: # 20240328 David add CP SN
						print ("line = {0}".format(line.lower()))
						cp_sn = line.lower().split('=')[1].strip()

				f.close()
		#BSNdict["mbsn"] = mbsn
		MBSNdict["mbsn"] = real_mbsn
		MBSNdict["bmc_mac_addr"] = bmc_mac_addr
		MBSNdict["nic_mac_addr"] = nic_mac_addr
		MBSNdict["cp_mac_addr"] = cp_mac_addr
		MBSNdict["CP_CERBERUS_FW"] = cp_cerberus_fw
		MBSNdict["CP_GOLDEN_IMAGE"] = cp_golden_image
		MBSNdict["CP_SOC_OS_FW"] = cp_soc_os_fw
		MBSNdict["CP_SOC_FIP_FW"] = cp_soc_fip_fw
		MBSNdict["CP_SOC_NITRO_FW"] = cp_soc_nitro_fw
		MBSNdict["CP_SN"] = cp_sn # 20240328 David add CP SN


		if g_project not in model_name.lower(): # 20221007 David add: Skip other project
			print ("EXP: {}, GET: {}, skip.".format(g_project, model_name.lower()))
			continue
		
		#get bmc ip from DHCP
		# MBSNdict["bmc_ip"] = get_ip(MBSNdict["bmc_mac_addr"])
		# if MBSNdict["bmc_ip"] == "" or MBSNdict["bmc_ip"] == 1:# 20220829 David modify if BMC no resp then skip
		# 	continue
		MBSNdict["cp_ip"] = get_ip(MBSNdict["cp_mac_addr"])
		if MBSNdict["cp_ip"] == "" or MBSNdict["cp_ip"] == 1:# 20220829 David modify if BMC no resp then skip
			continue
		MBSNdict["nic_ip"] = get_ip(MBSNdict["nic_mac_addr"])
		# for i in range(3):
		# 	#get nic_ip from DHCP
		# 	MBSNdict["nic_ip"] = get_ip(MBSNdict["nic_mac_addr"])
		# 	if MBSNdict["nic_ip"] == "" or MBSNdict["nic_ip"] == 1:
		# 		time.sleep(10)
		# 	else:
		# 		break
		# MBSNdict["nic_ip"] = 1
		if MBSNdict["nic_ip"] == "" or MBSNdict["nic_ip"] == 1:
			MBSNdict["is_reconfig"] = False
		mbsn_info_list.append(MBSNdict)
	return 0

#*****************************************************************************
# Function   : chk_uut_power_state
# Description: check C2080 power ON/OFF/other.
# Inputs     : MBSNdict: dictionary of SN info
# Outputs    : 0: PASS
#            : 1: FAIL
# Notice     : 
#*****************************************************************************
def chk_uut_power_state(MBSNdict):
	sn_log_folder = "{0}/{1}".format(g_log_folder, MBSNdict["mbsn"])
	log_name = "{0}_chk_uut_power_state.log".format(MBSNdict["mbsn"])
	log_path = "{0}/{1}".format(sn_log_folder, log_name)
	
	try:
		os.makedirs(sn_log_folder)
		sendlog("make log folder ({0}) success".format(sn_log_folder), GREEN)
	except OSError as e:
		if e.errno == errno.EEXIST:
			sendlog("log folder ({0}) exist".format(sn_log_folder), GREEN)
		else:
			sendlog("{0}".format(e))
			return 1
	ret = getresult("ipmitool -H {0} -U {1} -P {2} -I lanplus power status".format(MBSNdict["bmc_ip"], g_bmc_username, g_bmc_password))
	sendlog(ret, 0, log_path)
	if ret.strip() == "Chassis Power is on":
		msg = "[mbsn:{0} bmc_ip: {1} bmc_mac: {2}] power on".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"])
		sendlog(msg)
		return 0
	else:
		msg = "[mbsn:{0} bmc_ip: {1} bmc_mac: {2}]] power not on".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"])
		sendlog(msg)
		return 1

#*****************************************************************************
# Function   : do_record_CP_golden_img_ver
# Description: record CP image version 
# Inputs     : MBSNdict: dictionary of SN info
# Outputs    : 0: PASS
#            : 1: FAIL
# Notice     : 
#*****************************************************************************
def do_record_CP_golden_img_ver(MBSNdict):
	sn_log_folder = "{0}/{1}".format(g_log_folder, MBSNdict["mbsn"])
	log_name = "{0}_do_record_CP_golden_image_version.log".format(MBSNdict["mbsn"])
	log_path = "{0}/{1}".format(sn_log_folder, log_name)
	#flag_log_name = "{0}_updated_flag.log".format(MBSNdict["mbsn"])
	#flag_log_path = "{0}/{1}".format(sn_log_folder, flag_log_name)
	
	try:
		os.makedirs(sn_log_folder)
		sendlog("make log folder ({0}) success".format(sn_log_folder), GREEN)
	except OSError as e:
		if e.errno == errno.EEXIST:
			sendlog("log folder ({0}) exist".format(sn_log_folder), GREEN)
		else:
			sendlog("{0}".format(e))
			return 1
	
	#login to CP
	try:
		s = pxssh.pxssh()
		msg = "[mbsn:{0} bmc_ip: {1} bmc_mac: {2}] login to CP".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"])
		sendlog(msg)
		s.login(MBSNdict["bmc_ip"], g_bmc_username, g_bmc_password, port=g_bmc_port_to_CP, auto_prompt_reset=False)
		s.sendline()
	except pxssh.ExceptionPxssh as e:
		sendlog("[mbsn:{0} bmc_ip: {1} bmc_mac: {2}] pxssh failed: login to CP".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"]), RED)
		sendlog(e, RED)
		sendlog(e, RED, log_path)
		return 1
	
	#get CP chip id
	try:
		s.sendline("modprobe catapult")
		s.prompt()
		s.sendline("fpgadiagnostics -list")
		s.prompt()
		sendlog(s.before, 0, log_path)
	except pxssh.ExceptionPxssh as e:
		sendlog("[mbsn:{0} bmc_ip: {1} bmc_mac: {2}] pxssh failed: can not get CP chip id".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"]), RED)
		sendlog(e, RED)
		return 1

	info = s.before.split("\n")
	CP_chip_id = ""
	for i in range(len(info)):
		if "Chip ID" in info[i]:
			line_next = info[i+1]
			CP_chip_id = line_next.split("  ")[1].strip()

	if CP_chip_id == "":
		sendlog ("[mbsn:{0} bmc_ip: {1} bmc_mac: {2}]: fail to get CP chip id".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"]), RED)
		print (info)
		return 1
	
	actions=[
		["set CP to golden image", "fpgadiagnostics -chip {0} -reconfigToFlashSlot 0".format(CP_chip_id)],
		["get CP golden image role id", "fpgadiagnostics -chip {0} -mgmt -justreadreg 101".format(CP_chip_id)],
		["get CP golden image version", "fpgadiagnostics -chip {0} -mgmt -justreadreg 65".format(CP_chip_id)],
		["get CP golden image build version", "fpgadiagnostics -chip {0} -mgmt -justreadreg 59".format(CP_chip_id)],
		["get CP golden shell package version", "fpgadiagnostics -chip {0} -dumpHealth".format(CP_chip_id)]
	]
	
	for action,cmd in actions:
		try:
			s.sendline(cmd)
		except pxssh.ExceptionPxssh as e:
			sendlog("[mbsn:{0} bmc_ip: {1} bmc_mac: {2}] pxssh failed: can not send cmd- {3}".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"], action), RED)
			sendlog(e, RED)
			return 1
	try:
		s.prompt()
		sendlog(s.before, 0, log_path)
	except pxssh.ExceptionPxssh as e:
		sendlog("[mbsn:{0} bmc_ip: {1} bmc_mac: {2}] pxssh failed: record CP message".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"]), RED)
		sendlog(e, RED)
		return 1
		
	golen_image_role_id = ""
	golden_image_version = ""
	golden_image_build_version = ""
	info = s.before.split("\n")
	for i in range(len(info)):
		if "Read register 101" in info[i]:
			golen_image_role_id = info[i].split(" ")[5].strip()
		if "Read register 65" in info[i]:
			golden_image_version = info[i].split(" ")[5].strip()
		if "Read register 59" in info[i]:
			golden_image_build_version = info[i].split(" ")[5].strip()
	
	msgs = [
		"[mbsn:{0} bmc_ip: {1} bmc_mac: {2}] golen_image_role_id = {3}".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"], golen_image_role_id),
		"[mbsn:{0} bmc_ip: {1} bmc_mac: {2}] golden_image_version = {3}".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"], golden_image_version),
		"[mbsn:{0} bmc_ip: {1} bmc_mac: {2}] golden_image_build_version = {3}".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"], golden_image_build_version)
	]
	for msg in msgs:
		sendlog(msg, 0, log_path)
		sendlog(msg)
	
	if golen_image_role_id == golden_image_version == golden_image_build_version == "":
		msg = "[mbsn:{0} bmc_ip: {1} bmc_mac: {2}] record golden image fail".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"])
		sendlog(msg)
		#s.logout()
		return 1
	msg = "[mbsn:{0} bmc_ip: {1} bmc_mac: {2}] record golden image finish, full porocess please see {3}".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"], log_path)
	sendlog(msg)
	#s.logout()
	
	#os.system("touch {0}".format(flag_log_path))
	
	return 0

#*****************************************************************************
# Function   : do_reconfig_CP
# Description: reconfig CP. Let NIC get IP address
# Inputs     : MBSNdict: dictionary of SN info
# Outputs    : 0: PASS
#            : 1: FAIL
# Notice     : Wait a direct way to get Soc image status
#*****************************************************************************
def do_reconfig_CP(MBSNdict):
	sn_log_folder = "{0}/{1}".format(g_log_folder, MBSNdict["mbsn"])
	log_name = "{0}_do_reconfig.log".format(MBSNdict["mbsn"])
	log_path = "{0}/{1}".format(sn_log_folder, log_name)

	sendlog ("[mbsn: {0}, bmc_ip: {1}] DBG1===============".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"]))	
	try:
		os.makedirs(sn_log_folder)
		sendlog("make log folder ({0}) success".format(sn_log_folder), GREEN)
	except OSError as e:
		if e.errno == errno.EEXIST:
			sendlog("log folder ({0}) exist".format(sn_log_folder), GREEN)
		else:
			sendlog("{0}".format(e))
			return 1
	
	#login to CP
	sendlog ("[mbsn: {0}, bmc_ip: {1}] DBG2===============".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"]))
	try:
		#import pdb;pdb.set_trace()
		s = pxssh.pxssh()
		s.force_password = True
		msg = "[mbsn:{0} bmc_ip: {1} bmc_mac: {2}] login to CP".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"])
		sendlog(msg)
		print("IP:{0},name:{1},pass:{2},port:{3}".format(MBSNdict["bmc_ip"], g_bmc_username, g_bmc_password, g_bmc_port_to_CP))
		ret = s.login(MBSNdict["bmc_ip"], "admin", "admin", port=g_bmc_port_to_CP, auto_prompt_reset=False)
		print("retrun val:{0}".format(ret))
		s.sendline()
		'''
		s.prompt()
		print("s.before:{0}".format(s.before))
		info = s.before.split('\n')
		for line in info:
			print("DEBUG line is :{0}".format(line))
			if "root@localhost" in line:
				break
			if "password" in line:
				print("password")
				#s.logout()
				break
		print("start to reconfigApp=============")
		s.sendline('fpgadiagnostics -reconfigApp')
		s.prompt()
		print("s.before:{0}".format(s.before))
		info = s.before.split('\n')
		for line in info:
			print("DEBUG line is :{0}".format(line))
		print "[mbsn:{0} bmc_ip: {1} bmc_mac: {2}] do CP reconfig".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"])
		sendlog(s.before, 0, log_path)
		'''
	except pxssh.ExceptionPxssh as e:
		sendlog("[mbsn:{0} bmc_ip: {1} bmc_mac: {2}] pxssh failed: login to CP".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"]), RED)
		sendlog(e, RED)
		sendlog(e, RED, log_path)
		#s.logout()
		return 1
	
	sendlog ("[mbsn: {0}, bmc_ip: {1}] DBG3===============".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"]))
	try:
		#s.sendline('modprobe catapult')
		#s.prompt()
		#print "[mbsn:{0} bmc_ip: {1} bmc_mac: {2}] load CP driver".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"])
		##sendlog(s.before, 0, log_path)
		sendlog ("[mbsn: {0}, bmc_ip: {1}] DBG4===============".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"]))
		s.sendline('modprobe catapult')
		s.prompt()
		s.sendline('fpgadiagnostics -reconfigApp')
		s.prompt()
		print ("[mbsn:{0} bmc_ip: {1} bmc_mac: {2}] do CP reconfig".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"]))
		sendlog(s.before, 0, log_path)
	except pxssh.ExceptionPxssh as e:
		sendlog("[mbsn:{0} bmc_ip: {1} bmc_mac: {2}]pxssh failed: reconfig Celestial Peak.".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"]), RED)
		sendlog(e, RED)
		return 1
	
	#s.logout()
	return 0
	
def is_CP_Golden_mode(MBSNdict):
	ret = -1
	# try:
	# 	s = pxssh.pxssh()
	# 	s.force_password = True
	# 	#print "login... IP = {0}, user = {1}, password = {2}".format(MBSNdict["bmc_ip"], g_bmc_username, g_bmc_password)
	# 	s.login(MBSNdict["bmc_ip"], g_bmc_username, g_bmc_password, port=g_bmc_port_to_CP, auto_prompt_reset=False)
	# 	print "[mbsn:{0} bmc_ip: {1} bmc_mac: {2}] login".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"])
	# 	s.sendline()

	# 	#print "install catapult driver"
	# 	s.sendline('modprobe catapult')
	# 	print "[mbsn:{0} bmc_ip: {1} bmc_mac: {2}] load CP driver".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"])
	# 	#print "dumpHealth"
	# 	s.sendline('fpgadiagnostics -dumpHealth')
	# 	print "[mbsn:{0} bmc_ip: {1} bmc_mac: {2}] dumpHealth".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"])
	# 	s.prompt()
	# except pxssh.ExceptionPxssh, e:
	# 	print str(e)
	# 	sendlog("[mbsn:{0} bmc_ip: {1} bmc_mac: {2}]pxssh failed: is_CP_Golden_mode().".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"]), RED)
	# 	sendlog(e, RED)
	# 	#s.logout()
	# 	return -1
	
	print ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] load CP driver".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]))
	cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/sbin/modprobe catapult\"".format(MBSNdict["cp_ip"])
	# Changed ssh to null user
	getresult(cmd)

	print ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] dumpHealth".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]))
	cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/fpgadiagnostics -dumphealth\"".format(MBSNdict["cp_ip"])
		# Changed ssh to null user
	result = getresult(cmd)
	info = result.split('\n')

	# info = s.before.split('\n')
	for line in info:
		if "[FPGA-CONFIG    ]" in line:
			golden_str = line.split()[3].split(',')[0].strip()
			status = golden_str.split(':')[1]
			if status == "0":
				sendlog("[mbsn:{0} cp_ip: {1} cp_mac: {2}]: App mode".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), GREEN)
				ret = 1
				return ret
			else:
				sendlog("[mbsn:{0} cp_ip: {1} cp_mac: {2}]: Golden mode".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), GREEN)
				#ret = 0
	if "[FPGA-CONFIG    ]" not in result:
		return ret
	
	##1220
	sn_log_folder = "{0}/{1}".format(g_log_folder, MBSNdict["mbsn"])
	log_name = "{0}_do_reconfig.log".format(MBSNdict["mbsn"])
	log_path = "{0}/{1}".format(sn_log_folder, log_name)
	record_log_name = "{0}_do_record_CP_golden_image_version.log".format(MBSNdict["mbsn"])
	record_log_path = "{0}/{1}".format(sn_log_folder, record_log_name)
	if not os.path.isfile(record_log_path):
		print ("{0}_do_record_CP_golden_image_version is not exist".format(MBSNdict["mbsn"]))
		###do_record_CP_golden_img_ver
		try:
			os.makedirs(sn_log_folder)
			sendlog("make log folder ({0}) success".format(sn_log_folder), GREEN)
		except OSError as e:
			if e.errno == errno.EEXIST:
				sendlog("log folder ({0}) exist".format(sn_log_folder), GREEN)
			else:
				sendlog("{0}".format(e))
				return 3
		
		#get CP chip id
		# try:
		# 	s.sendline("modprobe catapult")
		# 	s.prompt()
		# 	s.sendline("fpgadiagnostics -list")
		# 	s.prompt()
		# 	sendlog(s.before, 0, record_log_path)
		# except pxssh.ExceptionPxssh, e:
		# 	sendlog("[mbsn:{0} bmc_ip: {1} bmc_mac: {2}] pxssh failed: can not get CP chip id".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"]), RED)
		# 	sendlog(e, RED)
		# 	return 3

		cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/sbin/modprobe catapult\"".format(MBSNdict["cp_ip"])
			# Changed ssh to null user
		getresult(cmd)

		cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/fpgadiagnostics -list\"".format(MBSNdict["cp_ip"])
			# Changed ssh to null user
		result = getresult(cmd)
		sendlog(result, 0, record_log_path)
		info = result.split('\n')

		# info = s.before.split("\n")
		CP_chip_id = ""
		for i in range(len(info)):
			if "Chip ID" in info[i]:
				line_next = info[i+1]
				CP_chip_id = line_next.split("  ")[1].strip()

		if CP_chip_id == "":
			sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}]: fail to get CP chip id".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), RED)
			print (info)
			return 3
		
		actions=[
			# ["set CP to golden image", "fpgadiagnostics -chip {0} -reconfigToFlashSlot 0".format(CP_chip_id)],
			["get CP golden image role id", "fpgadiagnostics -chip {0} -mgmt -justreadreg 101".format(CP_chip_id)],
			["get CP golden image version", "fpgadiagnostics -chip {0} -mgmt -justreadreg 65".format(CP_chip_id)],
			["get CP golden image build version", "fpgadiagnostics -chip {0} -mgmt -justreadreg 59".format(CP_chip_id)],
			["get CP golden shell package version", "fpgadiagnostics -chip {0} -dumpHealth".format(CP_chip_id)]
		]
		
		# for action,cmd in actions:
		# 	try:
		# 		s.sendline(cmd)
		# 	except pxssh.ExceptionPxssh, e:
		# 		sendlog("[mbsn:{0} cp_ip: {1} cp_mac: {2}] pxssh failed: can not send cmd- {3}".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"], action), RED)
		# 		sendlog(e, RED)
		# 		return 3
		# try:
		# 	s.prompt()
		# 	sendlog(s.before, 0, record_log_path)
		# except pxssh.ExceptionPxssh, e:
		# 	sendlog("[mbsn:{0} cp_ip: {1} cp_mac: {2}] pxssh failed: record CP message".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), RED)
		# 	sendlog(e, RED)
		# 	return 3


			
		golen_image_role_id = ""
		golden_image_version = ""
		golden_image_build_version = ""

		for action,cmd in actions:
			ccmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{0} \"echo overlake | sudo -S /usr/bin/{1}\"".format(MBSNdict["cp_ip"], cmd)
				# Changed ssh to null user
			result = getresult(ccmd)
			sendlog("\n"+result, 0, record_log_path)
			info = result.split('\n')

			# info = s.before.split("\n")
			for i in range(len(info)):
				if "Read register 101" in info[i]:
					golen_image_role_id = info[i].split(" ")[5].strip()
				if "Read register 65" in info[i]:
					golden_image_version = info[i].split(" ")[5].strip()
				if "Read register 59" in info[i]:
					golden_image_build_version = info[i].split(" ")[5].strip()
		
		msgs = [
			"[mbsn:{0} cp_ip: {1} cp_mac: {2}] golen_image_role_id = {3}".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"], golen_image_role_id),
			"[mbsn:{0} cp_ip: {1} cp_mac: {2}] golden_image_version = {3}".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"], golden_image_version),
			"[mbsn:{0} cp_ip: {1} cp_mac: {2}] golden_image_build_version = {3}".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"], golden_image_build_version)
		]
		for msg in msgs:
			sendlog(msg, 0, record_log_path)
			sendlog(msg)
		
		if golen_image_role_id == golden_image_version == golden_image_build_version == "":
			msg = "[mbsn:{0} cp_ip: {1} cp_mac: {2}] record golden image fail".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"])
			sendlog(msg)
			#s.logout()
			return 3
		msg = "[mbsn:{0} cp_ip: {1} cp_mac: {2}] record golden image finish, full porocess please see {3}".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"], log_path)
		sendlog(msg)
		
		
		
		
	else:
		print ("{0}_do_record_CP_golden_image_version exist".format(MBSNdict["mbsn"]))

	# try:
	# 	s.sendline('fpgadiagnostics -reconfigApp')
	# 	s.prompt()
	# 	print "[mbsn:{0} bmc_ip: {1} bmc_mac: {2}] do CP reconfig".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"])
	# 	sendlog(s.before, 0, log_path)
	# 	return 1
	# except pxssh.ExceptionPxssh, e:
	# 	sendlog("[mbsn:{0} bmc_ip: {1} bmc_mac: {2}]pxssh failed: reconfig Celestial Peak.".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"]), RED)
	# 	sendlog(e, RED)
	# 	return 2
	
	print ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] do CP reconfig".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]))
	cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/fpgadiagnostics -reconfigApp\"".format(MBSNdict["cp_ip"])
		# Changed ssh to null user
	result = getresult(cmd)

	# sendlog(s.before, 0, log_path)
	sendlog(result, 0, log_path)
	return 1

	#s.logout()
	return ret

#*****************************************************************************
# Function	 : chk_soc_fw
# Description: Login CP by RM, and get SoC firmware/Nitro firmware version
#			 : and check these version are as expected or not
# Inputs	 : sn_info_list: SN list information
# Outputs	 : 0: PASS
#			 : 1: FAIL
#			 : 2: it means it need to update SoC firmware version
# Notice	 : NA
#*****************************************************************************
def chk_soc_fw(MBSNdict):
	sn_log_folder = "{0}/{1}".format(g_log_folder, MBSNdict["mbsn"])
	log_name = "{0}_chk_soc_fw.log".format(MBSNdict["mbsn"])
	log_path = "{0}/{1}".format(sn_log_folder, log_name)
	
	try:
		os.makedirs(sn_log_folder)
		sendlog("make log folder ({0}) success".format(sn_log_folder), GREEN)
	except OSError as e:
		if e.errno == errno.EEXIST:
			sendlog("log folder ({0}) exist".format(sn_log_folder), GREEN)
		else:
			sendlog("{0}".format(e))
			return 1	

	g_cmd_get_soc_os_ver = "cat /etc/os-release | grep 'VERSION_ID'"
	#Get SoC OS version
	try: #20230902 David add try expect to prevent cannot get fw ver
		print ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Get SoC OS version".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]))
		cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"{}\"".format(MBSNdict["cp_ip"], g_cmd_get_soc_os_ver)
		# Changed ssh to null user
		result = getresult(cmd).split('\x00')[0]
		sendlog(result, 0, log_path)
		if result == "":
			sendlog("Can't get SoC OS version !")
			return 1
		else:
			get_soc_os_ver = result.split('=')[1].replace('"','').strip()
			print("get_soc_os_ver = {0}".format(get_soc_os_ver))
	except:
		get_soc_os_ver = ""
	
	#Get SoC firmware version
	try: #20230902 David add try expect to prevent cannot get fw ver
		print ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Get SoC firmware version".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]))
		cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"{}\"".format(MBSNdict["cp_ip"], g_cmd_get_soc_firmware_ver)
		# Changed ssh to null user
		result = getresult(cmd).split('\x00')[0]
		sendlog(result, 0, log_path)
		if result == "":
			sendlog("Can't get SoC firmware version !")
			return 1
		else:
			get_soc_fw_ver = result
			print("get_soc_fw_ver = {0}".format(get_soc_fw_ver))
	except:
		get_soc_fw_ver = ""

	#Get SoC cerberus firmware version
	try: #20230902 David add try expect to prevent cannot get fw ver
		print ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Get SoC cerberus firmware version".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]))
		cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/{} | grep 'Cerberus Version'\"".format(MBSNdict["cp_ip"], g_cmd_get_soc_cerberus_firmware_ver)
		# Changed ssh to null user
		result = getresult(cmd).split('\x00')[0]
		sendlog(result, 0, log_path)
		if result == "":
			sendlog("Can't get SoC cerberus firmware version !")
			return 1
		else:
			get_soc_cerberus_fw_ver = result.split(':')[1].strip()
			print("get_soc_cerberus_fw_ver = {0}".format(get_soc_cerberus_fw_ver))
	except:
		get_soc_cerberus_fw_ver = ""
	
	#Get SoC Nitro firmware version
	try: #20230902 David add try expect to prevent cannot get fw ver
		print ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Get SoC Nitro firmware version".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]))
		cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"{}\"".format(MBSNdict["cp_ip"], g_cmd_get_soc_nitro_firmware_ver)
		# Changed ssh to null user
		result = getresult(cmd).split('\x00')[0]
		sendlog(result, 0, log_path)
		if result == "":
			sendlog("Can't get SoC Nitro firmware version !")
			return 1
		else:
			get_soc_fw_nitro_ver = result
			print("get_soc_fw_nitro_ver = {0}".format(get_soc_fw_nitro_ver))
	except:
		get_soc_fw_nitro_ver = ""
	
	#Judge SoC firmware/Nitro firmware version are as expected or not
	if MBSNdict["CP_SOC_FIP_FW"] != get_soc_fw_ver:
		sendlog("SoC firmware version check FAIL ! exp:{0}, get:{1}".format(MBSNdict["CP_SOC_FIP_FW"], get_soc_fw_ver), RED)
		return 2
	else:
		sendlog("SoC firmware version check PASS ! exp:{0}, get:{1}".format(MBSNdict["CP_SOC_FIP_FW"], get_soc_fw_ver), GREEN)
		if MBSNdict["CP_SOC_NITRO_FW"] != get_soc_fw_nitro_ver:
			sendlog("SoC firmware Nitro version check FAIL ! exp:{0}, get:{1}".format(MBSNdict["CP_SOC_NITRO_FW"], get_soc_fw_nitro_ver), RED)
			return 2
		else:
			sendlog("SoC firmware Nitro version check PASS ! exp:{0}, get:{1}".format(MBSNdict["CP_SOC_NITRO_FW"], get_soc_fw_nitro_ver), GREEN)
		if MBSNdict["CP_CERBERUS_FW"] != get_soc_cerberus_fw_ver:
			sendlog("SoC cerberus firmware version check FAIL ! exp:{0}, get:{1}".format(MBSNdict["CP_CERBERUS_FW"], get_soc_cerberus_fw_ver), RED)
			return 2
		else:
			sendlog("SoC cerberus firmware version check PASS ! exp:{0}, get:{1}".format(MBSNdict["CP_CERBERUS_FW"], get_soc_cerberus_fw_ver), GREEN)
		
		if MBSNdict["CP_SOC_OS_FW"] != get_soc_os_ver:
			sendlog("SoC OS version check FAIL ! exp:{0}, get:{1}".format(MBSNdict["CP_SOC_OS_FW"], get_soc_os_ver), RED)
			return 2
		else:
			sendlog("SoC OS version check PASS ! exp:{0}, get:{1}".format(MBSNdict["CP_SOC_OS_FW"], get_soc_os_ver), GREEN)
	return 0

#*****************************************************************************
# Function	 : update_soc_fw
# Description: follow updating SoC firmware version SOP to update
# Inputs	 : sn_info_list: SN list information
# Outputs	 : 0: PASS
#			 : 1: FAIL
# Notice	 : NA
#*****************************************************************************
def update_soc_fw(MBSNdict):
	sn_log_folder = "{0}/{1}".format(g_log_folder, MBSNdict["mbsn"])
	log_name = "{0}_update_soc_fw.log".format(MBSNdict["mbsn"])
	log_path = "{0}/{1}".format(sn_log_folder, log_name)
	image_path = "/tftpboot/{}".format(g_os_path)
	try:
		os.makedirs(sn_log_folder)
		sendlog("make log folder ({0}) success".format(sn_log_folder), GREEN)
	except OSError as e:
		if e.errno == errno.EEXIST:
			sendlog("log folder ({0}) exist".format(sn_log_folder), GREEN)
		else:
			sendlog("{0}".format(e))
			return 1
	
	if build_side == 'QCI':
		print ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Check CP image on TFTP".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]))
		cmd = "sshpass -p '{0}' ssh -o 'StrictHostKeyChecking no' {1}@{2} 'ls {3}'".format(g_tftp_passwd, g_tftp_user, g_tftp_ip, image_path)
		result = getresult(cmd).split('\n')
		sendlog(result, 0, log_path)	
		if image_path not in result:
			sendlog("MBSN:{1} no overlake image on PXE server~~~~~~~~~".format(MBSNdict["mbsn"]))
			return 1
	else:
		if not os.path.isfile(image_path):
			sendlog("MBSN:{1} no overlake image on PXE server~~~~~~~~~".format(MBSNdict["mbsn"]))
			return 1	

	# label T6G rsa image
	# 	kernel firmware/T6G/stos/Image_rsa.img
	
	cp_mac = MBSNdict["cp_mac_addr"].lower()
	if build_side == 'QCI':
		image_mac_file = "/tmp/01-{0}-{1}-{2}-{3}-{4}-{5}".format(cp_mac[0:2], cp_mac[2:4], cp_mac[4:6], cp_mac[6:8], cp_mac[8:10], cp_mac[10:12])
		os.system("echo 'label T6G rsa image' > {}".format(image_mac_file))
		os.system("echo 'kernel {}' >> {}".format(g_os_path, image_mac_file))

		if not os.path.isfile(image_mac_file):
			sendlog("MBSN:{1} no CP grub on PXE server~~~~~~~~~".format(MBSNdict["mbsn"]))
			return 1	
		print ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] copy CP grub to TFTP".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]))
		cmd = "sshpass -p '{0}' scp -o 'StrictHostKeyChecking no' {1} {2}@{3}:{4}/".format(g_tftp_passwd, image_mac_file, g_tftp_user, g_tftp_ip, g_PXE_grub_folder)		
		result = getresult(cmd).split('\n')
		sendlog(result, 0, log_path)
		
		print ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Check CP grub on TFTP".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]))
		cmd = "sshpass -p '{0}' ssh -o 'StrictHostKeyChecking no' {1}@{2} 'ls {3} | grep {4}'".format(g_tftp_passwd, g_tftp_user, g_tftp_ip, g_PXE_grub_folder, image_mac_file.split('/')[-1].strip())
		print(cmd)
		result = getresult(cmd).split('\n')
		sendlog(result, 0, log_path)	
		if result == "":
			sendlog("copy CP grub to TFTP fail !")
			return 1
	else:
		image_mac_file = "{6}/01-{0}-{1}-{2}-{3}-{4}-{5}".format(cp_mac[0:2], cp_mac[2:4], cp_mac[4:6], cp_mac[6:8], cp_mac[8:10], cp_mac[10:12], g_PXE_grub_folder)
		os.system("echo 'label T6G rsa image' > {}".format(image_mac_file))
		os.system("echo 'kernel {}' >> {}".format(g_os_path, image_mac_file))

		if not os.path.isfile(image_mac_file):
			sendlog("MBSN:{1} no CP grub on PXE server~~~~~~~~~".format(MBSNdict["mbsn"]))
			return 1	
	

	#Set bootmode to 2 (PXE)
	print ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Set bootmode to 2".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]))
	cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/{}\"".format(MBSNdict["cp_ip"], g_cmd_set_bootmode_to_two)
	result = getresult(cmd).split('\n')
	sendlog(result, 0, log_path)
	
	if result != "":
		if "boot mode is set to 0x02 through cerberus" in result:
			sendlog("Set boot mode to 2 success !")
		else:
			sendlog("Set boot mode to 2 fail !")
			return 1
	else:
		sendlog("Can't get result - set boot mode to 2")
		return 1
	
	#Reboot the SoC
	print ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Reboot CP".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]))
	cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/sbin/{}\"".format(MBSNdict["cp_ip"], g_cmd_reboot)
	result = getresult(cmd).split('\n')
	sendlog(result, 0, log_path)	
	if result == "":
		return 1
	
	time.sleep(60)
	# print("rm -rf /root/.ssh/known_hosts...")
	# os.system("rm -rf /root/.ssh/known_hosts")

	print ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] CP status check".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]))
	cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"cat /etc/os-release\"".format(MBSNdict["cp_ip"])
	result = getresult(cmd)
	sendlog(result, 0, log_path)
	
	if result !="":
		#print "DBG:{0}".format(res)
		if "ID=\"msft\"" in result.split("\n"):
			sendlog("Reboot SOC success !") 
		else:
			time.sleep(10)
			print ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] CP status check".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]))
			cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"cat /etc/os-release\"".format(MBSNdict["cp_ip"])
			result = getresult(cmd).split('\n')
			sendlog(result, 0, log_path)
			
			if result !="":
				if len([word for word in result if 'VERSION=' in word]):
					sendlog("After Wait 10 second! Reboot SOC Success!")
				else:
					sendlog("After Wait 10 second! Reboot SOC fail!")
					return 1
			else:
				sendlog("Can't get result - After reboot SOC!!")
				return 1
	else:
		sendlog("Can't get result - After reboot SOC!!")
		return 1

	#Execute "socflash" command
	print ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] socflash".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]))
	cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/sbin/{}\"".format(MBSNdict["cp_ip"], g_cmd_emmcflash)
	result = getresult(cmd).split('\n')
	sendlog(result, 0, log_path)	
	if result == "":
		return 1
	sendlog("Execute socflash command success!!!")
	
	#Create /tmp/usb folder
	print ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Create /tmp/usb folder".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]))
	cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/{}\"".format(MBSNdict["cp_ip"], g_cmd_mkdir_usb_folder)
		# Changed ssh to null user
	result = getresult(cmd).split('\n')
	sendlog(result, 0, log_path)	
	if result == "":
		return 1
	sendlog("Create /tmp/usb folder success!!")
	
	if build_side == 'QCI':
		print ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Get CP overlake image on TFTP".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]))
		cmd = "sshpass -p '{0}' scp -o 'StrictHostKeyChecking no' {1}@{2}:{3}/{4} /tmp/".format(g_tftp_passwd, g_tftp_user, g_tftp_ip, g_overlake_image_path,upgrade_image)		
		result = getresult(cmd).split('\n')
		sendlog(result, 0, log_path)

		cmd = "ls /tmp/"
		result = getresult(cmd)
		sendlog(result, 0, log_path)
		if upgrade_image not in result:
			sendlog("Can't get overlake_image!!")
			return 1
				
		#Copy image from TFTP to CP SoC
		print ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Copy image from TFTP to CP SoC".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]))
		cmd = "sshpass -p overlake scp -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null /tmp/{0} stuser@{1}:/tmp/".format(upgrade_image, MBSNdict["cp_ip"])	
		result = getresult(cmd).split('\n')
		sendlog(result, 0, log_path)
	else:
		#Copy image from TFTP to CP SoC
		print ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Copy image from TFTP to CP SoC".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]))
		cmd = "sshpass -p overlake scp -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null {0}/{1} stuser@{2}:/tmp/".format(g_overlake_image_path,upgrade_image, MBSNdict["cp_ip"])	
		result = getresult(cmd).split('\n')
		sendlog(result, 0, log_path)
	
	g_cmd_losetup_image = "losetup -f -P /tmp/{}".format(upgrade_image)
	#Execute "losetup_image" command
	print ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] losetup_image".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]))
	cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/sbin/{}\"".format(MBSNdict["cp_ip"], g_cmd_losetup_image)
		# Changed ssh to null user
	result = getresult(cmd).split('\n')
	sendlog(result, 0, log_path)	
	if result == "":
		return 1
	sendlog("Execute losetup command success!!!")

	g_cmd_check_loop2_exist = "lsblk"
	#Check "loop2" drive losetup
	print ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Check loop2 drive losetup".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]))
	cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/{}\"".format(MBSNdict["cp_ip"], g_cmd_check_loop2_exist)
		# Changed ssh to null user
	result = getresult(cmd)
	sendlog(result, 0, log_path)	
	if result != "":
		if "loop2p1" in result:
			sendlog("Check 'loop2p1' drive losetup success !")
		else:
			sendlog("Check 'loop2p1' drive losetup fail !")
			return 1
	else:
		sendlog("Can't get result - check 'loop2' drive losetup")
		return 1

	g_cmd_mount_usb_loop2p1_folder = "mount /dev/loop2p1 /tmp/usb/"
	#Mount /tmp/usb to /dev/loop2p1
	print ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Mount /tmp/usb to /dev/loop2p1".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]))
	cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/{}\"".format(MBSNdict["cp_ip"], g_cmd_mount_usb_loop2p1_folder)
		# Changed ssh to null user
	result = getresult(cmd).split('\n')
	sendlog(result, 0, log_path)	
	if result == "":
		return 1
	sendlog("Mount /tmp/usb to /dev/loop2p1 success!!")

	#Check bin files exist or not
	print ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Check bin files exist or not".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]))
	cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/{}\"".format(MBSNdict["cp_ip"], g_cmd_check_bin_file_exist)
		# Changed ssh to null user
	result = getresult(cmd)
	sendlog(result, 0, log_path)	
	if result != "":
		if fip_fw_file and nitro_fw_file in result:
			sendlog("Check bin files success !")
		else:
			sendlog("Check bin files fail !")
			return 1
	else:
		sendlog("Can't get result - check bin files")
		return 1
		
	#do update FW
	for cmd in g_cmd_update_sop:
		print ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] CP SoC FW update: {3}".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"], cmd))
		cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/{}\"".format(MBSNdict["cp_ip"], cmd)
			# Changed ssh to null user
		result = getresult(cmd)
		sendlog(result, 0, log_path)	
		if result == "":
			sendlog("Can't get cmd result: {0}".format(cmd))
			return 1
		elif "Cerberus command completed successfully" in result:
			sendlog("Use update command success.")
		else:
			sendlog("Use update command fail: {0}".format(cmd))
			return 1
	
	# 20240328 David modify use SF info
	g_cp_Cerberus_fw="cerberus_v{}.bin".format(MBSNdict["CP_CERBERUS_FW"])
	g_cp_Cerberus_fw_loc="/project/firmware/{}/cp/{}".format(g_project,g_cp_Cerberus_fw)
	if build_side == "QCI":
		os.system("mkdir -p /project/firmware/{}/cp/".format(g_project))
		print ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Copy cp Cerberus FW file to server".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]))
		cmd = "cp -rf /mnt/smbfs/firmware/{}/cp/{} {}".format(g_project, g_cp_Cerberus_fw, g_cp_Cerberus_fw_loc)
		result = getresult(cmd)
		sendlog(result, 0, log_path)
		info = result.split('\n')
	#Copy Cerberus FW from TFTP to CP SoC
	print ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Copy Cerberus FW from TFTP to CP SoC".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]))
	cmd = "sshpass -p overlake scp -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null {0} stuser@{1}:/tmp/".format(g_cp_Cerberus_fw_loc, MBSNdict["cp_ip"])	
	result = getresult(cmd).split('\n')
	sendlog(result, 0, log_path)
	
	#do Cerberus FW update
	print ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Update CP Cerberus FW".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]))
	cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/cerberus_utility fwupdate /tmp/{}\"".format(MBSNdict["cp_ip"], g_cp_Cerberus_fw)
		# Changed ssh to null user
	result = getresult(cmd)
	sendlog(result.split('\n'), 0, log_path)
	if result == "":
		sendlog("Can't get cmd result: {0}".format(cmd))
		return 1
	elif "Cerberus command completed successfully" in result:
		sendlog("Use update command success.")
	else:
		sendlog("Use update command fail: {0}".format(cmd))
		return 1


	#Set bootmode to 0
	print ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Set bootmode to 0".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]))
	cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/{}\"".format(MBSNdict["cp_ip"], g_cmd_set_bootmode_to_zero)
		# Changed ssh to null user
	result = getresult(cmd).split('\n')
	sendlog(result, 0, log_path)
		
	if result != "":
		if "boot mode is set to 0x00 through cerberus" in result:
			sendlog("Set boot mode to 0 success !")
		else:
			sendlog("Set boot mode to 0 fail !")
			return 1
	else:
		sendlog("Can't get result - set boot mode to 0")
		return 1
		
	#Reset SoC
	print ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Reset SoC".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]))
	cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/{}\" &".format(MBSNdict["cp_ip"], g_cmd_reset_soc)
		# Changed ssh to null user
	# result = getresult(cmd).split('\n')	
	# sendlog(result, 0, log_path)
	os.system(cmd)

	time.sleep(10)	
	print ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Kill socreset process".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]))
	cmd = "ps -ax|grep -v 'grep' |grep 'stuser@{}' | awk '{{print $1}}'".format(MBSNdict["cp_ip"])
	result = getresult(cmd).split('\n')
	sendlog(result, 0, log_path)
	if result != "":
		os.system("kill {}".format(str(result[0])))
	'''
	if os.path.isfile(image_mac_file):
		sendlog("MBSN:{} Remove CP grub on PXE server~~~~~~~~~".format(MBSNdict["mbsn"]))
		os.system("rm -rf {}".format(image_mac_file))	
	'''
	time.sleep(60)	
	# print("rm -rf /root/.ssh/known_hosts...")
	# os.system("rm -rf /root/.ssh/known_hosts")

	return 0

#*****************************************************************************
# Function	 : chk_fpga_fw
# Description: Login CP by RM, and get CP FPGA firmware version
#			 : and check these version are as expected or not
# Inputs	 : sn_info_list: SN list information
# Outputs	 : 0: PASS
#			 : 1: FAIL
#			 : 2: it means it need to update SoC firmware version
# Notice	 : NA
#*****************************************************************************
def chk_fpga_fw(MBSNdict):
	sn_log_folder = "{0}/{1}".format(g_log_folder, MBSNdict["mbsn"])
	log_name = "{0}_chk_fpga_fw.log".format(MBSNdict["mbsn"])
	log_path = "{0}/{1}".format(sn_log_folder, log_name)
	ver = ""
	role = ""
	
	try:
		os.makedirs(sn_log_folder)
		sendlog("make log folder ({0}) success".format(sn_log_folder), GREEN)
	except OSError as e:
		if e.errno == errno.EEXIST:
			sendlog("log folder ({0}) exist".format(sn_log_folder), GREEN)
		else:
			sendlog("{0}".format(e))
			return 1
	
	print ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] load CP driver".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]))
	cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/sbin/modprobe catapult\"".format(MBSNdict["cp_ip"])
		# Changed ssh to null user
	getresult(cmd)

	print ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Change FPGA slot to Golden".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]))
	cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/fpgadiagnostics -reconfiggolden\"".format(MBSNdict["cp_ip"])
		# Changed ssh to null user
	result = getresult(cmd)
	sendlog(result, 0, log_path)
	info = result.split('\n')
		
	time.sleep(30)
	
	print ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] dumpHealth".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]))
	cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/fpgadiagnostics -dumphealth\"".format(MBSNdict["cp_ip"])
		# Changed ssh to null user
	result = getresult(cmd)
	sendlog(result, 0, log_path)
	info = result.split('\n')

	for line in info:
		if "[FPGA-CONFIG-EX ] OK" in line:
			ver = line.split()[6].split(',')[1].split('-')[0].strip()
			role = line.split()[7].split(',')[0].split('role:')[1]

	#Check FPGA version
	if ver == "" or role == "":
		sendlog("Can't get FPGA firmware version !")
		return 1
	else:
		get_fpga_fw_ver = ver+','+role
		print("GOLDEN:get_fpga_fw_ver = {0}".format(get_fpga_fw_ver))
		if MBSNdict["CP_GOLDEN_IMAGE"] != get_fpga_fw_ver:
			return 2	
	
	return 0

#*****************************************************************************
# Function	 : update_fpga_fw
# Description: follow updating FPGA firmware version SOP to update
# Inputs	 : sn_info_list: SN list information
# Outputs	 : 0: PASS
#			 : 1: FAIL
# Notice	 : NA
#*****************************************************************************
def update_fpga_fw(MBSNdict):	  
	sn_log_folder = "{0}/{1}".format(g_log_folder, MBSNdict["mbsn"])
	log_name = "{0}_update_fpga_fw.log".format(MBSNdict["mbsn"])
	log_path = "{0}/{1}".format(sn_log_folder, log_name)
	CP_IP=""
	
	try:
		os.makedirs(sn_log_folder)
		sendlog("make log folder ({0}) success".format(sn_log_folder), GREEN)
	except OSError as e:
		if e.errno == errno.EEXIST:
			sendlog("log folder ({0}) exist".format(sn_log_folder), GREEN)
		else:
			sendlog("{0}".format(e))
			return 1	
	
	#Find CP SOC IP
	print ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] dumpHealth".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]))
	cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/fpgadiagnostics -dumphealth\"".format(MBSNdict["cp_ip"])
		# Changed ssh to null user
	result = getresult(cmd)
	sendlog(result, 0, log_path)
	info = result.split('\n')
	
			
	#Copy image to CP SOC
	if build_side == "QCI":
		os.system("mkdir -p /project/firmware/{}/cp/".format(g_project))
		print ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Copy cp image file to server".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]))
		cmd = "cp -rf /mnt/smbfs/firmware/{}/cp/{} {}".format(g_project, g_cp_FPGA_firmware_loc.split('/')[-1], g_cp_FPGA_firmware_loc)
		result = getresult(cmd)
		sendlog(result, 0, log_path)
		info = result.split('\n')
	result_str="Another instance of"
	while "Another instance of" in  result_str:
		cmdstr = "sshpass -p 'overlake' scp -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null {0} stuser@[{1}]:{2}".format(g_cp_FPGA_firmware_loc, MBSNdict["cp_ip"], "/tmp/")
		result = getresult(cmdstr)
		print ("result:{0}".format(result))
		result_str = result
		time.sleep(1)
	print("Copy {0} to CP {1}".format(g_cp_FPGA_firmware_loc,"/tmp/"))

	#update FPGA image
	print ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Update FPGA image".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]))
	cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/{}\"".format(MBSNdict["cp_ip"], g_cmd_update_fpga.format("/tmp/"+g_cp_FPGA_firmware))
		# Changed ssh to null user
	result = getresult(cmd)
	sendlog(result, 0, log_path)
	info = result
	
	if info != "":
		if "Exiting WriteFlashSlot FPGA_STATUS 0x0" in info:
			sendlog("CP FPGA image update success !")
		else:
			sendlog("CP FPGA image update fail !")
			return 1
	else:
		sendlog("Can't get result - CP FPGA update")
		return 1
	
	##reconfig to app then reconfig back to golden
	#Change FPGA slot to App
	print ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Change FPGA slot to App".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]))
	cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/fpgadiagnostics -reconfigApp\"".format(MBSNdict["cp_ip"])
		# Changed ssh to null user
	result = getresult(cmd)
	sendlog(result, 0, log_path)
	
	# time.sleep(60)
		
	#Change FPGA slot to Golden
	print ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Change FPGA slot to Golden".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]))
	cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/fpgadiagnostics -reconfiggolden\"".format(MBSNdict["cp_ip"])
		# Changed ssh to null user
	result = getresult(cmd)
	sendlog(result, 0, log_path)	

	time.sleep(30)
	
	return 0


def is_CP_update(MBSNdict):
	sn_log_folder = "{0}/{1}".format(g_log_folder, MBSNdict["mbsn"])
	update_flag = "{0}_already_update.log".format(MBSNdict["CP_SN"]) # 20240328 David modify to CP SN to avoid change CP card no update
	flag_path = "{0}/{1}".format(sn_log_folder, update_flag)	
	if not os.path.isfile(flag_path):
		print ("{0}_do_CP_FW_version check".format(MBSNdict["mbsn"]))

		# 20240328 David modify to remove record to avoid change CP card no update record
		print("[MBSN:{0}]Remove CP record file".format(MBSNdict["mbsn"]))
		record_log_name = "{0}_do_record_CP_golden_image_version.log".format(MBSNdict["mbsn"])
		record_log_path = "{0}/{1}".format(sn_log_folder, record_log_name)
		if not os.path.isfile(record_log_path):
			os.system("rm -rf {0}".format(record_log_path))
		
		print ("start to do_cp_soc_fw_check~~")
		ret = chk_soc_fw(MBSNdict)
		if ret != 0:
			if ret == 2:
				sendlog("SoC firmware is error and need to update")
				ret = update_soc_fw(MBSNdict)
				if ret != 0:
					sendlog("[MBSN:{0}] update SoC firmware FAIL".format(MBSNdict["mbsn"]), RED)
					return 1
				else:
					sendlog("[MBSN:{0}] update SoC firmware PASS".format(MBSNdict["mbsn"]), GREEN)
					
			else:
				sendlog("[MBSN:{0}] check SoC firmware FAIL. it can not update".format(MBSNdict["mbsn"]), RED)
				return 1

		print ("start to do_cp_fpga_fw_check~~")
		ret=chk_fpga_fw(MBSNdict)
		if ret != 0:
			if ret == 2:
				sendlog("FPGA firmware is error and need to update")
				ret = update_fpga_fw(MBSNdict)
				if ret != 0:
					sendlog("[MBSN:{0}] update FPGA firmware FAIL".format(MBSNdict["mbsn"]), RED)
					return 1
				else:
					sendlog("[MBSN:{0}] update FPGA firmware PASS".format(MBSNdict["mbsn"]), GREEN)
					
			else:
				sendlog("[MBSN:{0}] check FPGA firmware FAIL. it can not update".format(MBSNdict["mbsn"]), RED)
				return 1
		else:
			sendlog("[MBSN:{0}] check FPGA firmware PASS. no need to update".format(MBSNdict["mbsn"]), GREEN)
			
		os.system("touch {0}".format(flag_path))
		# sendlog(msg, 0, flag_path)
	return 0

#*****************************************************************************
# Function   : do_record_CP_and_reconifg
# Description: Step 1. check C2080 power. Step 2. record CP image version. 
#            : Step 3. Reconfig CP
# Inputs     : sn, rm_mac_addr, rm_ip, uut_mac_addr, uut_ip, LOCATION, 
#            : uut_to_rm_port, is_dict_info_correct, is_reconfig
# Outputs    : 0: PASS
#            : 1: FAIL
# Notice     : 
#*****************************************************************************
def do_record_CP_and_reconifg(MBSNdict):
	# MBSNdict = {
	# 	"mbsn": mbsn,
	# 	"bmc_mac_addr": bmc_mac_addr,
	# 	"bmc_ip": bmc_ip,
	# 	"nic_mac_addr": nic_mac_addr,
	# 	"nic_ip": nic_ip,
	# 	"cp_mac_addr": cp_mac_addr,
	# 	"cp_ip": cp_ip
	# }
	sn_log_folder = "{0}/{1}".format(g_log_folder, MBSNdict["mbsn"])
	try:
		os.makedirs(sn_log_folder)
		sendlog("make log folder ({0}) success".format(sn_log_folder), GREEN)
	except OSError as e:
		if e.errno == errno.EEXIST:
			sendlog("log folder ({0}) exist".format(sn_log_folder), GREEN)
		else:
			sendlog("{0}".format(e))
			return 3
	#flag_log_name = "{0}_updated_flag.log".format(MBSNdict["mbsn"])
	#flag_log_path = "{0}/{1}".format(sn_log_folder, flag_log_name)

	#step 1 : check uut power status
	# ret = chk_uut_power_state(MBSNdict)
	# if ret != 0:
	# 	msg = "[mbsn: {0}, bmc_ip: {1}] chk_uut_power_state FAIL".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"])
	# 	sendlog(msg, RED)
	# 	return 1
	sn_log_folder = "{0}/{1}".format(g_log_folder, MBSNdict["mbsn"])
	updating_log_name = "{0}_updating.log".format(MBSNdict["mbsn"])
	updating_flag = "{0}/{1}".format(sn_log_folder, updating_log_name)
	if not os.path.isfile(updating_flag):
		os.system("touch {0}".format(updating_flag))
		try:
			ret = is_CP_update(MBSNdict)
			if ret == 0:
				sendlog ("[mbsn: {0}, cp_ip: {1}] CP FW check/update Success".format(MBSNdict["mbsn"], MBSNdict["cp_ip"]))
			else:
				sendlog ("[mbsn: {0}, cp_ip: {1}] CP FW check/update Fail".format(MBSNdict["mbsn"], MBSNdict["cp_ip"]))
				clear_flag(MBSNdict)
				return 1
		except:
			sendlog ("[mbsn: {0}, cp_ip: {1}] CP FW check/update Fail".format(MBSNdict["mbsn"], MBSNdict["cp_ip"]))
			print (sys.exc_info())
			clear_flag(MBSNdict)
			return 1

		#step 2 : check CP slot mode
		ret = is_CP_Golden_mode(MBSNdict)
		if ret == 0:
			'''
			#step 2.1 : record CP golden image version
			ret = do_record_CP_golden_img_ver(MBSNdict)
			if ret != 0:
				msg = "[mbsn: {0}, bmc_ip: {1}] record CP golden image version FAIL".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"])
				sendlog(msg, RED)
				return 1
		
			#step 3 : do reconfig cp
			sendlog ("[mbsn: {0}, bmc_ip: {1}]=========DBG============ start to reconfig CP============".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"]))
			ret = do_reconfig_CP(MBSNdict)
			if ret != 0:
				msg = "[mbsn: {0}, bmc_ip: {1}] reconfig CP FAIL".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"])
				sendlog(msg, RED)
				return 1
			'''
			# sendlog ("[mbsn: {0}, bmc_ip: {1}] reconfig CP Success".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"]))
			sendlog ("[mbsn: {0}, cp_ip: {1}] reconfig CP Success".format(MBSNdict["mbsn"], MBSNdict["cp_ip"]))
		elif ret == 1:
			# print "====== [mbsn: {0}, bmc_ip: {1}] already APP mode".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"])
			# msg = "[mbsn: {0}, bmc_ip: {1}] already APP mode".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"])
			print ("====== [mbsn: {0}, cp_ip: {1}] already APP mode".format(MBSNdict["mbsn"], MBSNdict["cp_ip"]))
			msg = "[mbsn: {0}, cp_ip: {1}] already APP mode".format(MBSNdict["mbsn"], MBSNdict["cp_ip"])
			sendlog(msg, GREEN)
		elif ret == 2:
			# print "====== [mbsn: {0}, bmc_ip: {1}] reconfig CP to APP mode fail".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"])
			# msg = "[mbsn: {0}, bmc_ip: {1}] reconfig CP to APP mode fail".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"])
			print ("====== [mbsn: {0}, cp_ip: {1}] reconfig CP to APP mode fail".format(MBSNdict["mbsn"], MBSNdict["cp_ip"]))
			msg = "[mbsn: {0}, cp_ip: {1}] reconfig CP to APP mode fail".format(MBSNdict["mbsn"], MBSNdict["cp_ip"])
			sendlog(msg, RED)
			clear_flag(MBSNdict)
			return 1
		elif ret == 3:
			# msg = "[mbsn: {0}, bmc_ip: {1}]reconfig CP FAIL".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"])
			msg = "[mbsn: {0}, cp_ip: {1}]reconfig CP FAIL".format(MBSNdict["mbsn"], MBSNdict["cp_ip"])
			sendlog(msg, RED)
			clear_flag(MBSNdict)
			return 1
		elif ret == 4:
			# msg = "[mbsn: {0}, bmc_ip: {1}]log file create fail".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"])
			msg = "[mbsn: {0}, cp_ip: {1}]log file create fail".format(MBSNdict["mbsn"], MBSNdict["cp_ip"])
			sendlog(msg, RED)
			clear_flag(MBSNdict)
			return 1
		else:
			# msg = "[mbsn: {0}, bmc_ip: {1}] Get CP current mode fail".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"])
			msg = "[mbsn: {0}, cp_ip: {1}] Get CP current mode fail".format(MBSNdict["mbsn"], MBSNdict["cp_ip"])
			sendlog(msg, RED)
			# print "====== [mbsn: {0}, bmc_ip: {1}] Get CP current mode fail".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"])
			print ("====== [mbsn: {0}, cp_ip: {1}] Get CP current mode fail".format(MBSNdict["mbsn"], MBSNdict["cp_ip"]))
			clear_flag(MBSNdict)
			return 1
		print("Finish Do_record_cp_and_reconfig~~~~")
		os.system("rm -rf {0}".format(updating_flag))
	else:
		check_flag(MBSNdict)
		sendlog("[mbsn:{0}, cp_ip: {1}]doing update~~~".format(MBSNdict["mbsn"], MBSNdict["cp_ip"]), GREEN)

	return 0

#*****************************************************************************
# Function	 : check flag 
# Description: Check UUT flag
# Inputs	 : NA
# Outputs	 : NA
# Notice	 : 
#*****************************************************************************
def check_flag(sn_info_list):
	sn_log_folder = "{0}/{1}".format(g_log_folder, sn_info_list["mbsn"])
	updating_log_name = "{0}_updating.log".format(sn_info_list["mbsn"])
	updating_flag = "{0}/{1}".format(sn_log_folder, updating_log_name)
	
	stat=os.stat(updating_flag)
	diff=int(time.time())-int(stat.st_mtime)
	print("======================")
	print("flag time diff :{0}".format(diff/60))
	print("======================")
	if diff/60 > 180:
		os.system("rm -rf {0}".format(updating_flag))
		sendlog("[mbsn:{0}, cp_ip: {1}]update process to long! Remove the flag and do update again!".format(sn_info_list["mbsn"], sn_info_list["cp_ip"]), RED)
	
	
#*****************************************************************************
# Function	 : clear_flag
# Description: Clear UUT flag
# Inputs	 : NA
# Outputs	 : NA
# Notice	 : 
#*****************************************************************************
def clear_flag(sn_info_list):
	sn_log_folder = "{0}/{1}".format(g_log_folder, sn_info_list["mbsn"])
	log_name = "{0}_update_flag.log".format(sn_info_list["mbsn"])
	update_flag = "{0}/{1}".format(sn_log_folder, log_name)
	
	##enhance flow
	updating_log_name = "{0}_updating.log".format(sn_info_list["mbsn"])
	updating_flag = "{0}/{1}".format(sn_log_folder, updating_log_name)
	
	#os.system("rm -rf {0}".format(update_flag))
	os.system("rm -rf {0}".format(updating_flag))
	sendlog("[mbsn:{0}, cp_ip: {1}]update process fail! Clear all flag!".format(sn_info_list["mbsn"], sn_info_list["cp_ip"]), RED)

###########################################################################
##############################     MAIN     ###############################	
###########################################################################
if __name__ == "__main__":
	try:
		os.makedirs(g_log_folder)
		sendlog("make log folder ({0}) success".format(g_log_folder), GREEN)
	except OSError as e:
		if e.errno == errno.EEXIST:
			sendlog("log folder () exist", GREEN)
		else:
			sendlog("{0}".format(e))
			sys.exit(1)
	show_info()
	
	p = ""
	mbsn_info_list = []
	
	#while cycle always loop Please dont change i
	# while True:
	#initial
	# print("rm -rf /root/.ssh/known_hosts...")
	# os.system("rm -rf /root/.ssh/known_hosts")

	p = ""
	mbsn_info_list = []
	
	ret = get_mbsn_info_from_sf_folder(mbsn_info_list)
	if ret != 0:
		log = "get_mbsn_info_from_sf_folder Fail"
		sendlog(log,"FAIL")
	else:
		#print "-------------"
		#print mbsn_info_list
		#print "-------------"
		for i in range(len(mbsn_info_list)):
			print ("-" * 100)
			print (mbsn_info_list[i])
			print ("-" * 100)
			if not mbsn_info_list[i]["is_reconfig"]:
				mbsn = mbsn_info_list[i]["mbsn"]
				bmc_mac_addr = mbsn_info_list[i]["bmc_mac_addr"]
				bmc_ip = mbsn_info_list[i]["bmc_ip"]
				nic_mac_addr = mbsn_info_list[i]["nic_mac_addr"]
				nic_ip = mbsn_info_list[i]["nic_ip"]
				cp_mac_addr = mbsn_info_list[i]["cp_mac_addr"]
				cp_ip = mbsn_info_list[i]["cp_ip"]
				#do_record_CP_and_reconifg(mbsn, bmc_mac_addr, bmc_ip, nic_mac_addr, nic_ip)
				#'''
				# p = Process(target=do_record_CP_and_reconifg, args=(mbsn, bmc_mac_addr, bmc_ip, nic_mac_addr, nic_ip, cp_mac_addr, cp_ip))
				p = Process(target=do_record_CP_and_reconifg, args=(mbsn_info_list[i],))
				if p != "":
					p.start()
				#'''
			else:
				msg =  "[mbsn:{0}, cp_ip:{1}, cp_mac:{2}]reconfig already done".format(mbsn_info_list[i]["mbsn"], mbsn_info_list[i]["cp_ip"], mbsn_info_list[i]["cp_mac_addr"])
				sendlog(msg)
	# if p != "":
	# 	p.join()
	if build_side != "QMF": # 20230707 David modify QMF use crontab to run
		print ("wait 180 sec")
		time.sleep(180)
	sys.exit(0)
