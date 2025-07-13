# Copyright (C) 2019 Quanta Computer, Inc.
#
# This file is confidential and a trade secret of Quanta Computer, Inc.
# The receipt of or possession of this file does not convey any rights
# to reproduce or disclose its contents or to manufacture, use, or sell
# anything it may describe, in whole, or in part, without the specific
# written consent of Quanta Computer, Inc.
#
# File: 
# Author: 
# Date: 
# 
#

from multiprocessing import Process
from pexpect import pxssh
import sys
import os
import time 
import subprocess
import configparser
import shutil
import errno
# import commands
import re
#import paramiko
import datetime
import base64

ESC_GREEN		= "\033[32m"
ESC_RED			= "\033[31m"
ESC_YELLOW_F	        = "\033[33;1m"
ESC_YELLOW		= "\033[33m"
ESC_PINK		= "\033[35m"
ESC_LBLUE		= "\033[36m"
ESC_OFF			= "\033[0m"

GREEN			= 1
RED			= 2 
YELLOW			= 3
PINK			= 4
ORANGE			= 5
BLUE			= 6
#Sai update 0.1.4 for support QMF 
#David update 0.2.3 for T6G L11
PASS			= "PASS"
FAIL			= "FAIL"
VERSION			= "1.0.0"
EDITOR			= "David"
RELEASE_DATE	= "2023/08/30"
#Sai modify location for QMF 
g_model = "MODEL"
g_project = "L15"
g_log_folder = "/RACKLOG/{0}/RM_logs".format(g_project.lower())
g_mainlog_file = "{0}/monitor.log".format(g_log_folder)
g_win_config_folder = "/WIN/{0}/response/config".format(g_project)
g_win_prov_folder = "/WIN/{0}/keys/provisions".format(g_project)
g_win_ccr_folder = "/WIN/{0}/CCR".format(g_project)
g_dhcp_folder = ""
build_side = "QMF"
g_cp_tmp = "/tmp/"
g_cp_FPGA_firmware="CelestialPeak_SysInt_4.1.1-70c6abd1_jic.rpd"
g_cp_FPGA_firmware_loc="/project/firmware/l15/{0}".format(g_cp_FPGA_firmware)

#QMF#####################
tftp_ip = "10.0.3.254"
tftp_user = "root"
tftp_passwd = "M1cr0$0ft"
#########################
#QCI#####################
# tftp_ip = "192.168.0.253"
# tftp_user = "test"
# tftp_passwd = "qcitest"
#########################
image_path = "firmware/Celestial_Peak/dropcp-2.15FW-stos2008.4.23031201/rMedia/"
rm_firmware_path = "firmware/{0}/RM/".format(g_project.lower())
upgrade_image = "overlake-2008.4.23031201-prod.img"

#####################
# RM Command Define #
#####################
g_rm_username		= "root"
g_rm_password		= "$pl3nd1D"
g_cmd_rm_info	=	"show manager info"
g_cmd_check_pn	=	"set system cmd -i {0} -c fru print 0"
g_cmd_connect_cp =	"start serial session -i {0} -b 1"
g_cmd_disconnect_cp = "stop serial session -i {0} -b 1"
g_cmd_show_system_info = "show system info -i {0}"
g_cmd_install_catapult_driver = "modprobe catapult"
g_cmd_dumphealth = "fpgadiagnostics -dumpHealth"
g_cmd_reconfigGolden = "fpgadiagnostics -reconfigGolden"
g_cmd_reconfigapp = "fpgadiagnostics -reconfigApp"
g_cmd_fpgadiagnostics_list = "fpgadiagnostics -list"
g_cmd_show_system_state = "show system state -i {0}"
g_cmd_show_tftp = "show manager tftp list"
g_cmd_RM_FW_UPDATE = "set manager  fwupdate -f {0}"
#####################
# RM Command Define #
#####################

#############################
# SoC Update Command Define #
#############################
g_cmd_get_soc_firmware_ver = "cat /proc/device-tree/firmware/version"
g_cmd_get_soc_nitro_firmware_ver = "cat /proc/device-tree/firmware/nitro-version"
g_cmd_copy_image_to_rm = "set manager tftp get -s {0} -f {1}{2}"
g_cmd_mount_image_on_soc = "set system remotedrive mount -i {0} -b 1 -n {1}"
g_cmd_check_sda_exist = "lsblk | grep -i 'sda'"
g_cmd_set_bootmode_to_one = "bootmode set 1"
g_cmd_reboot = "reboot"
g_cmd_socflash = "socflash"
g_cmd_mkdir_usb_folder = "mkdir -p /tmp/usb"
g_cmd_mount_usb_folder = "mount /dev/sda1 /tmp/usb"
g_cmd_check_bin_file_exist = "ls -al /tmp/usb"
fip_pfm_file  = "A2040.FIP.PFM.46.bin"
fip_fw_file = "fip.bin"
nitro_pfm_file = "A2040.NITRO.PFM.46.bin"
nitro_fw_file = "nitro.img"
g_cmd_update_sop = ["cerberus_utility pfmupdate 0 /tmp/usb/{} 0".format(fip_pfm_file),
					"cerberus_utility socfwupdate 0 /tmp/usb/fip.bin 1",
					"cerberus_utility pfmupdate 1 /tmp/usb/{} 0".format(nitro_pfm_file),
					"cerberus_utility socfwupdate 1 /tmp/usb/nitro.img"]


g_cmd_set_bootmode_to_zero = "bootmode set 0"
g_cmd_reset_soc = "cerberus_utility socreset"
g_cmd_update_fpga = "fpgadiagnostics -writeFlashjic {0}"
g_cmd_cerberus_prov_chk = "cerberus_utility getcertstate"
g_cmd_cerberus_pfm_chk = "cerberus_utility pfmid {0} 0"
g_cmd_cerberus_exportcsr = "cerberus_utility exportcsr /tmp/{0}"
g_cmd_cerberus_prov_import = "cerberus_utility importsignedcert {0} /tmp/{1}"


#############################
# SoC Update Command Define #
#############################

########################
# Other Command Define #
########################
g_cmd_search_ip_QMF = "grep -B8 -A1 {0} /var/lib/dhcpd/dhcpd.leases | grep lease"
g_cmd_search_ip_QCI = "grep -B2 -A1 {0} /mnt/smbfs/__DHCP/dhcp2.txt | grep \"^192\" | awk -F \":\" '{{print $1}}'"
g_cmd_ping = "ping -c 3 {0}"
########################
# Other Command Define #
########################

############################
# Celestial Peak FW Define # #20230517 David: get from SFC
############################
exp_soc_fw_ver = "0002.15.230425-prd"
exp_soc_fw_nitro_ver = "0002.15.230425-prd"
############################
# Celestial Peak FW Define #
############################


#*****************************************************************************
# Function	 : getresult
# Description: Get the return value, stdout, stderr from input system command 
# Inputs	 : arg1: the command tobe execute
# Outputs	 : return value, stdout, stderr from the result of input command
# Notice	 : use subprocess.Popen(), no command result will show on screen
#*****************************************************************************
def getresult(arg1):

	p = subprocess.Popen(arg1, stdout=subprocess.PIPE, shell=True,encoding="utf-8")
	(text, err) = p.communicate()
	res = text
	
	return res

#*****************************************************************************
# Function	 : sendlog
# Description: Get log message then input to log file
# Inputs	 : message: log message, color: defult white, file: log file name
# Outputs	 : NA
# Notice	 : NA
#*****************************************************************************
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

	message = message.replace('\'','')
	if logfile != "":
		cmd = ("echo '{0} ====>> {1}' >>{2}".format(time.strftime("%m-%d-%y-%H:%M:%S"), message, logfile))
		os.system(cmd)
		
	cmd = ("echo '{0} ====>> {1}' >>{2}".format(time.strftime("%m-%d-%y-%H:%M:%S"), message, g_mainlog_file))
	os.system(cmd)

#*****************************************************************************
# Function	 : check flag 
# Description: Check UUT flag
# Inputs	 : NA
# Outputs	 : NA
# Notice	 : 
#*****************************************************************************
def check_flag(sn_info_list):
	sn_log_folder = "{0}/{1}".format(g_log_folder, sn_info_list["sn"])
	updating_log_name = "{0}_updating.log".format(sn_info_list["sn"])
	updating_flag = "{0}/{1}".format(sn_log_folder, updating_log_name)
	
	stat=os.stat(updating_flag)
	diff=int(time.time())-int(stat.st_mtime)
	print("======================")
	print("flag time diff :{0}".format(diff/60))
	print("======================")
	if diff/60 > 180:
		os.system("rm -rf {0}".format(updating_flag))
		sendlog("[RACKSN:{0} SN:{1}]update process to long! Remove the flag and do update again!".format(sn_info_list["RACKSN"],sn_info_list["sn"]), RED)
	
	
#*****************************************************************************
# Function	 : clear_flag
# Description: Clear UUT flag
# Inputs	 : NA
# Outputs	 : NA
# Notice	 : 
#*****************************************************************************
def clear_flag(sn_info_list):
	sn_log_folder = "{0}/{1}".format(g_log_folder, sn_info_list["sn"])
	log_name = "{0}_update_flag.log".format(sn_info_list["sn"])
	update_flag = "{0}/{1}".format(sn_log_folder, log_name)
	
	##enhance flow
	updating_log_name = "{0}_updating.log".format(sn_info_list["sn"])
	updating_flag = "{0}/{1}".format(sn_log_folder, updating_log_name)
	
	#os.system("rm -rf {0}".format(update_flag))
	os.system("rm -rf {0}".format(updating_flag))
	sendlog("[RACKSN:{0} SN:{1}]update process fail! Clear all flag!".format(sn_info_list["RACKSN"],sn_info_list["sn"]), RED)
	
#*****************************************************************************
# Function	 : show_info
# Description: Show Monitor version history
# Inputs	 : NA
# Outputs	 : NA
# Notice	 : V0.3 modify get_ip() function log message, get_mac_address_by_rm_port() add message "failure" check
#*****************************************************************************
def show_info():
	sendlog ("\n")
	sendlog ("\033[1;36;40m*******************************************************\033[0m")
	sendlog ("\033[1;36;40m*\033[1;33;40m Celecial Peak Config Check Program	 -\033[0m  V{0} {1} Release By {2} \033[1;36;40m*\033[0m".format(VERSION, RELEASE_DATE, EDITOR))
	sendlog ("\033[1;36;40m*******************************************************\033[0m")
	sendlog ("\n")

#*****************************************************************************
# Function       : send_data_sf
# Description: 
# Inputs         : NA
# Outputs        : NA
# Notice         : 
#*****************************************************************************
def send_data_sf(start_time,message,log_type, sf_sn, location, station, log_file):
	if build_side == "QMF":
		st_file = "/home/Monitor_reconfig_CP/{0}.ST".format(sf_sn)
	else:
		return 0
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
        #shutil.copyfile(st_file, '{0}request/mac/{1}.ST'.format(head_location, sf_sn))

#*****************************************************************************
# Function	 : login_rm
# Description: Use RM IP, username, and password to login RM
# Inputs	 : sn_info_list: SN list information  
# Outputs	 : ssh_object: the object of SSH 
#			 : None: can not return the object of SSH
# Notice	 : NA
#*****************************************************************************
def login_rm(sn_info_list):
	try:
		ssh_object = pxssh.pxssh()
		sendlog("[rm_ip:{0:>12} rm_mac: {1}] RM login".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"]))
		ssh_object.login(sn_info_list["rm_ip"], g_rm_username, g_rm_password, auto_prompt_reset=False)
		return ssh_object
	except pxssh.ExceptionPxssh as e:
		sendlog("[rm_ip:{0:>12} rm_mac: {1}] pxssh failed: login to RM.".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"]), RED)
		sendlog(e, RED)
		return None

#*****************************************************************************
# Function	 : send_cmd_to_cp
# Description: Send command to CP via RM, and execute it
# Inputs	 : ssh_object: the object of SSH
#			 : sn_info_list: SN list information
#			 : cmd: execute this cmd on RM
#            : sleep_time: when execute this cmd, need to wait sleep_time to get result
#            : log_path: record the log on this path
# Outputs	 : 0, ssh_object.before: it means PASS and return the result of ssh_object.before
#			 : 1, None: it means FAIL and return None
# Notice	 : NA
#*****************************************************************************
def send_cmd_to_cp(ssh_object, sn_info_list, cmd, sleep_time, log_path = ""):
	return send_cmd_to_rm(ssh_object, sn_info_list, cmd, sleep_time, log_path,device="CP")
	
#*****************************************************************************
# Function	 : send_cmd_to_rm
# Description: Send command to RM, and execute it
# Inputs	 : ssh_object: the object of SSH
#			 : sn_info_list: SN list information
#			 : cmd: execute this cmd on RM
#            : sleep_time: when execute this cmd, need to wait sleep_time to get result
#            : log_path: record the log on this path
#            : device: RM or CP
# Outputs	 : 0, ssh_object.before: it means PASS and return the result of ssh_object.before
#			 : 1, None: it means FAIL and return None
# Notice	 : NA
#*****************************************************************************
def send_cmd_to_rm(ssh_object, sn_info_list, cmd, sleep_time, log_path = "",device = "RM"):
	try:
		####check the link is connect or not, if not connect to rm again
		ssh_object.buffer = b"" #20230724 david
		# ssh_object.expect(r'.+')
		ssh_object.sendline(" ")
		ssh_object.prompt()
		
		if device == "CP":
			if "root@localhost:~#" not in ssh_object.before.decode ('utf-8').splitlines()[-1]:
				#Login to RM switch
				ssh_object = login_rm(sn_info_list)
				if ssh_object == None:
					return 1
				#Disconnect other device
				res = disconnect_cp_by_rm(ssh_object, sn_info_list)
				if res == 1:
					return 1
				#Login to CP by port
				res = connect_cp_by_rm(ssh_object, sn_info_list)
				if res == 1:
					return 1
		elif device == "RM":
			if "WcsCli#" not in ssh_object.before.decode ('utf-8').splitlines()[-1]:
				#Login to RM switch
				ssh_object = login_rm(sn_info_list)
				if ssh_object == None:
					return 1
			
		ssh_object.buffer = b"" #20230724 david
		# ssh_object.expect(r'.+')
		ssh_object.sendline(cmd)
		time.sleep(sleep_time)
		ssh_object.prompt()
		sendlog(ssh_object.before.decode ('utf-8'), 0, log_path)
		return 0, ssh_object.before.decode ('utf-8')
	except pxssh.ExceptionPxssh as e:
		sendlog("[rm_ip:{0} rm_mac: {1}] pxssh failed: can not execute cmd:{2}".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"], cmd), RED)
		sendlog(e, RED)
		return 1, None

#*****************************************************************************
# Function	 : scp_send_cmd_to_cp
# Description: Send scp command to cp, and execute it
# Inputs	 : ssh_object: the object of SSH
#			 : sn_info_list: SN list information
#			 : cmd: execute this cmd on RM
#            : sleep_time: when execute this cmd, need to wait sleep_time to get result
#            : log_path: record the log on this path
#            : device: CP
# Outputs	 : 0, ssh_object.before: it means PASS and return the result of ssh_object.before
#			 : 1, None: it means FAIL and return None
# Notice	 : NA
#*****************************************************************************
def scp_send_cmd_to_cp(ssh_object, sn_info_list, cmd, sleep_time, log_path = "",device = "CP"):
	try:
		####check the link is connect or not, if not connect to rm again
		ssh_object.buffer = b"" #20230724 david
		# ssh_object.expect(r'.+')
		ssh_object.sendline(" ")
		ssh_object.prompt()
		
		if device == "CP":
			if "root@localhost:~#" not in ssh_object.before.decode ('utf-8').splitlines()[-1]:
				#Login to RM switch
				ssh_object = login_rm(sn_info_list)
				if ssh_object == None:
					return 1
				#Disconnect other device
				res = disconnect_cp_by_rm(ssh_object, sn_info_list)
				if res == 1:
					return 1
				#Login to CP by port
				res = connect_cp_by_rm(ssh_object, sn_info_list)
				if res == 1:
					return 1
                    
		ssh_object.buffer = b"" #20230724 david
		# ssh_object.expect(r'.+')
		ssh_object.sendline(cmd)
		time.sleep(sleep_time)
		ssh_object.prompt()
		print(ssh_object.before.decode ('utf-8'), 0, log_path)
		if "Are you sure you want to continue connecting" in ssh_object.before.decode ('utf-8'):
			ssh_object.buffer = b"" #20230724 david
			# ssh_object.expect(r'.+')
			ssh_object.sendline("yes")
			ssh_object.prompt()
			print(ssh_object.before.decode ('utf-8'), 0, log_path)
			time.sleep(5)
		if "password:" in ssh_object.before.decode ('utf-8'):
			ssh_object.buffer = b"" #20230724 david
			# ssh_object.expect(r'.+')
			ssh_object.sendline(tftp_passwd)
			ssh_object.prompt()
			print(ssh_object.before.decode ('utf-8'), 0, log_path)

		return 0, ssh_object.before.decode ('utf-8')
	except pxssh.ExceptionPxssh as e:
		sendlog("[rm_ip:{0} rm_mac: {1}] pxssh failed: can not execute cmd:{2}".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"], cmd), RED)
		sendlog(e, RED)
		return 1, None
		
#_*****************************************************************************
#_ Function   : send_file_to_console
#_ Description: 
#_ Inputs     : cmd: the command tobe execute
#_ Outputs    : return value from the result of input command
#_ Notice     : 
#_*****************************************************************************
def send_file_to_console(ip,from_file,to_file):
	# os.system("rm -rf /root/.ssh/known_hosts")
	result_str="Another instance of"
	while "Another instance of" in  result_str:
		cmdstr = "sshpass -p 'overlake' scp -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null {0} stuser@[{1}]:{2}".format(from_file, ip, to_file)
		# (status,result) = commands.getstatusoutput(cmdstr)
		p = subprocess.Popen(cmdstr, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True,encoding="utf-8")
		stdout,stderr = p.communicate()
		output=stdout.strip() 
		ret=p.returncode
		status = ret
		result = output
		print ("status:{0}".format(status))
		print ("result:{0}".format(result))
		result_str = result
		time.sleep(1)
	return result

#_*****************************************************************************
#_ Function   : send_file_from_console
#_ Description: 
#_ Inputs     : cmd: the command tobe execute
#_ Outputs    : return value from the result of input command
#_ Notice     : 
#_*****************************************************************************
def send_file_from_console(ip,from_file,to_file):
	# os.system("rm -rf /root/.ssh/known_hosts")
	result_str="Another instance of"
	while "Another instance of" in  result_str:
		cmdstr = "sshpass -p 'overlake' scp -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@[{1}]:{0} {2} ".format(from_file, ip, to_file)
		# (status,result) = commands.getstatusoutput(cmdstr)
		p = subprocess.Popen(cmdstr, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True,encoding="utf-8")
		stdout,stderr = p.communicate()
		output=stdout.strip() 
		ret=p.returncode
		status = ret
		result = output
		print ("status:{0}".format(status))
		print ("result:{0}".format(result))
		result_str = result
		time.sleep(1)
	return result
	
#*****************************************************************************
# Function	 : disconnect_cp_by_rm
# Description: Use the port that UUT connect to RM to disconnect CP
# Inputs	 : ssh_object: the object of SSH 
#            : sn_info_list: SN list information
# Outputs	 : 0: PASS 
#			 : 1: FAIL
# Notice	 : NA
#*****************************************************************************
def disconnect_cp_by_rm(ssh_object, sn_info_list):
	try:
		ssh_object.buffer = b"" #20230724 david
		# ssh_object.expect(r'.+')
		ssh_object.sendline(g_cmd_disconnect_cp.format(sn_info_list["uut_to_rm_port"]))
		ssh_object.prompt()
		sendlog(ssh_object.before.decode ('utf-8'))
		return 0
	except pxssh.ExceptionPxssh as e:
		sendlog("[rm_ip:{0:>12} rm_mac: {1}] pxssh failed: can not disconnect other device".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"]), RED)
		sendlog(e, RED)
		return 1

#*****************************************************************************
# Function	 : connect_cp_by_rm
# Description: Use the port that UUT connect to RM to connect CP
# Inputs	 : ssh_object: the object of SSH 
#            : sn_info_list: SN list information
# Outputs	 : 0: PASS 
#			 : 1: FAIL
# Notice	 : NA
#*****************************************************************************
def connect_cp_by_rm(ssh_object, sn_info_list):
	try:
		ssh_object.buffer = b"" #20230724 david
		# ssh_object.expect(r'.+')
		ssh_object.sendline(g_cmd_connect_cp.format(sn_info_list["uut_to_rm_port"]))
		ssh_object.prompt()
		sendlog(ssh_object.before.decode ('utf-8'))
		return 0
	except pxssh.ExceptionPxssh as e:
		sendlog("[rm_ip:{0:>12} rm_mac: {1}] pxssh failed: can not login to CP by port".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"]), RED)
		sendlog(e, RED)
		return 1

#*****************************************************************************
# Function	 : get_mac_address_by_rm_port
# Description: Get NIC mac address by rm port
# Inputs	 : sn_info_list: SN list information
# Outputs	 : nic_mac_address: mac adddress
#            : 1: FAIL
# Notice	 : NA
#*****************************************************************************
def get_mac_address_by_rm_port(sn_info_list):
	sn_log_folder = "{0}/{1}".format(g_log_folder, sn_info_list["sn"])
	log_name = "{0}_get_mac_address_by_rm_port.log".format(sn_info_list["sn"])
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
			
	#Login to RM switch
	ssh_object = login_rm(sn_info_list)
	if ssh_object == None:
		return 1
		
	#Get system info and mac address by port
	ret, res = send_cmd_to_rm(ssh_object, sn_info_list, g_cmd_show_system_info.format(sn_info_list["uut_to_rm_port"]), 0, log_path)
	if ret != 0:
		return 1
	else:
		if res != "":
			if "Mac Address" in res:
				sendlog("Get system info and mac address by port success !")
			else:
				sendlog("Get system info and mac address by port fail !")
				return 1
		else:
			sendlog("Can't get result - get system info and mac address by port")
			return 1
	
	SN = ""
	nic_mac_address = ""
	info = res.split("\n")
	for i in range(len(info)):
		if "Mac Address" in info[i]:
			nic_mac_address = info[i].split(": ")[1].strip()
			print ("[Get port info] nic_mac_address = {0}".format(nic_mac_address))
		if "SerialNumber" in info[i]:
			SN = info[i].split(": ")[1].strip()
			print ("[Get port info] SerialNumber = {0}".format(SN))
	
	if SN != sn_info_list["csn"]: 
		sendlog("login to rm check SerialNumber FAIL : EXP = {0} GET = {1}.".format(sn_info_list["csn"], SN),"FAIL")
		sendlog(sn_info_list,"FAIL")
		return 1
	
	if nic_mac_address != "":
		nic_mac_address = nic_mac_address.replace(":", "")
		
		#20210830 Ed add when C2080 is power off by Rack Manager, the mac adddress show failure
		if "failure" in nic_mac_address:
			return 1

		return nic_mac_address
	else:
		sendlog("login to rm get mac adddress get fail ({0}.txt).".format(sn_info_list["sn"]), "FAIL")
		sendlog(sn_info_list,"FAIL")
		return 1
	

#*****************************************************************************
# Function	 : get_sn_info_from_config
# Description: Get all SN info from SF config files, rm table and DHCP
# Inputs	 : sn_info_list: an empty array for storing SN info
# Outputs	 : 0: PASS
#			 : 1: FAIL
# Notice	 : NA
#*****************************************************************************
def get_sn_info_from_config(sn_info_list):
	if not os.path.isdir(g_win_config_folder):
		sendlog("{0} not found.".format(g_win_config_folder), RED)
		return 1
	
	info = os.listdir(g_win_config_folder)
	for file_name in info:
		if ".txt" in file_name:
			SNdict = {
				"sn": "NA",
				"csn": "NA",
				"RACKSN": "NA",
				"rm_mac_addr": "NA",
				"rm_ip": "NA",
				"uut_mac_addr": "NA",
				"uut_ip": "NA",
				"LOCATION": "NA",
				"STATION": "NA",
				"CP_GOLDEN_IMAGE": "NA",
				"CP_FACTORY_IMAGE": "NA",
				"CP_SOC_FIP_FW":"NA",
				"CP_SOC_FIP_PFMID":"NA",
				"CP_SOC_NITRO_FW":"NA",
				"CP_SOC_NITRO_PFMID":"NA",
				"CP_SOC_OS_FW":"NA",
				"CP_SOC_DRIVER":"NA",
				"CP_SN": "NA",
				"RACK_MOUNT_FW":"NA",
				"uut_to_rm_port": "NA",
				"master_rm_port": "NA",
				"is_dict_info_correct": True,
				"is_reconfig": True
			}
			rackpn = ""
			rm_mac1 = ""
			rm_mac2 = ""
			file_path = "{0}/{1}".format(g_win_config_folder, file_name)
			if os.path.isfile(file_path):
			
				#Get sn from file name
				SNdict["sn"] = file_path.split('.')[0].strip().split('/')[-1].strip()
				f = open(file_path)
				for line in f:
				
					#Get rackpn from SN.txt
					if "RACKPN" in line:
						rackpn = line.split('=')[1].strip()
						
					#Get rm mac address from SN.txt
					if "RACK_MOUNT_MAC1" in line:
						rm_mac1 = line.split('=')[1].strip()

					if "RACK_MOUNT1_MAC1" in line:
						rm_mac2 = line.split('=')[1].strip()	
						
					#Get uut mac address from SN.txt
					if "ETH0" in line and "CP" not in line:
						nic_info = line.split('=')[1].strip()
						nic_info = nic_info.split(',')
						if len(nic_info) != 0:
							SNdict["uut_mac_addr"] = nic_info[0].strip()
							
					#Get uut location from SN.txt
					if "LOCATION" in line:
						SNdict["LOCATION"] = line.split('=')[1].strip()
					
					#Get uut station from SN.txt
					if "STATION" in line:
						SNdict["STATION"] = line.split('=')[1].strip()

					#Get RACKSN from SN.txt
					if "RACKSN" in line:
						SNdict["RACKSN"] = line.split('=')[1].strip()
					
					#Get CP_GOLDEN_IMAGE from SN.txt
					if "CP_GOLDEN_IMAGE" in line:
						SNdict["CP_GOLDEN_IMAGE"] = line.split('=')[1].strip()
					
					#Get CP_FACTORY_IMAGE from SN.txt					
					if "CP_FACTORY_IMAGE" in line:
						SNdict["CP_FACTORY_IMAGE"] = line.split('=')[1].strip()
					
					#Get CP_SOC_FIP_FW from SN.txt					
					if "CP_SOC_FIP_FW" in line:
						SNdict["CP_SOC_FIP_FW"] = line.split('=')[1].strip()
					#Get CP_SOC_FIP_PFMID from SN.txt					
					if "CP_SOC_FIP_PFMID" in line:
						SNdict["CP_SOC_FIP_PFMID"] = line.split('=')[1].strip().lower()
					#Get CP_SOC_NITRO_FW from SN.txt					
					if "CP_SOC_NITRO_FW" in line:
						SNdict["CP_SOC_NITRO_FW"] = line.split('=')[1].strip()
					#Get CP_SOC_NITRO_PFMID from SN.txt					
					if "CP_SOC_NITRO_PFMID" in line:
						SNdict["CP_SOC_NITRO_PFMID"] = line.split('=')[1].strip().lower()

					if "CP_SOC_OS_FW" in line:
						SNdict["CP_SOC_OS_FW"] = line.split('=')[1].strip()

					if "CP_SOC_DRIVER" in line:
						SNdict["CP_SOC_DRIVER"] = line.split('=')[1].strip()
					
					#Get RACK_MOUNT_FW from SN.txt					
					if "RACK_MOUNT_FW" in line:
						SNdict["RACK_MOUNT_FW"] = line.split('=')[1].strip()
					
					#Get CSN from SN.txt					
					if "CSN" in line:
						SNdict["csn"] = line.split('=')[1].strip()
						print ("CSN:{0}".format(SNdict["csn"]))
					
					#Get CP_SN from SN.txt
					if "CP_SN" in line:
						SNdict["CP_SN"] = line.split('=')[1].strip()
					
				f.close()
				
				#Check rackpn
				if rackpn == "":
					sendlog("rackpn get fail ({0}.txt).".format(SNdict["sn"]),"FAIL")
					sendlog(SNdict,"FAIL")
					continue
				print ("rackpn = {0}".format(rackpn))

				#Check rackpn in sku.ini and get sku name
				sku_name = ""
				master_node = ""
				sku_file_path = "{0}/sku.ini".format(g_win_ccr_folder)
				f = open(sku_file_path)
				for line in f:
					if rackpn in line:
						sku_name = line.split('=')[0].strip()					

				sku_config_file_path = "{0}/config_{1}.ini".format(g_win_ccr_folder, sku_name)
				f = open(sku_config_file_path)
				for line in f:
					if "node =" in line:
						master_node = line.split('=')[1].strip().split(',')

				f.close()
				if sku_name == "":
					sendlog("sku_name get fail ({0}.txt).".format(SNdict["sn"]),"FAIL")
					sendlog(SNdict,"FAIL")
					continue

				#Get uut rm port number from rm table
				rm_table_file_path = "{0}/rm_table_{1}.txt".format(g_win_ccr_folder, sku_name)
				print(rm_table_file_path)
				f = open(rm_table_file_path)
				for line in f:
					if SNdict["LOCATION"] in line:
						SNdict["uut_to_rm_port"] = line.split('-')[1].strip()
				f.close()

				sendlog("SN={0}".format(SNdict["sn"]))
				
				#Get rm ip from DHCP
				sendlog("get rm ip")
				if len(master_node) == 2:
					if SNdict["LOCATION"] >= master_node[0]:
						SNdict["rm_mac_addr"] = rm_mac2
						SNdict["master_rm_port"] = master_node[0]
					elif SNdict["LOCATION"] <= master_node[1]:
						SNdict["rm_mac_addr"] = rm_mac1
						SNdict["master_rm_port"] = master_node[1]
				else:
					SNdict["rm_mac_addr"] = rm_mac1
					SNdict["master_rm_port"] = master_node[0]
				SNdict["rm_ip"] = get_ip(SNdict["rm_mac_addr"])
				if SNdict["rm_ip"] == 1:
					sendlog("rm ip get fail ({0}.txt).".format(SNdict["sn"]),"FAIL")
					sendlog(SNdict,"FAIL")
					continue
				
				#Get C2080 nic mac address by rm port, this is for build from L10.
				# SNdict["uut_mac_addr"] = get_mac_address_by_rm_port(SNdict)
				# if SNdict["uut_mac_addr"] == 1:
					# sendlog("mac adddress by rm port get fail ({0}.txt).".format(SNdict["sn"]),"FAIL")
					# sendlog(SNdict,"FAIL")
					# continue
				
				#Get uut ip from DHCP
				sendlog("get uut ip: [{0}]{1}".format(SNdict["LOCATION"],SNdict["sn"]))
				SNdict["uut_ip"] = get_ip(SNdict["uut_mac_addr"])

				#Check reconfig flag
				if SNdict["uut_ip"] == 1 or SNdict["uut_ip"] == "":
					SNdict["is_reconfig"] = False

				#Check dict info correct
				if SNdict["sn"] == SNdict["rm_mac_addr"] == SNdict["rm_mac_addr"] == SNdict["uut_to_rm_port"] == "":
					SNdict["is_dict_info_correct"] = False
				if SNdict["rm_ip"] == 1:
					SNdict["is_dict_info_correct"] = False

				if SNdict["is_dict_info_correct"]:
					sn_info_list.append(SNdict)
				else:
					sendlog("SN.txt ({0}.txt) config error.".format(SNdict["sn"]),"FAIL")
					sendlog(SNdict,"FAIL")
			else:
				print ("{0} is not file".format(file_name))
	if len(sn_info_list) == 0:
		sendlog("Can not find any RACK_MOUNT_MAC1 in SN.txt","FAIL")
		return 1
	return 0

#*****************************************************************************
# Function	 : read_sn_info_from_config
# Description: Get all SN info from SF config files, rm table and DHCP
# Inputs	 : sn_info_list: an empty array for storing SN info
# Outputs	 : 0: PASS
#			 : 1: FAIL
# Notice	 : 20230829 David add only read SF config
#*****************************************************************************
def read_sn_info_from_config(file_name):	
	if ".txt" in file_name:
		SNdict = {
			"sn": "NA",
			"csn": "NA",
			"RACKSN": "NA",
			"rm_mac_addr": "NA",
			"rm_ip": "NA",
			"uut_mac_addr": "NA",
			"uut_ip": "NA",
			"LOCATION": "NA",
			"STATION": "NA",
			"CP_GOLDEN_IMAGE": "NA",
			"CP_FACTORY_IMAGE": "NA",
			"CP_SOC_FIP_FW":"NA",
			"CP_SOC_FIP_PFMID":"NA",
			"CP_SOC_NITRO_FW":"NA",
			"CP_SOC_NITRO_PFMID":"NA",
			"CP_SOC_OS_FW":"NA",
			"CP_SOC_DRIVER":"NA",
			"CP_SN": "NA",
			"RACK_MOUNT_FW":"NA",
			"uut_to_rm_port": "NA",
			"master_rm_port": "NA",
			"is_dict_info_correct": True,
			"is_reconfig": True
		}
		rackpn = ""
		rm_mac1 = ""
		rm_mac2 = ""
		file_path = "{0}/{1}".format(g_win_config_folder, file_name)
		if os.path.isfile(file_path):
		
			#Get sn from file name
			SNdict["sn"] = file_path.split('.')[0].strip().split('/')[-1].strip()
			f = open(file_path)
			for line in f:
			
				#Get rackpn from SN.txt
				if "RACKPN" in line:
					rackpn = line.split('=')[1].strip()
					
				#Get rm mac address from SN.txt
				if "RACK_MOUNT_MAC1" in line:
					rm_mac1 = line.split('=')[1].strip()

				if "RACK_MOUNT1_MAC1" in line:
					rm_mac2 = line.split('=')[1].strip()	
					
				#Get uut mac address from SN.txt
				if "ETH0" in line and "CP" not in line:
					nic_info = line.split('=')[1].strip()
					nic_info = nic_info.split(',')
					if len(nic_info) != 0:
						SNdict["uut_mac_addr"] = nic_info[0].strip()
						
				#Get uut location from SN.txt
				if "LOCATION" in line:
					SNdict["LOCATION"] = line.split('=')[1].strip()
				
				#Get uut station from SN.txt
				if "STATION" in line:
					SNdict["STATION"] = line.split('=')[1].strip()

				#Get RACKSN from SN.txt
				if "RACKSN" in line:
					SNdict["RACKSN"] = line.split('=')[1].strip()
				
				#Get CP_GOLDEN_IMAGE from SN.txt
				if "CP_GOLDEN_IMAGE" in line:
					SNdict["CP_GOLDEN_IMAGE"] = line.split('=')[1].strip()
				
				#Get CP_FACTORY_IMAGE from SN.txt					
				if "CP_FACTORY_IMAGE" in line:
					SNdict["CP_FACTORY_IMAGE"] = line.split('=')[1].strip()
				
				#Get CP_SOC_FIP_FW from SN.txt					
				if "CP_SOC_FIP_FW" in line:
					SNdict["CP_SOC_FIP_FW"] = line.split('=')[1].strip()
				#Get CP_SOC_FIP_PFMID from SN.txt					
				if "CP_SOC_FIP_PFMID" in line:
					SNdict["CP_SOC_FIP_PFMID"] = line.split('=')[1].strip().lower()
				#Get CP_SOC_NITRO_FW from SN.txt					
				if "CP_SOC_NITRO_FW" in line:
					SNdict["CP_SOC_NITRO_FW"] = line.split('=')[1].strip()
				#Get CP_SOC_NITRO_PFMID from SN.txt					
				if "CP_SOC_NITRO_PFMID" in line:
					SNdict["CP_SOC_NITRO_PFMID"] = line.split('=')[1].strip().lower()

				if "CP_SOC_OS_FW" in line:
					SNdict["CP_SOC_OS_FW"] = line.split('=')[1].strip()

				if "CP_SOC_DRIVER" in line:
					SNdict["CP_SOC_DRIVER"] = line.split('=')[1].strip()
				
				#Get RACK_MOUNT_FW from SN.txt					
				if "RACK_MOUNT_FW" in line:
					SNdict["RACK_MOUNT_FW"] = line.split('=')[1].strip()
				
				#Get CSN from SN.txt					
				if "CSN" in line:
					SNdict["csn"] = line.split('=')[1].strip()
					print ("CSN:{0}".format(SNdict["csn"]))
				
				#Get CP_SN from SN.txt
				if "CP_SN" in line:
					SNdict["CP_SN"] = line.split('=')[1].strip()
				
			f.close()
			
			#Check rackpn
			if rackpn == "":
				sendlog("rackpn get fail ({0}.txt).".format(SNdict["sn"]),"FAIL")
				sendlog(SNdict,"FAIL")
				return 1
			print ("rackpn = {0}".format(rackpn))

			#Check rackpn in sku.ini and get sku name
			sku_name = ""
			master_node = ""
			sku_file_path = "{0}/sku.ini".format(g_win_ccr_folder)
			f = open(sku_file_path)
			for line in f:
				if rackpn in line:
					sku_name = line.split('=')[0].strip()					

			sku_config_file_path = "{0}/config_{1}.ini".format(g_win_ccr_folder, sku_name)
			f = open(sku_config_file_path)
			for line in f:
				if "node =" in line:
					master_node = line.split('=')[1].strip().split(',')

			f.close()
			if sku_name == "":
				sendlog("sku_name get fail ({0}.txt).".format(SNdict["sn"]),"FAIL")
				sendlog(SNdict,"FAIL")
				return 1

			#Get uut rm port number from rm table
			rm_table_file_path = "{0}/rm_table_{1}.txt".format(g_win_ccr_folder, sku_name)
			print(rm_table_file_path)
			f = open(rm_table_file_path)
			for line in f:
				if SNdict["LOCATION"] in line:
					SNdict["uut_to_rm_port"] = line.split('-')[1].strip()
			f.close()

			sendlog("SN={0}".format(SNdict["sn"]))
			
			#Get rm ip from DHCP
			sendlog("get rm ip")
			if len(master_node) == 2:
				if SNdict["LOCATION"] >= master_node[0]:
					SNdict["rm_mac_addr"] = rm_mac2
					SNdict["master_rm_port"] = master_node[0]
				elif SNdict["LOCATION"] <= master_node[1]:
					SNdict["rm_mac_addr"] = rm_mac1
					SNdict["master_rm_port"] = master_node[1]
			else:
				SNdict["rm_mac_addr"] = rm_mac1
				SNdict["master_rm_port"] = master_node[0]
			SNdict["rm_ip"] = get_ip(SNdict["rm_mac_addr"])
			if SNdict["rm_ip"] == 1:
				sendlog("rm ip get fail ({0}.txt).".format(SNdict["sn"]),"FAIL")
				sendlog(SNdict,"FAIL")
				return 1
			
			#Get C2080 nic mac address by rm port, this is for build from L10.
			# SNdict["uut_mac_addr"] = get_mac_address_by_rm_port(SNdict)
			# if SNdict["uut_mac_addr"] == 1:
				# sendlog("mac adddress by rm port get fail ({0}.txt).".format(SNdict["sn"]),"FAIL")
				# sendlog(SNdict,"FAIL")
				# continue
			
			#Get uut ip from DHCP
			sendlog("get uut ip: [{0}]{1}".format(SNdict["LOCATION"],SNdict["sn"]))
			SNdict["uut_ip"] = get_ip(SNdict["uut_mac_addr"])

			#Check reconfig flag
			if SNdict["uut_ip"] == 1 or SNdict["uut_ip"] == "":
				SNdict["is_reconfig"] = False

			#Check dict info correct
			if SNdict["sn"] == SNdict["rm_mac_addr"] == SNdict["rm_mac_addr"] == SNdict["uut_to_rm_port"] == "":
				SNdict["is_dict_info_correct"] = False
			if SNdict["rm_ip"] == 1:
				SNdict["is_dict_info_correct"] = False

			if SNdict["is_dict_info_correct"]:
				return SNdict
			else:
				sendlog("SN.txt ({0}.txt) config error.".format(SNdict["sn"]),"FAIL")
				sendlog(SNdict,"FAIL")
				return 1
		else:
			print ("{0} is not file".format(file_name))
	
	return 1

#*****************************************************************************
# Function	 : get_ip
# Description: Change SF mac address format to dhcp.lease format, then search ip in dhcp.lease
# Inputs	 : mac_addr: SF mac address format
# Outputs	 : line: ip address
#			 : 1: can not found ip in dhcp.lease
# Notice	 : Make sure dhcp.lease location is correct
#*****************************************************************************
def get_ip(mac_addr):
	ip = "" 
	log = "get_rm_ip"
	mac_trans = (mac_addr[:2]+':'+mac_addr[2:4]+':'+mac_addr[4:6]+':'+mac_addr[6:8]+':'+mac_addr[8:10]+':'+mac_addr[10:12])
	mac_trans = mac_trans.lower()
	if build_side == "QTMC" or build_side == "QMF":
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
						sendlog("Get_IP MAC = {0} IP = {1:.<12}".format(mac_trans,line),"PASS")
						return line
				else:
					break
		sendlog(log,"FAIL")
		return 1
	elif build_side == "QCI":
		ip = getresult(g_cmd_search_ip_QCI.format(mac_trans))
		ip = ip.split("\n")
		for i in range(len(ip)):
			tmp = ip[i].strip()
			if tmp == "":
				continue
			ret = os.system(g_cmd_ping.format(tmp))
			if ret == 0:
				sendlog("Get_ip MAC = {0} IP = {1:.<12}".format(mac_trans,tmp),"PASS")
				return tmp
		sendlog("Get_IP MAC = {0} IP = {1:.<12}".format(mac_trans,ip),"FAIL")
		return 1
	else:
		sendlog("Unknown build side","FAIL")
		return 1

#*****************************************************************************
# Function	 : do_reconfig_connect_rm_port
# Description: Reconfig CP. Let NIC get IP address
# Inputs	 : sn_info_list: SN list information
# Outputs	 : 0: PASS
#			 : 1: FAIL
# Notice	 : Wait a direct way to get Soc image status
#*****************************************************************************
def do_reconfig_connect_rm_port(sn_info_list):
	sn_log_folder = "{0}/{1}".format(g_log_folder, sn_info_list["sn"])
	log_name = "{0}_do_reconfig.log".format(sn_info_list["sn"])
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
			
	#Login to RM switch
	ssh_object = login_rm(sn_info_list)
	if ssh_object == None:
		return 1
		
	#Disconnect other device
	res = disconnect_cp_by_rm(ssh_object, sn_info_list)
	if res == 1:
		return 1
	
	#Login to CP by port
	res = connect_cp_by_rm(ssh_object, sn_info_list)
	if res == 1:
		return 1

	try:
		if not sn_info_list["is_reconfig"]:
			sendlog("[rm_ip:{0:>12} rm_mac: {1} rm_port: {2}]do reconfig Celestial Peak.".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"], sn_info_list["uut_to_rm_port"]))
			sendlog("Need reconfig Celestial Peak", 0, log_path)
			ssh_object.sendline(g_cmd_install_catapult_driver)
			ssh_object.prompt()
			ssh_object.sendline(g_cmd_reconfigapp)
			ssh_object.prompt()
			sendlog(ssh_object.before.decode ('utf-8'), 0, log_path)
	except pxssh.ExceptionPxssh as e:
		sendlog("[rm_ip:{0:>12} rm_mac: {1} rm_port: {2}]pxssh failed: reconfig Celestial Peak.".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"], sn_info_list["uut_to_rm_port"]), RED)
		sendlog(e, RED)
		return 1

	sendlog("[rm_ip:{0:>12} rm_mac: {1} rm_port: {2}]CP Reconfig success".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"], sn_info_list["uut_to_rm_port"]))
	return 0

#*****************************************************************************
# Function	 : is_cp_golden_mode
# Description: Check CP is golden mode or not 
# Inputs	 : sn_info_list: SN list information
# Outputs	 : True: golden mode 
#			 : False: not golden mode
# Notice	 : NA
#*****************************************************************************
def is_cp_golden_mode(sn_info_list):
	try:
		ssh_object = pxssh.pxssh()
		ssh_object.force_password = True
		print ("login... IP = {0}, user = {1}, password = {2}".format(sn_info_list["rm_ip"], g_rm_username, g_rm_password))
		ssh_object.login(sn_info_list["rm_ip"], g_rm_username, g_rm_password, auto_prompt_reset=False)
		print ("stop serial port")
		ssh_object.sendline(g_cmd_disconnect_cp.format(sn_info_list["uut_to_rm_port"]))
		print ("start serial port")
		ssh_object.sendline(g_cmd_connect_cp.format(sn_info_list["uut_to_rm_port"]))
		print ("install catapult driver")
		ssh_object.sendline(g_cmd_install_catapult_driver)
		print ("dumpHealth")
		ssh_object.sendline(g_cmd_dumphealth)
		ssh_object.prompt()
	except pxssh.ExceptionPxssh as e:
		print (str(e))
		print ("pxssh fail")
		return False
		
	info = ssh_object.before.decode ('utf-8').split('\n')
	for line in info:
		print(line)
		if "[FPGA-CONFIG    ] OK " in line:
			golden_str = line.split()[3].split(',')[0].strip()
			status = golden_str.split(':')[1]
			if status == "0":
				print ("App mode")
				return False
			else:
				print ("Golden mode")
				return True
	
#*****************************************************************************
# Function	 : do_record_cp_golden_img_ver_connect_rm_port
# Description: Record CP image version 
# Inputs	 : sn_info_list: SN list information
# Outputs	 : 0: PASS
#			 : 1: FAIL
# Notice	 : NA
#*****************************************************************************
def do_record_cp_golden_img_ver_connect_rm_port(sn_info_list):
	sn_log_folder = "{0}/{1}".format(g_log_folder, sn_info_list["sn"])
	log_name = "{0}_do_record_cp_golden_image_version.log".format(sn_info_list["sn"])
	log_path = "{0}/{1}".format(sn_log_folder, log_name)
	
	update_flag = "{0}_update_flag.log".format(sn_info_list["sn"])
	update_flag_path = "{0}/{1}".format(sn_log_folder, update_flag)

	if os.path.isfile(update_flag_path):
		sendlog("[rm_ip:{0:>12} rm_mac: {1} rm_port: {2}]CP record is already done ,please see {3}".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"], sn_info_list["uut_to_rm_port"], log_path))
		return 0

	###20211004 Jeffhung remove log_name everytime
	if os.path.isfile(log_path):
		os.remove(log_path)
	
	try:
		os.makedirs(sn_log_folder)
		sendlog("make log folder ({0}) success".format(sn_log_folder), GREEN)
	except OSError as e:
		if e.errno == errno.EEXIST:
			sendlog("log folder ({0}) exist".format(sn_log_folder), GREEN)
		else:
			sendlog("{0}".format(e))
			return 1
	
	#Login to RM switch
	ssh_object = login_rm(sn_info_list)
	if ssh_object == None:
		return 1
	
	#Disconnect other device
	if disconnect_cp_by_rm(ssh_object, sn_info_list) == 1:
		return 1
	
	#Login to CP by port
	if connect_cp_by_rm(ssh_object, sn_info_list) == 1:
		return 1
	
	#Get CP chip id
	try:
		ssh_object.sendline(g_cmd_install_catapult_driver)
		time.sleep(1)
		ssh_object.sendline(g_cmd_fpgadiagnostics_list)
		time.sleep(1)
		ssh_object.prompt()
		sendlog(ssh_object.before.decode ('utf-8'), 0, log_path)
	except pxssh.ExceptionPxssh as e:
		sendlog("[rm_ip:{0:>12} rm_mac: {1}] pxssh failed: can not get CP chip id".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"]), RED)
		sendlog(e, RED)
		return 1
	
	readflag = False
	info = ssh_object.before.decode ('utf-8').split("\n")
	for i in range(len(info)):
		if "Chip ID" in info[i]:
			line_next = info[i+1]
			CP_chip_id = re.findall(r'\S+',line_next)[1]
			print ("CP_chip_id:{0}".format(CP_chip_id))
	
	actions=[
		["set CP to golden image", "fpgadiagnostics -chip {0} -reconfigToFlashSlot 0".format(CP_chip_id), "[hip-0,fn-0]:"],
		["get CP golden image role id", "fpgadiagnostics -chip {0} -mgmt -justreadreg 101".format(CP_chip_id), "Read register 101"],
		["get CP golden image version", "fpgadiagnostics -chip {0} -mgmt -justreadreg 65".format(CP_chip_id), "Read register 65"],
		["get CP golden image build version", "fpgadiagnostics -chip {0} -mgmt -justreadreg 59".format(CP_chip_id), "Read register 59"],
		["get CP golden shell package version", "fpgadiagnostics -chip {0} -dumpHealth".format(CP_chip_id), "[FPGA-CONFIG"]
	]

	for action,cmd,exp_output_str in actions:
		try:
			ssh_object.sendline(cmd)
			time.sleep(1)
			ssh_object.prompt()
			if not exp_output_str in ssh_object.before.decode ('utf-8'): #20240122 connect to CP againg and retry when the output is not expected.
				connect_cp_by_rm(ssh_object, sn_info_list)
				time.sleep(1)
				ssh_object.sendline(cmd)
				ssh_object.prompt()
			sendlog(ssh_object.before.decode ('utf-8'), 0, log_path)
		except pxssh.ExceptionPxssh as e:
			sendlog("[rm_ip:{0:>12} rm_mac: {1}] pxssh failed: can not {2}".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"], action), RED)
			sendlog(e, RED)
			return 1
	
	golen_image_role_id = ""
	golden_image_version = ""
	golden_image_build_version = ""
	info = ssh_object.before.decode ('utf-8').split("\n")
	for i in range(len(info)):
		if "Read register 101" in info[i]:
			golen_image_role_id = info[i].split(" ")[5].strip()
		if "Read register 65" in info[i]:
			golden_image_version = info[i].split(" ")[5].strip()
		if "Read register 59" in info[i]:
			golden_image_build_version = info[i].split(" ")[5].strip()
	 
	sendlog("[rm_ip:{0} rm_mac: {1} rm_port: {2}] golen_image_role_id = {3}".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"], sn_info_list["uut_to_rm_port"], golen_image_role_id), 0, log_path)
	sendlog("[rm_ip:{0} rm_mac: {1} rm_port: {2}] golden_image_version = {3}".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"], sn_info_list["uut_to_rm_port"], golden_image_version), 0, log_path)
	sendlog("[rm_ip:{0} rm_mac: {1} rm_port: {2}] golden_image_build_version = {3}".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"], sn_info_list["uut_to_rm_port"], golden_image_build_version), 0, log_path)
	
	if golen_image_role_id == golden_image_version == golden_image_build_version == "":
		sendlog("[rm_ip:{0:>12} rm_mac: {1} rm_port: {2}] record golden image fail".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"], sn_info_list["uut_to_rm_port"]))
		return 1
	
	sendlog("[rm_ip:{0:>12} rm_mac: {1} rm_port: {2}] record golden image finish, full porocess please see {3}".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"], sn_info_list["uut_to_rm_port"], log_path))
	##20211130 jeffadd flag
	os.system("touch {0}".format(update_flag_path))
		
	return 0
#*****************************************************************************
# Function	 : chk_uut_power_state
# Description: Check C2080 power ON/OFF/other
# Inputs	 : sn_info_list: SN list information
# Outputs	 : 0: PASS
#			 : 1: FAIL
# Notice	 : NA
#*****************************************************************************
def chk_uut_power_state(sn_info_list):
	sn_log_folder = "{0}/{1}".format(g_log_folder, sn_info_list["sn"])
	log_name = "{0}_chk_uut_power_state.log".format(sn_info_list["sn"])
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
	
	#Login to RM switch
	ssh_object = login_rm(sn_info_list)
	if ssh_object == None:
		return 1
	
	#Show system state
	ret, res = send_cmd_to_rm(ssh_object, sn_info_list, g_cmd_show_system_state.format(sn_info_list["uut_to_rm_port"]), 0, log_path)
	if ret != 0:
		return 1
	else:
		if res != "":
			if "State" in res:
				sendlog("Show system state success !")
			else:
				sendlog("Show system state fail !")
				return 1
		else:
			sendlog("Can't get result - show system state")
			return 1
	
	#Check power state
	power_state_flag = False
	info = res.split("\n")
	for line in info:
		if "State" in line:
			if "ON" in line:
				power_state_flag = True
	
	if power_state_flag:
		sendlog("[rm_ip:{0:>12} rm_mac: {1} rm_port: {2}] power on".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"], sn_info_list["uut_to_rm_port"]))
		return 0
	else:
		sendlog("[rm_ip:{0:>12} rm_mac: {1} rm_port: {2}] power off".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"], sn_info_list["uut_to_rm_port"]))
		return 1

#*****************************************************************************
# Function	 : do_record_cp_and_reconfig
# Description: Step 1. check C2080 power
#            : Step 2. record CP image version
#			 : Step 3. Reconfig CP
# Inputs	 : sn_info_list: SN list information 
# Outputs	 : 0: PASS
#			 : 1: FAIL
# Notice	 : 
#*****************************************************************************
def do_record_cp_and_reconfig(sn_info_list):
	print ("sn = {0}".format(sn_info_list["sn"]))
	print ("rm_mac_addr = {0}".format(sn_info_list["rm_mac_addr"]))
	print ("rm_ip = {0}".format(sn_info_list["rm_ip"]))
	print ("uut_mac_addr = {0}".format(sn_info_list["uut_mac_addr"]))
	print ("uut_ip = {0}".format(sn_info_list["uut_ip"]))
	print ("LOCATION = {0}".format(sn_info_list["LOCATION"]))
	print ("STATION = {0}".format(sn_info_list["STATION"]))
	print ("uut_to_rm_port = {0}".format(sn_info_list["uut_to_rm_port"]))
	print ("is_dict_info_correct = {0}".format(sn_info_list["is_dict_info_correct"]))
	print ("is_reconfig = {0}".format(sn_info_list["is_reconfig"]))
	sendlog("[{0}]{1} need record golden image and do reconfig".format(sn_info_list["LOCATION"], sn_info_list["sn"]))
	#step 1 : check uut power status
	if chk_uut_power_state(sn_info_list) != 0: 
		sendlog("[SN: {0}] chk_uut_power_state FAIL".format(sn_info_list["sn"]), RED)
		return 1
	#step 2 : check CP slot mode
	if is_cp_golden_mode(sn_info_list):
		#step 2.1 : In Golden, record CP golden image version
		if sn_info_list["STATION"] == "PRETEST":
			if do_record_cp_golden_img_ver_connect_rm_port(sn_info_list) != 0:
				sendlog("[SN: {0}] record CP golden image version FAIL".format(sn_info_list["sn"]), RED)
				return 1
		#step 3 : do reconfig 
		if do_reconfig_connect_rm_port(sn_info_list) != 0:
			sendlog("[SN: {0}] reconfig CP FAIL".format(sn_info_list["sn"]), RED)
			return 1
	return 0

#*****************************************************************************
# Function	 : get_soc_version
# Description: Use command to get SoC firmware/Nitro firmware version
# Inputs	 : ssh_object: the object of SSH
#            : sn_info_list: SN list information
#            : cmd: execute this cmd on RM
#            : log_path: record the log on this path
# Outputs	 : 0, version: it means PASS, and return SoC firmware/Nitro firmware version
#			 : 1, None: it means FAIL, and return None
# Notice	 : NA
#*****************************************************************************
def get_soc_version(ssh_object, sn_info_list, cmd, log_path):
	ret, res = send_cmd_to_cp(ssh_object, sn_info_list, cmd, 0, log_path)
	if ret != 0:
		return 1, None

	if res != "":
		res = res.split("\n")
		for line in res:
			if "devroot" in line: 
				return 0, line.split('root')[0]
			if "prdroot" in line:
				return 0, line.split('root')[0]
	else:
		return 1, None

#*****************************************************************************
# Function	 : do_soc_fw_chk
# Description: Check SoC firmware first. If the version is not as expected, 
#			 : it will update to correct version
# Inputs	 : sn_info_list: SN list information
# Outputs	 : 0: PASS
#			 : 1: FAIL
# Notice	 : NA
#*****************************************************************************
def do_soc_fw_chk(sn_info_list):
	sn_log_folder = "{0}/{1}".format(g_log_folder, sn_info_list["sn"])
	flag_name = "{0}_first_update_soc_fw.log".format(sn_info_list["sn"])
	flag_path = "{0}/{1}".format(sn_log_folder, flag_name)
	ret = chk_soc_fw(sn_info_list)
	if ret != 0:
		if ret == 2:
			sendlog("SoC firmware is error and need to update")
			ret = update_soc_fw(sn_info_list)
			if ret != 0:
				sendlog("[RACKSN:{0} SN:{1}] update SoC firmware FAIL".format(sn_info_list["RACKSN"],sn_info_list["sn"]), RED)
				return 1
			else:
				sendlog("[RACKSN:{0} SN:{1}] update SoC firmware PASS".format(sn_info_list["RACKSN"],sn_info_list["sn"]), GREEN)
				return 0
		else:
			sendlog("[RACKSN:{0} SN:{1}] check SoC firmware FAIL. it can not update".format(sn_info_list["RACKSN"],sn_info_list["sn"]), RED)
			return 1
	elif chk_pfmid(sn_info_list) != 0: #20230724 David add chk_pfmid
		sendlog("First SoC firmware update and do PFM active")
		ret = first_update_soc_fw(sn_info_list)
		if ret != 0:
			sendlog("[RACKSN:{0} SN:{1}] update SoC firmware FAIL".format(sn_info_list["RACKSN"],sn_info_list["sn"]), RED)
			os.system("rm -rf {}".format(flag_path))
			return 1
		else:
			sendlog("[RACKSN:{0} SN:{1}] update SoC firmware PASS".format(sn_info_list["RACKSN"],sn_info_list["sn"]), GREEN)
			return 0
	else:
		sendlog("[RACKSN:{0} SN:{1}] check SoC firmware PASS. no need to update".format(sn_info_list["RACKSN"],sn_info_list["sn"]), GREEN)
		if chk_pfmid(sn_info_list) != 0: # 20220525 David add PFM check
			sendlog("[RACKSN:{0} SN:{1}] SoC PFM FAIL".format(sn_info_list["RACKSN"],sn_info_list["sn"]), RED)
			
		return 0

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
def chk_soc_fw(sn_info_list):
	sn_log_folder = "{0}/{1}".format(g_log_folder, sn_info_list["sn"])
	log_name = "{0}_chk_soc_fw.log".format(sn_info_list["sn"])
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
	
	#Login to RM switch
	ssh_object = login_rm(sn_info_list)
	if ssh_object == None:
		return 1
	
	#Disconnect other device
	if disconnect_cp_by_rm(ssh_object, sn_info_list) == 1:
		return 1
	
	#Login to CP by port
	if connect_cp_by_rm(ssh_object, sn_info_list) == 1:
		return 1
	
	#Get SoC firmware version
	ret, res = get_soc_version(ssh_object, sn_info_list, g_cmd_get_soc_firmware_ver, log_path)
	if ret != 0:
		sendlog("Can't get SoC firmware version !")
		return 1
	else:
		get_soc_fw_ver = res
		print("get_soc_fw_ver = {0}".format(get_soc_fw_ver))
	
	#Get SoC Nitro firmware version
	ret, res = get_soc_version(ssh_object, sn_info_list, g_cmd_get_soc_nitro_firmware_ver, log_path)
	if ret != 0:
		sendlog("Can't get SoC Nitro firmware version !")
		return 1
	else:
		get_soc_fw_nitro_ver = res
		print("get_soc_fw_nitro_ver = {0}".format(get_soc_fw_nitro_ver))

	#Disconnect other device
	if disconnect_cp_by_rm(ssh_object, sn_info_list) == 1:
		return 1
	
	#Judge SoC firmware/Nitro firmware version are as expected or not
	if sn_info_list["CP_SOC_FIP_FW"] != get_soc_fw_ver:
		sendlog("SoC firmware version check FAIL ! exp:{0}, get:{1}".format(sn_info_list["CP_SOC_FIP_FW"], get_soc_fw_ver), RED)
		return 2
	else:
		sendlog("SoC firmware version check PASS ! exp:{0}, get:{1}".format(sn_info_list["CP_SOC_FIP_FW"], get_soc_fw_ver), GREEN)
		if sn_info_list["CP_SOC_NITRO_FW"] != get_soc_fw_nitro_ver:
			sendlog("SoC firmware Nitro version check FAIL ! exp:{0}, get:{1}".format(sn_info_list["CP_SOC_NITRO_FW"], get_soc_fw_nitro_ver), RED)
			return 2
		else:
			sendlog("SoC firmware Nitro version check PASS ! exp:{0}, get:{1}".format(sn_info_list["CP_SOC_NITRO_FW"], get_soc_fw_nitro_ver), GREEN)

	return 0


def is_success(res):
	completion = False
	for line in res.split("\n"):
		if "Completion Code:" in line:
			if "Success" in line:
				completion = True
			else:
				completion = False
	return completion	

	
	
#*****************************************************************************
# Function	 : update_rm_fw
# Description: follow updating RM firmware version SOP to update
# Inputs	 : sn_info_list: SN list information
# Outputs	 : 0: PASS
#			 : 1: FAIL
# Notice	 : NA
#*****************************************************************************
def update_rm_fw(sn_info_list):	  
	sn_log_folder = "{0}/{1}".format(g_log_folder, sn_info_list["sn"])
	log_name = "{0}_update_rm_fw.log".format(sn_info_list["sn"])
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
	
	#Login to RM switch
	ssh_object = login_rm(sn_info_list)
	if ssh_object == None:
		return 1
	
	#Disconnect other device
	if disconnect_cp_by_rm(ssh_object, sn_info_list) == 1:
		return 1
		
		
	##20220105 check RM FW if not fit SF then update
	rmfw_image = "m2010fwimage-{0}.tgz".format(sn_info_list["RACK_MOUNT_FW"])
	if sn_info_list["STATION"] == "PRETEST":	
		ret, res = send_cmd_to_rm(ssh_object, sn_info_list, "show manager version", 20, log_path)
		if ret != 0:
			return 1
		else:
			if res != "":
				if sn_info_list["RACK_MOUNT_FW"] in res:
					sendlog("[RACKSN:{0};SN:{1}]RM FW is {2}!".format(sn_info_list["RACKSN"],sn_info_list["sn"],rmfw_image))
					return 0
				else:
					sendlog("[RACKSN:{0};SN:{1}]RM FW is not {2}!".format(sn_info_list["RACKSN"],sn_info_list["sn"],rmfw_image))
					##start to update RM FW
					ret, res = send_cmd_to_rm(ssh_object, sn_info_list, g_cmd_show_tftp, 100, log_path)
					if ret != 0:
						return 1
					else:
						if res != "":
							if rmfw_image in res:
								sendlog("[RACKSN:{0};SN:{1}]{2} image from TFTP to RM success !".format(sn_info_list["RACKSN"],sn_info_list["sn"],rmfw_image))
							else:
								#Copy image from TFTP to RM
								ret, res = send_cmd_to_rm(ssh_object, sn_info_list, g_cmd_copy_image_to_rm.format(tftp_ip, rm_firmware_path, rmfw_image), 200, log_path)
								if ret != 0:
									return 1
								else:
									if res != "":
										if is_success(res):
											sendlog("Copy RM FW image from TFTP to RM success !")
											
										else:
											sendlog("Copy RM FW image from TFTP to RM fail !")
											return 1
									else:
										sendlog("Can't get result - copy RM FW image from TFTP to RM")
										return 1
							###update RM FW (g_cmd_RM_FW_UPDATE)
							ret, res = send_cmd_to_rm(ssh_object, sn_info_list, g_cmd_RM_FW_UPDATE.format(rmfw_image), 5, log_path)
							if ret != 0:
								sendlog("[RACKSN:{0};SN:{1}]RMFW {2} update Fail!".format(sn_info_list["RACKSN"],sn_info_list["sn"],rmfw_image)) 	
								return 1
							else:
								if res != "":
									if is_success(res):
										sendlog("[RACKSN:{0};SN:{1}]update RM FW image  success !Need to sleep 900s!".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
										time.sleep(900)
										return 0
								else:
									sendlog("[RACKSN:{0};SN:{1}]Can't get result - update RM FW image.".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
									return 1

						else:
							sendlog("Can't get result - For RM FW IMAGE!")
							return 1
	
	
#*****************************************************************************
# Function	 : update_soc_fw
# Description: follow updating SoC firmware version SOP to update
# Inputs	 : sn_info_list: SN list information
# Outputs	 : 0: PASS
#			 : 1: FAIL
# Notice	 : NA
#*****************************************************************************
def update_soc_fw(sn_info_list):	  
	sn_log_folder = "{0}/{1}".format(g_log_folder, sn_info_list["sn"])
	log_name = "{0}_update_soc_fw.log".format(sn_info_list["sn"])
	log_path = "{0}/{1}".format(sn_log_folder, log_name)
	upload_img_flag = "{0}/{1}_overlakeimg_flag.log".format(g_log_folder,sn_info_list["RACKSN"])
	flag_name = "{0}_first_update_soc_fw.log".format(sn_info_list["sn"])
	flag_path = "{0}/{1}".format(sn_log_folder, flag_name)
	try:
		os.makedirs(sn_log_folder)
		sendlog("make log folder ({0}) success".format(sn_log_folder), GREEN)
	except OSError as e:
		if e.errno == errno.EEXIST:
			sendlog("log folder ({0}) exist".format(sn_log_folder), GREEN)
		else:
			sendlog("{0}".format(e))
			return 1
	
	#Login to RM switch
	ssh_object = login_rm(sn_info_list)
	if ssh_object == None:
		return 1
	
	#Disconnect other device
	if disconnect_cp_by_rm(ssh_object, sn_info_list) == 1:
		return 1

	
	#check tftp list from RM
	ret, res = send_cmd_to_rm(ssh_object, sn_info_list, g_cmd_show_tftp, 100, log_path)
	if ret != 0:
		return 1
	else:
		if res != "":
			if upgrade_image in res:
				sendlog("{0} image from TFTP to RM success !".format(upgrade_image))
			else:
				#Copy image from TFTP to RM
				ret, res = send_cmd_to_rm(ssh_object, sn_info_list, g_cmd_copy_image_to_rm.format(tftp_ip, image_path, upgrade_image), 200, log_path)
				if ret != 0:
					return 1
				else:
					if res != "":
						if is_success(res):
							os.system("touch {0}".format(upload_img_flag))
							sendlog("Copy image from TFTP to RM success !")
						else:
							sendlog("Copy image from TFTP to RM fail !")
							return 1
					else:
						sendlog("Can't get result - copy image from TFTP to RM")
						return 1
		else:
			sendlog("Can't get result - check image on SoC")
			return 1
	
	#Mount image on SoC
	ret, res = send_cmd_to_rm(ssh_object, sn_info_list, g_cmd_mount_image_on_soc.format(sn_info_list["uut_to_rm_port"], upgrade_image), 10, log_path)
	if ret != 0:
		return 1
	else:
		if res != "":
			if is_success(res):
				sendlog("Mount image on SoC success !")
			else:
				sendlog("Mount image on SoC fail !")
				return 1
		else:
			sendlog("Can't get result - mount image on SoC")
			return 1

	#Login to CP by port
	if connect_cp_by_rm(ssh_object, sn_info_list) == 1:
		return 1

	#Check "sda" drive mounted
	ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_check_sda_exist, 0, log_path)
	if ret != 0:
		return 1
	else:
		if res != "":
			if "sda1" in res:
				sendlog("Check 'sda' drive mounted success !")
			else:
				sendlog("Check 'sda' drive mounted fail !")
				return 1
		else:
			sendlog("Can't get result - check 'sda' drive mounted")
			return 1

	#Set bootmode to 1
	ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_one, 0, log_path)
	if ret != 0:
		return 1
	else:
		if res != "":
			if "boot mode is set to 0x01" in res:
				sendlog("Set boot mode to 1 success !")
			else:
				sendlog("Set boot mode to 1 fail !")
				return 1
		else:
			sendlog("Can't get result - set boot mode to 1")
			return 1
	
	#Reboot the SoC
	ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_reboot, 150, log_path)
	if ret != 0:
		return 1

	ret, res = send_cmd_to_cp(ssh_object, sn_info_list, " ", 10, log_path)
	if ret != 0:
			return 1
	else:
		if res !="":
			#print "DBG:{0}".format(res)
			if "root@localhost:~#" in res.split("\n")[-1]:
				sendlog("Reboot SOC success !") 
			else:
				time.sleep(10)
				ret, res = send_cmd_to_cp(ssh_object, sn_info_list, " ", 3, log_path)
				if ret != 0:
					return 1
				else:
					if res !="":
						if "root@localhost:~#" in res.split("\n")[-1]:
							sendlog("After Wait 10 second! Reboot SOC success !")
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
	ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_socflash, 150, log_path)
	if ret != 0:
		return 1
	sendlog("Execute socflash command success!!!")

	#Create /tmp/usb folder
	ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_mkdir_usb_folder, 0, log_path)
	if ret != 0:
		return 1
	sendlog("Create /tmp/usb folder success!!")

	#Mount /tmp/usb to /dev/sda1
	ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_mount_usb_folder, 0, log_path)
	if ret != 0:
		return 1
	sendlog("Mount /tmp/usb to /dev/sda1 success!!")
	
	#Check bin files exist or not
	ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_check_bin_file_exist, 0, log_path)
	if ret != 0:
		return 1
	else:
		if res != "":
			if fip_pfm_file and fip_fw_file and nitro_pfm_file and nitro_fw_file in res:
				sendlog("Check bin files success !")
			else:
				sendlog("Check bin files fail !")
				return 1
		else:
			sendlog("Can't get result - check bin files")
			return 1
		
	#do update FW
	for cmd in g_cmd_update_sop:
		ret, res = send_cmd_to_cp(ssh_object, sn_info_list, cmd, 120, log_path)
		if ret != 0:
			return 1

		if res != "":
			if "Cerberus command completed successfully" in res:
				sendlog("Use update command success.")
			else:
				sendlog("Use update command fail: {0}".format(cmd))
				return 1
		else:
			sendlog("Can't get cmd result: {0}".format(cmd))
			return 1

	#Set bootmode to 0
	ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, log_path)
	if ret != 0:
		return 1
	else:
		if res != "":
			if "boot mode is set to 0x00" in res:
				sendlog("Set boot mode to 0 success !")
			else:
				sendlog("Set boot mode to 0 fail !")
				return 1
		else:
			sendlog("Can't get result - set boot mode to 0")
			return 1
		
	#Reset SoC
	ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_reset_soc, 90, log_path)
	if ret != 0:
		return 1	

	os.system("touch {0}".format(flag_path))

	return 0


#*****************************************************************************
# Function	 : first_update_soc_fw
# Description: follow updating SoC firmware version SOP to update
# Inputs	 : sn_info_list: SN list information
# Outputs	 : 0: PASS
#			 : 1: FAIL
# Notice	 : NA
#*****************************************************************************
def first_update_soc_fw(sn_info_list):	  
	sn_log_folder = "{0}/{1}".format(g_log_folder, sn_info_list["sn"])
	log_name = "{0}_update_soc_fw.log".format(sn_info_list["sn"])
	log_path = "{0}/{1}".format(sn_log_folder, log_name)
	flag_name = "{0}_first_update_soc_fw.log".format(sn_info_list["sn"])
	flag_path = "{0}/{1}".format(sn_log_folder, flag_name)
	try:
		os.makedirs(sn_log_folder)
		sendlog("make log folder ({0}) success".format(sn_log_folder), GREEN)
	except OSError as e:
		if e.errno == errno.EEXIST:
			sendlog("log folder ({0}) exist".format(sn_log_folder), GREEN)
		else:
			sendlog("{0}".format(e))
			return 1

	os.system("touch {0}".format(flag_path))

	#Login to RM switch
	ssh_object = login_rm(sn_info_list)
	if ssh_object == None:
		return 1
	
	#Disconnect other device
	if disconnect_cp_by_rm(ssh_object, sn_info_list) == 1:
		return 1

	#Login to CP by port
	if connect_cp_by_rm(ssh_object, sn_info_list) == 1:
		return 1

	g_cmd_copy_image_to_soc = "scp {0}@{1}:/tftpboot/{2}{3} /tmp/".format(tftp_user,tftp_ip,image_path,upgrade_image)
	#Copy image from TFTP to CP SoC
	ret, res = scp_send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_copy_image_to_soc, 0, log_path)
	if ret != 0:
		return 1
	else:
		if res != "":
			if "100%" in res:
				sendlog("copy image from TFTP to SoC success !")
			else:
				sendlog("copy image from TFTP to SoC fail !")
				return 1
		else:
			sendlog("Can't get result - copy image from TFTP to SoC")
			return 1

	
	g_cmd_losetup_image = "losetup -f -P /tmp/{}".format(upgrade_image)
	#Execute "losetup_image" command
	ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_losetup_image, 0, log_path)
	if ret != 0:
		return 1
	sendlog("Execute losetup command success!!!")

	g_cmd_check_loop2_exist = "lsblk"
	#Check "loop2" drive losetup
	ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_check_loop2_exist, 0, log_path)
	if ret != 0:
		return 1
	else:
		if res != "":
			if "loop2p1" in res:
				sendlog("Check 'loop2p1' drive losetup success !")
			else:
				sendlog("Check 'loop2p1' drive losetup fail !")
				return 1
		else:
			sendlog("Can't get result - check 'loop2' drive losetup")
			return 1

	#Create /tmp/usb folder
	ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_mkdir_usb_folder, 0, log_path)
	if ret != 0:
		return 1
	sendlog("Create /tmp/usb folder success!!")

	g_cmd_mount_usb_loop2p1_folder = "mount /dev/loop2p1 /tmp/usb/"
	#Mount /tmp/usb to /dev/loop2p1
	ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_mount_usb_loop2p1_folder, 0, log_path)
	if ret != 0:
		return 1
	sendlog("Mount /tmp/usb to /dev/loop2p1 success!!")
	
	#Check bin files exist or not
	ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_check_bin_file_exist, 0, log_path)
	if ret != 0:
		return 1
	else:
		if res != "":
			if fip_pfm_file and fip_fw_file and nitro_pfm_file and nitro_fw_file in res:
				sendlog("Check bin files success !")
			else:
				sendlog("Check bin files fail !")
				return 1
		else:
			sendlog("Can't get result - check bin files")
			return 1

	#do update FW
	for cmd in g_cmd_update_sop:
		ret, res = send_cmd_to_cp(ssh_object, sn_info_list, cmd, 120, log_path)
		if ret != 0:
			return 1

		if res != "":
			if "Cerberus command completed successfully" in res:
				sendlog("Use update command success.")
			else:
				sendlog("Use update command fail: {0}".format(cmd))
				return 1
		else:
			sendlog("Can't get cmd result: {0}".format(cmd))
			return 1
		
	#Reset SoC
	ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_reset_soc, 90, log_path)
	if ret != 0:
		return 1
	#Check SoC PFM status
	if chk_pfmid(sn_info_list) != 0: # 20220525 David add PFM check
		sendlog("[RACKSN:{0} SN:{1}] SoC PFM FAIL".format(sn_info_list["RACKSN"],sn_info_list["sn"]), RED)
		return 1

	return 0


#*****************************************************************************
# Function	 : do_cp_fpga_upgrade
# Description: Do FPGA of CP fw check & upgrade
# Inputs	 : sn_info_list: SN list information
# Outputs	 : 0 - check pass
#			 : 1 - check fail
# Notice	 : NA
#*****************************************************************************
def do_cp_fpga_upgrade(sn_info_list):
	
	print ("start to do_cp_fpga_upgrade~~")
	ret=chk_fpga_fw(sn_info_list)
	if ret != 0:
		if ret == 2:
			sendlog("FPGA firmware is error and need to update")
			ret = update_fpga_fw(sn_info_list)
			if ret != 0:
				sendlog("[RACKSN:{0} SN:{1}] update FPGA firmware FAIL".format(sn_info_list["RACKSN"],sn_info_list["sn"]), RED)
				return 1
			else:
				sendlog("[RACKSN:{0} SN:{1}] update FPGA firmware PASS".format(sn_info_list["RACKSN"],sn_info_list["sn"]), GREEN)
				return 0
		else:
			sendlog("[RACKSN:{0} SN:{1}] check FPGA firmware FAIL. it can not update".format(sn_info_list["RACKSN"],sn_info_list["sn"]), RED)
			return 1
	else:
		sendlog("[RACKSN:{0} SN:{1}] check FPGA firmware PASS. no need to update".format(sn_info_list["RACKSN"],sn_info_list["sn"]), GREEN)
		return 0

#*****************************************************************************
# Function	 : get_fpga_version
# Description: Use command to get fpga version
# Inputs	 : ssh_object: the object of SSH
#            : sn_info_list: SN list information
#            : cmd: execute this cmd on RM
#            : log_path: record the log on this path
# Outputs	 : 0, version: it means PASS, and return SoC firmware/Nitro firmware version
#			 : 1, None: it means FAIL, and return None
# Notice	 : NA
#*****************************************************************************
def get_fpga_version(ssh_object, sn_info_list, cmd, log_path):
	ret, res = send_cmd_to_cp(ssh_object, sn_info_list, cmd, 0, log_path)
	if ret != 0:
		return 1, res,None,None

	if res != "":
		for line in res.splitlines():
			if "[FPGA-CONFIG-EX ] OK " in line:
				ver = line.split()[6].split(',')[1].split('-')[0].strip()
				role = line.split()[7].split(',')[0].split('role:')[1]
		return 0, res,ver,role
	else:
		return 1, res,None,None
	
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
def chk_fpga_fw(sn_info_list):
	sn_log_folder = "{0}/{1}".format(g_log_folder, sn_info_list["sn"])
	log_name = "{0}_chk_fpga_fw.log".format(sn_info_list["sn"])
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
	
	#Login to RM switch
	ssh_object = login_rm(sn_info_list)
	if ssh_object == None:
		return 1
	
	#Disconnect other device
	if disconnect_cp_by_rm(ssh_object, sn_info_list) == 1:
		return 1
	
	#Login to CP by port
	if connect_cp_by_rm(ssh_object, sn_info_list) == 1:
		return 1
		
	#load driver
	ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_install_catapult_driver, 0, log_path)
	if ret != 0:
		return 1
		
	#Change FPGA slot to Golden
	ret, res = reconfig_fpga_slot(ssh_object, sn_info_list, g_cmd_reconfigGolden, log_path)
	if ret != 0:
		sendlog("Can't reconfig CP FPGA slot successfully![DBG]:{0}".format(res))
		return 1
	
	#Check FPGA version
	ret, res, ver, role = get_fpga_version(ssh_object, sn_info_list, g_cmd_dumphealth, log_path)
	if ret != 0:
		sendlog("Can't get FPGA firmware version !")
		return 1
	else:
		get_fpga_fw_ver = ver+','+role
		print("GOLDEN:get_fpga_fw_ver = {0}".format(get_fpga_fw_ver))
		if sn_info_list["CP_GOLDEN_IMAGE"] != get_fpga_fw_ver:
			return 2
	'''	
	#Change FPGA slot to App
	ret, res = reconfig_fpga_slot(ssh_object, sn_info_list, g_cmd_reconfigapp, log_path)
	if ret != 0:
		sendlog("Can't reconfig CP FPGA slot successfully![DBG]:{0}".format(res))
		return 1
	
	#Check FPGA version
	ret, res, ver, role = get_fpga_version(ssh_object, sn_info_list, g_cmd_dumphealth, log_path)
	if ret != 0:
		sendlog("Can't get FPGA firmware version !")
		return 1
	else:
		get_fpga_fw_ver = ver+','+role
		print("FACTORY:get_fpga_fw_ver = {0}".format(get_fpga_fw_ver))
		if sn_info_list["CP_FACTORY_IMAGE"] != get_fpga_fw_ver:
			return 2
	'''
	#Disconnect other device
	if disconnect_cp_by_rm(ssh_object, sn_info_list) == 1:
		return 1
	
	return 0
	
#*****************************************************************************
# Function	 : reconfig_fpga_slot
# Description: reconfig CP fpga slot
# Inputs	 : sn_info_list: SN list information
# Outputs	 : 0: PASS
#			 : 1: FAIL
# Notice	 : NA
#*****************************************************************************
def reconfig_fpga_slot(ssh_object, sn_info_list, cmd, log_path):
	ret, res = send_cmd_to_cp(ssh_object, sn_info_list, cmd, 0, log_path)
	if ret != 0:
		return 1, None
	
	if res != "":
		res = res.splitlines()[-4]
		if "SUCCEEDED" in res:
			return 0,res
		else:
			return 1,res
	else:
		return 1, None
	
#*****************************************************************************
# Function	 : update_fpga_fw
# Description: follow updating FPGA firmware version SOP to update
# Inputs	 : sn_info_list: SN list information
# Outputs	 : 0: PASS
#			 : 1: FAIL
# Notice	 : NA
#*****************************************************************************
def update_fpga_fw(sn_info_list):	  
	sn_log_folder = "{0}/{1}".format(g_log_folder, sn_info_list["sn"])
	log_name = "{0}_update_fpga_fw.log".format(sn_info_list["sn"])
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
	
	#Login to RM switch
	ssh_object = login_rm(sn_info_list)
	if ssh_object == None:
		return 1
	
	#Disconnect other device
	if disconnect_cp_by_rm(ssh_object, sn_info_list) == 1:
		return 1
	
	#Login to CP by port
	if connect_cp_by_rm(ssh_object, sn_info_list) == 1:
		return 1
	
	#Find CP SOC IP
	ret, res = send_cmd_to_cp(ssh_object, sn_info_list, "ifconfig", 0, log_path)
	if ret != 0:
		return 1, None
	if res != "":
		for line in res.splitlines():
			if "inet " in line:
				CP_IP = re.findall( r'[0-9]+(?:\.[0-9]+){3}', line)[0]
				ret = os.system(g_cmd_ping.format(CP_IP))
				if ret == 0:
					sendlog("Get_CP_IP IP = {0}".format(CP_IP),"PASS")
					break
			
	#Copy image to CP SOC
	send_file_to_console(CP_IP,g_cp_FPGA_firmware_loc,g_cp_tmp)
	print("Copy {0} to CP {1}".format(g_cp_FPGA_firmware_loc,g_cp_tmp))

	#update FPGA image
	ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_update_fpga.format(g_cp_tmp+g_cp_FPGA_firmware), 500, log_path)
	if ret != 0:
		return 1
	else:
		if res != "":
			if "Exiting WriteFlashSlot FPGA_STATUS 0x0" in res.splitlines()[-4]:
				sendlog("CP FPGA image update success !")
			else:
				sendlog("CP FPGA image update fail !")
				return 1
		else:
			sendlog("Can't get result - CP FPGA update")
			return 1
	
	##reconfig to app then reconfig back to golden
	#Change FPGA slot to App
	ret, res = reconfig_fpga_slot(ssh_object, sn_info_list, g_cmd_reconfigapp, log_path)
	if ret != 0:
		sendlog("Can't reconfig CP FPGA slot successfully![DBG]:{0}".format(res))
		return 1
		
	#Change FPGA slot to Golden
	ret, res = reconfig_fpga_slot(ssh_object, sn_info_list, g_cmd_reconfigGolden, log_path)
	if ret != 0:
		sendlog("Can't reconfig CP FPGA slot successfully![DBG]:{0}".format(res))
		return 1
	
	
	return 0

#*****************************************************************************
# Function	 : chk_pfmid
# Description: Check CP PFMID
# Inputs	 : sn_info_list: SN list information
# Outputs	 : True : already provision
#			 : False : not provision
# Notice	 : NA
#*****************************************************************************
def chk_pfmid(sn_info_list):
	sn_log_folder = "{0}/{1}".format(g_log_folder, sn_info_list["sn"])
	log_name = "{0}_cp_pfmid.log".format(sn_info_list["sn"])
	log_path = "{0}/{1}".format(sn_log_folder, log_name)
	#Login to RM switch
	ssh_object = login_rm(sn_info_list)
	if ssh_object == None:
		return 1
	
	#Disconnect other device
	if disconnect_cp_by_rm(ssh_object, sn_info_list) == 1:
		return 1
	
	#Login to CP by port
	if connect_cp_by_rm(ssh_object, sn_info_list) == 1:
		return 1	
		
	#check cerberus FIP_PFMID
	ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_cerberus_pfm_chk.format(0), 3, log_path)
	if ret != 0:
		sendlog("Can't get cerberus provision status!")
		return 1
	get_fip_pfmid = ""
	for line in res.splitlines():
		if  "Cerberus PFM ID:" in line:
			get_fip_pfmid = line.split()[3]
			print ("get_fip_pfmid:{0}".format(get_fip_pfmid))
		elif "No valid PFM found" in line:
			print ("Cerberus FIP No PFM")
			return 2
			
	
	#check cerberus NITRO_PFMID
	ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_cerberus_pfm_chk.format(1), 3, log_path)
	if ret != 0:
		sendlog("Can't get cerberus provision status!")
		return 1
	get_nitro_pfmid = ""
	for line in res.splitlines():
		if  "Cerberus PFM ID:" in line:
			get_nitro_pfmid = line.split()[3]
			print ("get_nitro_pfmid:{0}".format(get_nitro_pfmid))
		elif "No valid PFM found" in line:
			print ("Cerberus NITRO No PFM")
			return 2
	
	#Judge SoC FIP/NITRO PFMID are as expected or not
	if sn_info_list["CP_SOC_FIP_PFMID"] != get_fip_pfmid:
		sendlog("[RACKSN:{0} SN:{1}]SoC FIP PFMID FAIL ! exp:{2}, get:{3}".format(sn_info_list["RACKSN"],sn_info_list["sn"],sn_info_list["CP_SOC_FIP_PFMID"], get_fip_pfmid), RED)
		return 2
	else:
		sendlog("[RACKSN:{0} SN:{1}]SoC FIP PFMID check PASS ! exp:{2}, get:{3}".format(sn_info_list["RACKSN"],sn_info_list["sn"],sn_info_list["CP_SOC_FIP_PFMID"], get_fip_pfmid), GREEN)
		if sn_info_list["CP_SOC_NITRO_PFMID"] != get_nitro_pfmid:
			sendlog("[RACKSN:{0} SN:{1}]SoC NITRO PFMID check FAIL ! exp:{2}, get:{3}".format(sn_info_list["RACKSN"],sn_info_list["sn"],sn_info_list["CP_SOC_NITRO_PFMID"], get_nitro_pfmid), RED)
			return 2
		else:
			sendlog("[RACKSN:{0} SN:{1}]SoC NITRO PFMID check PASS ! exp:{2}, get:{3}".format(sn_info_list["RACKSN"],sn_info_list["sn"],sn_info_list["CP_SOC_NITRO_PFMID"], get_nitro_pfmid), GREEN)

	#Disconnect other device
	if disconnect_cp_by_rm(ssh_object, sn_info_list) == 1:
		return 1
	
	print("CP is Provision~~")
	return 0

#*****************************************************************************
# Function	 : is_provision
# Description: Check CP is provisioned
# Inputs	 : sn_info_list: SN list information
# Outputs	 : True : already provision
#			 : False : not provision
# Notice	 : NA
#*****************************************************************************
def is_provision(sn_info_list):
	sn_log_folder = "{0}/{1}".format(g_log_folder, sn_info_list["sn"])
	log_name = "{0}_cp_prov.log".format(sn_info_list["sn"])
	log_path = "{0}/{1}".format(sn_log_folder, log_name)
	#Login to RM switch
	ssh_object = login_rm(sn_info_list)
	if ssh_object == None:
		return 1
	
	#Disconnect other device
	if disconnect_cp_by_rm(ssh_object, sn_info_list) == 1:
		return 1
	
	#Login to CP by port
	if connect_cp_by_rm(ssh_object, sn_info_list) == 1:
		return 1	
		
	#cerberus provision check
	ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_cerberus_prov_chk, 3, log_path)
	if ret != 0:
		sendlog("Can't get cerberus provision status!")
		return 1
	
	if "Device Certificate State" not in res: #20230803 David add
		sendlog("Can't get cerberus provision status!")
		return 1
		
	for line in res.splitlines():
		if  "Device Certificate State: Device certificate chain is incomplete or invalid" in line: # 20230724 David remove error code message
			print("Not Provision!")
			return False
	
	#Disconnect other device
	if disconnect_cp_by_rm(ssh_object, sn_info_list) == 1:
		return 1
	
	print("CP is Provision~~")
	return True

#*****************************************************************************
# Function	 : do_cp_provision
# Description: Do CP provision
# Inputs	 : sn_info_list: SN list information
# Outputs	 : 0 - provision success
#			 : 1 - do provision fail
# Notice	 : NA
#*****************************************************************************
def do_cp_provision(sn_info_list):
	print("do cp provision!")
	#Sai modify .log to .txt
	try:#20230728 David add try except for run crash
		prov_file = "{0}/{1}.txt".format(g_win_prov_folder, sn_info_list["CP_SN"])

		if not os.path.isfile(prov_file):
			sendlog("[RACKSN:{0} SN:{1}] There is no key file in /WIN/{2}/keys/provisions folder!!".format(sn_info_list["RACKSN"],sn_info_list["sn"],g_project),"FAIL")
			return 1	
		cfg = cfg_parser_file(prov_file)
		print (cfg)
		if cfg == 1 : 
			sendlog ("Cant get the key!! please check it .", "FAIL")
			log_type="WARNING" #20230821 David add for send no key file status to sf
			message = "Cant get the CP provision key!! please check it."
			start_time=time.strftime("%Y%m%d%H%M%S")
			log_file =""
			send_data_sf(start_time,message, log_type, sn_info_list["sn"], sn_info_list["LOCATION"], sn_info_list["STATION"], log_file)

			return 1
		key_list = ['PUBLICKEY', 'HWKEY1', 'HWKEY2', 'HWKEY3']
		for key_idx in key_list:
			print (key_idx)
			if key_idx in cfg:
				with open('{0}/{1}_{2}.log'.format(g_win_prov_folder,sn_info_list["CP_SN"], key_idx.upper()), 'w') as f:
					f.write(cfg[key_idx].strip().replace("-----BEGIN CERTIFICATE-----","").replace("-----END CERTIFICATE-----",""))
				cfg.pop(key_idx)
						
		print ("key file is ready.")
		
		# Compare Public Key
		if compare_public_key(sn_info_list)!=0:
			sendlog("Cerberus Public Key Check FAIL.","FAIL")
			return 1

		# Fuse Certificate
		## Device ID: HWKey1
		if cerberus_fuse (sn_info_list,0, 1):
			sendlog ("Device ID fuse certificate success.", "PASS")
		else:
			sendlog ("Device ID fuse certificate fault.", "FAIL")
			return 1
		
		## Root CA: HWKey3
		if cerberus_fuse (sn_info_list,1, 3):
			sendlog ("Root CA fuse certificate success.", "PASS")
		else:
			sendlog ("Root CA fuse certificate fault.", "FAIL")
			return 1

		## Intermediate CA: HWKey2
		if cerberus_fuse (sn_info_list,2, 2):
			sendlog ("Intermediate CA fuse certificate success.", "PASS")
		else:
			sendlog ("Intermediate CA fuse certificate fault.", "FAIL")
			return 1
		
		if not is_provision(sn_info_list):
			sendlog ("Cerberus Provision Fail.", "FAIL")
			return 1
	except:
		return 1
	return 0

def compare_public_key(sn_info_list):
	sn_log_folder = "{0}/{1}".format(g_log_folder, sn_info_list["sn"])
	log_name = "{0}_compare_public_key.log".format(sn_info_list["sn"])
	log_path = "{0}/{1}".format(sn_log_folder, log_name)
	pub_file = '{0}/{1}_PUBLICKEY.log'.format(g_win_prov_folder,sn_info_list["CP_SN"])
	csr_file = "{0}/{1}.bin".format(g_win_prov_folder,sn_info_list["CP_SN"])
	csr_bin = "{0}.bin".format(sn_info_list["CP_SN"])
	pem_file = "{0}/{1}.pem".format(g_win_prov_folder,sn_info_list["CP_SN"])
	csr_public_key = ""
	CP_IP=""

	print("pub_file location:{0}".format(pub_file))	
	if not os.path.isfile(pub_file):
		sendlog ("SF Public Key file does not exist: {0}".format(pub_file), "FAIL")
		return 1
	#Login to RM switch
	ssh_object = login_rm(sn_info_list)
	if ssh_object == None:
		return 1
	
	#Disconnect other device
	if disconnect_cp_by_rm(ssh_object, sn_info_list) == 1:
		return 1
	
	#Login to CP by port
	if connect_cp_by_rm(ssh_object, sn_info_list) == 1:
		return 1	
		
	ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_cerberus_exportcsr.format(csr_bin), 1, log_path)
	if ret != 0:
		sendlog("Execute cerberus exportcsr fail!DBG:{0}".format(res))
		return False
	else:
		sendlog("Execute cerberus exportcsr PASS!DBG:{0}".format(res))
	
	#Find CP SOC IP
	ret, res = send_cmd_to_cp(ssh_object, sn_info_list, "ifconfig", 0, log_path)
	if ret != 0:
		return 1, None
	if res != "":
		for line in res.splitlines():
			if "inet " in line:
				CP_IP = re.findall( r'[0-9]+(?:\.[0-9]+){3}', line)[0]
				ret = os.system(g_cmd_ping.format(CP_IP))
				if ret == 0:
					sendlog("Get_CP_IP IP = {0}".format(CP_IP),"PASS")
					break
	#Copy public key to local
	send_file_from_console(CP_IP, "/tmp/{0}.bin".format(sn_info_list["CP_SN"]), g_win_prov_folder)
	
	# Get Public
	os.system("echo '-----BEGIN CERTIFICATE REQUEST-----' > {0}".format(pem_file))
	cmd="base64 {0} >> {1}".format(csr_file, pem_file)
	p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True,encoding="utf-8")
	stdout,stderr = p.communicate()
	output=stdout.strip()
	ret=p.returncode
	if ret != 0:
		sendlog ("Execute command fail: base64 {0}".format(csr_file),"FAIL")
		return 1
	os.system("echo '-----END CERTIFICATE REQUEST-----' >> {0}".format(pem_file))
	
	cmd="openssl req -in {0} -noout -text | grep -A5 'pub:'".format(pem_file)
	p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True,encoding="utf-8")
	stdout,stderr = p.communicate()
	output=stdout.strip()
	ret=p.returncode
	
	tmp_key=""
	for line in output.split("\n"):
		if "pub" in line:
			continue
		tmp_key += line.strip().replace(":", "")
	# csr_public_key = tmp_key.decode("hex").encode("base64").replace("\n", "") #python2
	csr_public_key = base64.b64encode(bytes.fromhex(tmp_key)).decode('utf-8') #20230724 David change to python3
	
	#add for debug csr_public_key getting null
	if output == "" or tmp_key == "" or csr_public_key == "":
		sendlog("CSR key get NULL","FAIL")
		sendlog("output: {0}".format(output))
		sendlog("tmp_key: {0}".format(tmp_key))
		sendlog("csr_public_key: {0}".format(csr_public_key))
		
	sendlog ("Cerberus SN: {0}".format(sn_info_list["CP_SN"]))
	sendlog ("CSR Public Key: {0}".format(csr_public_key))
	
	
	sf_pub_key = getresult("cat {0}".format(pub_file))
	if sf_pub_key == csr_public_key:
		sendlog ("Cerberus Public Key Check PASS", "PASS")
	else:
		sendlog ("Cerberus Public Key Check FAIL, EXP={0}".format(sf_pub_key), "FAIL")
		return 1
	
	return 0
	
#*****************************************************************************
# Function   : cerberus_fuse
# Description: Fuse Certificate
# Inputs     : None
# Outputs    : True - Pass  ; Faile - Fail
# Notice     : None
#*****************************************************************************
def cerberus_fuse(sn_info_list,cert_idx, file_idx):
	sn_log_folder = "{0}/{1}".format(g_log_folder, sn_info_list["sn"])
	log_name = "{0}_cp_prov_import.log".format(sn_info_list["sn"])
	log_path = "{0}/{1}".format(sn_log_folder, log_name)
	CP_IP=""
	
	key_file = '{2}/{0}_HWKEY{1}.log'.format(sn_info_list["CP_SN"], file_idx,g_win_prov_folder)
	
	key_file_bin = '{2}/{0}_HWKEY{1}.bin'.format(sn_info_list["CP_SN"], file_idx,g_win_prov_folder)
	key_file_bin_soc = '{0}_HWKEY{1}.bin'.format(sn_info_list["CP_SN"], file_idx)
	if not os.path.isfile(key_file):
		sendlog ("Key file does not exist: {0}".format(key_file), "FAIL")
		return False
	if os.path.isfile(key_file_bin):
		os.remove (key_file_bin)

	cmd = "base64 -di {0} > {1}".format(key_file, key_file_bin)
	p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True,encoding="utf-8")
	stdout,stderr = p.communicate()
	output=stdout.strip()
	ret=p.returncode
	sendlog("Execute CMD: {0}, RET: {1}".format(cmd, ret))
	if ret != 0:
		sendlog ("Execute CMD fail", "FAIL")
		return False

	#Login to RM switch
	ssh_object = login_rm(sn_info_list)
	if ssh_object == None:
		return 1

	#Disconnect other device
	if disconnect_cp_by_rm(ssh_object, sn_info_list) == 1:
		return 1		
	
	#Login to CP by port
	if connect_cp_by_rm(ssh_object, sn_info_list) == 1:
		return 1	
	
	#Find CP SOC IP
	ret, res = send_cmd_to_cp(ssh_object, sn_info_list, "ifconfig", 0, log_path)
	if ret != 0:
		return 1, None
	retry = 0 #20230724 David add retry
	if res != "":
		while CP_IP == "" and retry < 3:
			for line in res.splitlines():
				if "inet " in line and "127.0.0.1" not in line:
					CP_IP = re.findall( r'[0-9]+(?:\.[0-9]+){3}', line)[0]
					ret = os.system(g_cmd_ping.format(CP_IP))
					if ret == 0:
						sendlog("Get_CP_IP IP = {0}".format(CP_IP),"PASS")
						break
			retry += 1
	
	###send HWKEY bin to console
	send_file_to_console(CP_IP,key_file_bin,g_cp_tmp)
	
	# Do Fuse Certification
	ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_cerberus_prov_import.format(cert_idx, key_file_bin_soc), 5, log_path)
	if ret != 0:
		sendlog("Execute cerberus importsignedcert fail!DBG:{0}".format(res))
		return False
	else:
		sendlog("Execute cerberus importsignedcert PASS!DBG:{0}".format(res))
	
	#Disconnect other device
	if disconnect_cp_by_rm(ssh_object, sn_info_list) == 1:
		return 1
		
	return True
	
#*****************************************************************************
# Function   : cfg_parser_file()
# Description: parser the file and return config
# Inputs     : file
# Outputs    : config of file
# Notice     : None
#*****************************************************************************
def cfg_parser_file(fullpath):
	cfg = dict()
	sub_cfg = dict()
	section = ""
	# Sai add 20211015 
	if not os.path.isfile(fullpath):
		sendlog("[ Unknown Patch for key ] : {0} ".format(fullpath))
		return 1	
	
	with open(fullpath) as f:
		for line in f:
			if "CERBERUSSN" in line or "PUBLICKEY" in line:
				if '=' in line or ':' in line:
					if '=' in line:
						pos_equal = line.find('=')  #find first '=', maybe someday the value contain '='
					elif ':' in line:
						pos_equal = line.find(':')  #find first ':', maybe someday the value contain ':'
					key = line[0:pos_equal].strip()
					val = line[pos_equal+1:].strip()	
					if section:
						sub_cfg.setdefault(key,val)
					else:
						cfg.setdefault(key, val)	
			elif "HWKEY1" in line or "HWKEY2" in line or "HWKEY3" in line:
				if '=' in line or ':' in line:
					if '=' in line:
						pos_equal = line.find('=')  #find first '=', maybe someday the value contain '='
					elif ':' in line:
						pos_equal = line.find(':')  #find first ':', maybe someday the value contain ':'
					key = line[0:pos_equal].strip()
					val = line[pos_equal+1:].strip()
					if val == "":	
						sendlog("[{0}]Provsion key is null.".format(fullpath))
						return 1

					while "-----END CERTIFICATE-----" not in line:
						val += next(f).strip()
						if "-----END CERTIFICATE-----" in val:
							break
					if section:
						sub_cfg.setdefault(key,val)
					else:
						cfg.setdefault(key, val)
			else:
				try:
					sub_cfg[key] += "|{0}".format(line.strip())
				except:
					print (fullpath)
					print (key)
					print (line)
					print (sub_cfg[key])
					#save to log
					sendlog("[Unknown]fullpath:{0},key:{1},line:{2},sub_cfg[key]:{3}.".format(fullpath,key,line,sub_cfg[key]))
	
	return cfg
	
#*****************************************************************************
# Function	 : soc_fw_chk_and_reconfig_cp_chk
# Description: do SoC FW check and reconfig CP check 
# Inputs	 : sn_info_list: SN list information
# Outputs	 : 0: PASS
#			 : 1: FAIL
# Notice	 : NA
#*****************************************************************************
def soc_fw_chk_and_reconfig_cp_chk(sn_info_list):

	
	if sn_info_list["is_reconfig"]:
		sendlog(sn_info_list["sn"] + " reconfig finish")
		return 0
	print("start to do soc fw chk and then reconfig!!")	

	sn_log_folder = "{0}/{1}".format(g_log_folder, sn_info_list["sn"])
	log_name = "{0}_update_flag.log".format(sn_info_list["sn"])
	update_flag = "{0}/{1}".format(sn_log_folder, log_name)
	
	rm_flag_name = "{0}_rm_update_flag.log".format(sn_info_list["RACKSN"])
	rm_updated_flag = "{0}/{1}".format(g_log_folder, rm_flag_name)
	
	##enhance flow
	updating_log_name = "{0}_updating.log".format(sn_info_list["sn"])
	updating_flag = "{0}/{1}".format(sn_log_folder, updating_log_name)

	
	try:
		os.makedirs(sn_log_folder)
		sendlog("make log folder ({0}) success".format(sn_log_folder), GREEN)
	except OSError as e:
		if e.errno == errno.EEXIST:
			sendlog("log folder ({0}) exist".format(sn_log_folder), GREEN)
		else:
			sendlog("{0}".format(e))
			return 1
	
	if not os.path.isfile(updating_flag):
		os.system("touch {0}".format(updating_flag))
		if sn_info_list["STATION"] == "PRETEST":
			if sn_info_list["LOCATION"] == sn_info_list["master_rm_port"]:
				ret=update_rm_fw(sn_info_list)
				if ret == 0:
					os.system("touch {0}".format(rm_updated_flag))
			else:
				while not os.path.isfile(rm_updated_flag):
					print("rm_updated_flag:{0}".format(rm_updated_flag))
					sendlog("RACKSN:{0};SN:{1} waiting for Master UUT upload RM FW~~~~~~~~~".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
					time.sleep(60)
								
		if not os.path.isfile(update_flag):
			if sn_info_list["STATION"] == "PRETEST":
				log_type="START"
				message = "Start to do CP reconfig and update!"
				start_time=time.strftime("%Y%m%d%H%M%S")
				log_file =""
				send_data_sf(start_time,message, log_type, sn_info_list["sn"], sn_info_list["LOCATION"], sn_info_list["STATION"], log_file)
				##about 8 minutes 
				if not is_provision(sn_info_list):
					if do_cp_provision(sn_info_list) != 0:
						clear_flag(sn_info_list)
						return 1
				prov_log_name = "{0}_cp_prov_import.log".format(sn_info_list["sn"]) #20230822 David add for no prov
				prov_log_path = "{0}/{1}".format(sn_log_folder, prov_log_name)
				if not os.path.isfile(prov_log_path):
					prov_ret = is_provision(sn_info_list) #20230830 David fix
					if not prov_ret:
						clear_flag(sn_info_list)
						return 1
				print("CP is provision! Start to do soc fw chk and active CP in SOC update~~~")
		
				if do_soc_fw_chk(sn_info_list) != 0:
					sendlog("do_soc_fw_chk FAIL !")
					clear_flag(sn_info_list)
					return 1
				print("CP SOC is right FW version~~~")
				
				if do_cp_fpga_upgrade (sn_info_list) != 0:
					clear_flag(sn_info_list)
					return 1
				print("CP FPGA is right FW version~~~")
		
				log_type="FINISH"
				message = "CP reconfig and update FINISH!"
				start_time=time.strftime("%Y%m%d%H%M%S")
				log_file =""
				send_data_sf(start_time,message, log_type, sn_info_list["sn"], sn_info_list["LOCATION"], sn_info_list["STATION"], log_file)
		#if do_record_cp_and_reconfig(sn_info_list) != 0:
		#	sendlog("do_record_cp_and_reconfig FAIL !")
		#	clear_flag(sn_info_list)
		#	return 1
		#20230824 David modify to check network again
		sendlog("get uut ip: [{0}]{1}".format(sn_info_list["LOCATION"],sn_info_list["sn"]))
		sn_info_list["uut_ip"] = get_ip(sn_info_list["uut_mac_addr"])

		#Check reconfig flag
		if sn_info_list["uut_ip"] == 1 or sn_info_list["uut_ip"] == "":			
			if do_record_cp_and_reconfig(sn_info_list) != 0:
				sendlog("do_record_cp_and_reconfig FAIL !")
				clear_flag(sn_info_list)
				return 1
		else:
			sendlog("APP mode, don't need to do_record_cp_and_reconfig")
		print("Finish Do_record_cp_and_reconfig~~~~")
		os.system("rm -rf {0}".format(updating_flag))
	else:
		check_flag(sn_info_list)
		sendlog("[RACKSN:{0} SN:{1}]doing update~~~".format(sn_info_list["RACKSN"],sn_info_list["sn"]), GREEN)


#*****************************************************************************
# Function	 : check_sf_and_soc_fw_chk_and_reconfig_cp_chk
# Description: check sf config and do SoC FW check and reconfig CP check 
# Inputs	 : sn_info_list: SN list information
# Outputs	 : 0: PASS
#			 : 1: FAIL
# Notice	 : 20230829 David add
#*****************************************************************************
def check_sf_and_soc_fw_chk_and_reconfig_cp_chk(sf_file_list):
	sn_info_list = read_sn_info_from_config(sf_file_list)
	if sn_info_list != 1:
	
		if sn_info_list["is_reconfig"]:
			sendlog(sn_info_list["sn"] + " reconfig finish")
			return 0
		print("start to do soc fw chk and then reconfig!!")	

		sn_log_folder = "{0}/{1}".format(g_log_folder, sn_info_list["sn"])
		log_name = "{0}_update_flag.log".format(sn_info_list["sn"])
		update_flag = "{0}/{1}".format(sn_log_folder, log_name)
		
		rm_flag_name = "{0}_rm_update_flag.log".format(sn_info_list["RACKSN"])
		rm_updated_flag = "{0}/{1}".format(g_log_folder, rm_flag_name)
		
		##enhance flow
		updating_log_name = "{0}_updating.log".format(sn_info_list["sn"])
		updating_flag = "{0}/{1}".format(sn_log_folder, updating_log_name)

		
		try:
			os.makedirs(sn_log_folder)
			sendlog("make log folder ({0}) success".format(sn_log_folder), GREEN)
		except OSError as e:
			if e.errno == errno.EEXIST:
				sendlog("log folder ({0}) exist".format(sn_log_folder), GREEN)
			else:
				sendlog("{0}".format(e))
				return 1
		
		if not os.path.isfile(updating_flag):
			os.system("touch {0}".format(updating_flag))
			if sn_info_list["STATION"] == "PRETEST":
				if sn_info_list["LOCATION"] == sn_info_list["master_rm_port"]:
					ret=update_rm_fw(sn_info_list)
					if ret == 0:
						os.system("touch {0}".format(rm_updated_flag))
				else:
					while not os.path.isfile(rm_updated_flag):
						print("rm_updated_flag:{0}".format(rm_updated_flag))
						sendlog("RACKSN:{0};SN:{1} waiting for Master UUT upload RM FW~~~~~~~~~".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
						time.sleep(60)
									
			if not os.path.isfile(update_flag):
				if sn_info_list["STATION"] == "PRETEST":
					log_type="START"
					message = "Start to do CP reconfig and update!"
					start_time=time.strftime("%Y%m%d%H%M%S")
					log_file =""
					send_data_sf(start_time,message, log_type, sn_info_list["sn"], sn_info_list["LOCATION"], sn_info_list["STATION"], log_file)
					##about 8 minutes 
					if not is_provision(sn_info_list):
						if do_cp_provision(sn_info_list) != 0:
					 		clear_flag(sn_info_list)
					 		return 1
					prov_log_name = "{0}_cp_prov_import.log".format(sn_info_list["sn"]) #20230822 David add for no prov
					prov_log_path = "{0}/{1}".format(sn_log_folder, prov_log_name)
					if not os.path.isfile(prov_log_path):
					 	prov_ret = is_provision(sn_info_list) #20230830 David fix
					 	if not prov_ret:
					 		clear_flag(sn_info_list)
					 		return 1
					print("CP is provision! Start to do soc fw chk and active CP in SOC update~~~")
			
					if do_soc_fw_chk(sn_info_list) != 0:
						sendlog("do_soc_fw_chk FAIL !")
						clear_flag(sn_info_list)
						return 1
					print("CP SOC is right FW version~~~")
					
					if do_cp_fpga_upgrade (sn_info_list) != 0:
						clear_flag(sn_info_list)
						return 1
					print("CP FPGA is right FW version~~~")
			
					log_type="FINISH"
					message = "CP reconfig and update FINISH!"
					start_time=time.strftime("%Y%m%d%H%M%S")
					log_file =""
					send_data_sf(start_time,message, log_type, sn_info_list["sn"], sn_info_list["LOCATION"], sn_info_list["STATION"], log_file)
			#if do_record_cp_and_reconfig(sn_info_list) != 0:
			#	sendlog("do_record_cp_and_reconfig FAIL !")
			#	clear_flag(sn_info_list)
			#	return 1
			#20230824 David modify to check network again
			sendlog("get uut ip: [{0}]{1}".format(sn_info_list["LOCATION"],sn_info_list["sn"]))
			sn_info_list["uut_ip"] = get_ip(sn_info_list["uut_mac_addr"])

			#Check reconfig flag
			if sn_info_list["uut_ip"] == 1 or sn_info_list["uut_ip"] == "":			
				if do_record_cp_and_reconfig(sn_info_list) != 0:
					sendlog("do_record_cp_and_reconfig FAIL !")
					clear_flag(sn_info_list)
					return 1
			else:
				sendlog("APP mode, don't need to do_record_cp_and_reconfig")
			print("Finish Do_record_cp_and_reconfig~~~~")
			os.system("rm -rf {0}".format(updating_flag))
		else:
			check_flag(sn_info_list)
			sendlog("[RACKSN:{0} SN:{1}]doing update~~~".format(sn_info_list["RACKSN"],sn_info_list["sn"]), GREEN)
		
##############################	   MAIN		############################### 
if __name__ == "__main__":

	try:
		os.makedirs(g_log_folder)
		sendlog("make log folder ({0}) success".format(g_log_folder), GREEN)
	except OSError as e:
		if e.errno == errno.EEXIST:
			sendlog("log folder ({0}) exist".format(g_log_folder), GREEN)
		else:
			sendlog("{0}".format(e))
			sys.exit(1)

	show_info()

	if build_side != "QMF":			
		while True:
			p = ""
			sn_info_list = []

			#20230829 David add ##########################################################################
			sf_file_list = []
			if not os.path.isdir(g_win_config_folder):
				sendlog("{0} not found.".format(g_win_config_folder), RED)
				sys.exit(1)
			
			info = os.listdir(g_win_config_folder)
			for file_name in info:
				if ".txt" in file_name:
					sf_file_list.append(file_name)

			for i in range(len(sf_file_list)):
				p = Process(target=check_sf_and_soc_fw_chk_and_reconfig_cp_chk, args=(sf_file_list[i],))
				if p != "":
					p.start()
				if i != 0 and i%11 == 0: #20230829 David add prevent server busy
					time.sleep(10)
			#20230829 David add END#######################################################################

		
			# if get_sn_info_from_config(sn_info_list) != 0:
			# 	sendlog("get_sn_info_from_config Fail", "FAIL")
			# else:
			# 	for i in range(len(sn_info_list)):
			# 		print("=====================================")
			# 		print("len(sn_info_list):{0}".format(len(sn_info_list)))
			# 		print("=====================================")
			# 		####this line is for sequence  test !#####
			# 		#soc_fw_chk_and_reconfig_cp_chk(sn_info_list[i])
			# 		############################################
			# 		####below is for in-parallel test !!#####			
			# 		p = Process(target=soc_fw_chk_and_reconfig_cp_chk, args=(sn_info_list[i],))
			# 		if p != "":
			# 			p.start()
			# 		if i == 11: #20230728 David add prevent server busy
			# 			time.sleep(20)
			# 		############################################	
			
			time.sleep(600)
			print("==============next loop for cp_reconfig===================")
			print("==============next loop for cp_reconfig===================")
			print("==============next loop for cp_reconfig===================")
			os.system("cp -f /var/lib/dhcpd/dhcpd.leases /project/ ")
	else:
		p = ""
		sn_info_list = []

		#20230829 David add ##########################################################################
		sf_file_list = []
		if not os.path.isdir(g_win_config_folder):
			sendlog("{0} not found.".format(g_win_config_folder), RED)
			sys.exit(1)
		
		info = os.listdir(g_win_config_folder)
		for file_name in info:
			if ".txt" in file_name:
				sf_file_list.append(file_name)

		for i in range(len(sf_file_list)):
			p = Process(target=check_sf_and_soc_fw_chk_and_reconfig_cp_chk, args=(sf_file_list[i],))
			if p != "":
				p.start()
			if i != 0 and i%11 == 0: #20230829 David add prevent server busy
				time.sleep(10)
		#20230829 David add END#######################################################################
	

		# if get_sn_info_from_config(sn_info_list) != 0:
		# 	sendlog("get_sn_info_from_config Fail", "FAIL")
		# else:
		# 	for i in range(len(sn_info_list)):
		# 		print("=====================================")
		# 		print("len(sn_info_list):{0}".format(len(sn_info_list)))
		# 		print("=====================================")
		# 		####this line is for sequence  test !#####
		# 		#soc_fw_chk_and_reconfig_cp_chk(sn_info_list[i])
		# 		############################################
		# 		####below is for in-parallel test !!#####			
		# 		p = Process(target=soc_fw_chk_and_reconfig_cp_chk, args=(sn_info_list[i],))
		# 		if p != "":
		# 			p.start()
		# 		############################################	
		os.system("cp -f /var/lib/dhcpd/dhcpd.leases /project/ ")
		sys.exit(0)
