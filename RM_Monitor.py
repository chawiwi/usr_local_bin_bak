# Copyright (C) 2019 Quanta Computer, Inc.
#
# This file is confidential and a trade secret of Quanta Computer, Inc.
# The receipt of or possession of this file does not convey any rights
# to reproduce or disclose its contents or to manufacture, use, or sell
# anything it may describe, in whole, or in part, without the specific
# written consent of Quanta Computer, Inc.
#
# File: T6R_RM_Monitor.py
# Author: Sai.Goh
# Date: 2020-08-07
# 
# 
from multiprocessing import Process
import sys
import os
import time 
import subprocess
import logging
# import ConfigParser

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

ON 				= "on"
OFF 			= "off"

ACTION 			= "ACTION"
ACTION_AC_CYCLE = "AC_CYCLE"

###############
##RM command define
###############
g_rm_pass 		= "$pl3nd1D"

g_cmd_RM_info	=	"show manager info"
g_cmd_AC_Cycle	=	"set manager port {0} -i {1}"#on/off /index
g_cmd_DC_Cycle	=	"set system -i {0}"
g_log_RM_info	=	"/tmp/show_manager_info.txt"


###############
##RM command define
###############

def getresult(arg1):

	p = subprocess.Popen(arg1, stdout=subprocess.PIPE, shell=True)
	(text, err) = p.communicate()
	res = text.decode(errors='ignore')
	
	return res


def get_rm_ip(RACK_MOUNT_MAC):	
	ip = "" 	
	log = "get_rm_ip"
	RACK_MOUNT_MAC_TRANS=(RACK_MOUNT_MAC[:2]+':'+RACK_MOUNT_MAC[2:4]+':'+RACK_MOUNT_MAC[4:6]+':'+RACK_MOUNT_MAC[6:8]+':'+RACK_MOUNT_MAC[8:10]+':'+RACK_MOUNT_MAC[10:12])
	RACK_MOUNT_MAC_TRANS = RACK_MOUNT_MAC_TRANS.lower()
	serch_ip_cmd = "grep -B8 -A1 {0} /var/lib/dhcpd/dhcpd.leases | grep lease".format(RACK_MOUNT_MAC_TRANS)
	#serch_ip_cmd = "grep -B6 -A1 {0} /mnt/smbfs/sai_project/dhcpd.leases | grep lease".format(RACK_MOUNT_MAC_TRANS)
	ip = getresult(serch_ip_cmd)
	log = "get_rm_ip MAC = {0}  IP ={1}".format(RACK_MOUNT_MAC_TRANS,ip)
	if len(ip) >= 1 : 
		ip =  ip.strip().split("{")
		for line in ip:
			#sai 2022/01/05 add for fix crash issue 
			if " " in line :
				line = line.split(" ")[1]
				
			log = "get_rm_ip  MAC = {0} IP ={1}".format(RACK_MOUNT_MAC_TRANS,line)
			if line != "" :
				logging.debug(log)
				log = "Check RM Connection IP ={0}".format(line)
				cmd = "ping -c 3 {0} > /dev/null 2>&1".format(line)
				if os.system(cmd) == 0:
					logging.debug(log)
					return line
				else:
					continue
			else:
				break
	logging.error(log)
	return 1

def do_ssh_connect(cmd,ip,sshpass,location ="NA"):
	ret = 0
	if os.path.exists(location) and location != "NA":
		os.system("rm -rf "+ location)
		
	cmd = "sshpass -p '{0}' ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null root@{1} \"{2}\"".format(sshpass,ip,cmd)
	logging.info(cmd)
	ret = getresult(cmd)
	#ret = os.system(cmd)
	return ret

def get_txt_info(location):
	info = ""
	log = ""
	if not os.path.exists(location):
		log = "get_txt_info ,Cant get location [{0}]..Please Check it!!".format(location)
		logging.error (log)
		return 1
		
	fp = open(location, "r")
	info = fp.readlines()
	fp.close()
	return info
	
def get_single_info(info,key):
	log = ""
	for line in info:
		line = line.strip()
		key_word=key+"="
		if key_word in line :
			get_info = line.split("=")[1]
			log = "[{0}] = [{1}]".format(key,get_info)
			logging.debug (log)
			return get_info
	logging.error ("get_single_info , Cannot get [{0}] info ,Please check it!!".format(key))
	return 1

def GET_UUT_RM_PORT(rm_ip,uut_mac):
	log = "" 
	mapping_info = ""
	server_ID = ""
	
	server_ID 		= "NA"
	port_state 		= "NA"
	present			= "NA"
	type 			= "NA"
	Completion_Code = "NA"
	
	do_ssh_connect(g_cmd_RM_info, rm_ip, g_rm_pass, g_log_RM_info)
	ret = get_txt_info(g_log_RM_info)
	
	for line in ret:
		line = line.strip()
		if uut_mac.upper() in line:
			uut_info 		= 	line.strip().split("| ")
			
			server_ID 		= 	uut_info[1].strip()
			port_state 		= 	uut_info[2].strip()
			present			= 	uut_info[3].strip()
			type 			= 	uut_info[4].strip()
			Completion_Code = 	uut_info[7].strip()
			break
			
		if uut_mac.lower() in line:
			uut_info 		= 	line.strip().split("| ")
			
			server_ID 		= 	uut_info[1].strip()
			port_state 		= 	uut_info[2].strip()
			present			= 	uut_info[3].strip()
			type 			= 	uut_info[4].strip()
			Completion_Code = 	uut_info[7].strip()
			break
			

			
	log = "Get server_ID=[{0}], port_state=[{1}], resent=[{2}], type=[{3}], Completion_Code=[{4}] ".format(server_ID,port_state,present,type,Completion_Code)
	if server_ID != "" and port_state == "ON" and present == "True" and type == "Server" and Completion_Code == "Success":
		logging.debug (log,PASS)
		return server_ID
				
	logging.error(log)
	return FAIL

def getSku():
	sku_info = "NA"
	global cable_mapping
	rackpn =  get_single_info(sf,"RACKPN")
	
	if not os.path.isfile(skufile):
		log = "Sku file [{0}]doesn\'t exist.".format(skufile)
		logging.error(log)
		sys.exit(1)
	info = get_txt_info(skufile)
	for get_info in info :
		if rackpn in get_info:
			sku_info = get_info.strip().split(' = ')[0]
			return sku_info

	log = "Cannot find RACKPN={0} in {1}".format(rackpn, skufile)
	logging.error(log)
	return sku_info
			
				 
	
	
def get_port_by_config(location):
	info = get_txt_info(cable_mapping)
	
	for line in info:
		# print(line)
		line = line.strip()
		config_location = line.split("-")[2]
		if location == config_location :
			get_info = line.split("-")[1]
			log = "[{0}] = [{1}]".format(config_location,get_info)
			logging.debug (log)
			return get_info
			
	logging.error ("Cannot get location [{0}] info.".format(location))
	return -1
	
def do_AC_Cycle(rm_ip, location):
	log = ""
	#port = GET_UUT_RM_PORT(rm_ip,uut_mac)
	port = get_port_by_config(location)
	log = "Get UUT port on RM "
	if port != FAIL and port != "":
		logging.info(log + "...............[PASS]")
		cmd = g_cmd_AC_Cycle.format("OFF", port)
		do_ssh_connect(cmd, rm_ip, g_rm_pass)
		time.sleep(10)
		ret = check_pwr_status_off(rm_ip,port)
		if ret != 0:
			for i in range(3):
				cmd = "set manager port {0} -i {1}".format("OFF", port)
				do_ssh_connect(cmd, rm_ip, g_rm_pass)
				time.sleep(10)
				ret = check_pwr_status_off(rm_ip, port)
				if ret == 0:
					break
				if i == 2:
					logging.error( "RM power off UUT-{0} FAIL".format(port))
					return 1

		time.sleep(240)	
		cmd = g_cmd_AC_Cycle.format("ON",port)
		do_ssh_connect(cmd,rm_ip, g_rm_pass)
		return 0
		
	logging.error(log + "...............[FAIL]")
	return 1

def check_pwr_status_on(rm_ip, locate_idx):
	cmd = "show system type -i {0}".format(locate_idx)
	stdout = do_ssh_connect(cmd, rm_ip, g_rm_pass)
	cmplt_code = stdout.split("Completion Code:")[-1].splitlines()[0].strip()
	if cmplt_code.upper() == "SUCCESS":
		return 1    #power on
	return 0    #power off

def check_pwr_status_off(rm_ip, locate_idx):
	cmd = "show system type -i {0}".format(locate_idx)
	logging.debug(cmd)
	stdout = do_ssh_connect(cmd, rm_ip, g_rm_pass)
	logging.debug(stdout)
	cmplt_code = stdout.split("Completion Code:")[-1].splitlines()[0].strip()
	logging.debug(cmplt_code)
	logging.debug("PORT-{0} cmplt_code={1}".format(locate_idx,cmplt_code))
	if cmplt_code.upper() == "DEVICEPOWEREDOFF":
		return 0    #power off
	return 1    #power on

def usage():
	print("{0}: <Project code>".format(sys.argv[0]))

	
##############################     MAIN     ###############################	
if __name__ == "__main__":
	
	log = ""
	ret = ""
	rm_ip = 1
	get_info = ""			

	if len(sys.argv) == 1:
		usage()
		exit(1)

	if len(sys.argv) > 1:
		project = sys.argv[1]
		# T6UB, T6UA_2U_MILAN etc.

	logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
	head_location 		= "/WIN/{0}/".format(project)
	#head_location		= "/WIN/"+project+"/"
	ccr_config			= head_location+'CCR/'
	skufile				= ccr_config+'sku.ini'

	cable_mapping		= ""
	sf_loc				= head_location+"response/config"
	monitor_loc 		= head_location+"windows/RM_ACTION/"

#	show_info()

	try:
		if not os.path.isdir(monitor_loc):
			os.makedirs(monitor_loc)
		#while cycle always loop Please dont change i
		#20220111 Jason: remove SSH key in the beginning
		# os.system("rm -rf /root/.ssh/known_hosts")
		
		#j = j+1
		# One time only get one 
		#print monitor_loc
		while True:
			cmd = "ls -al {0} | grep -i '.txt' | tail -1 ".format(monitor_loc)
			get_info = getresult(cmd)
			# print("Get Info = [" + get_info.strip() +"]")
			if len(get_info) > 10 :
					# Change permission already done in the swlog
					# os.system("chmod -R 666 {0}*".format(head_location))	
					get_info = get_info.strip()
					#get config file with SF and UUT request
					if ".txt" in get_info :  
							
							snfile =  get_info.split(" ")[-1]
							logging.info("snfile ="+snfile)
	
							check_file = monitor_loc+"/"+snfile
							uut_sf_file = sf_loc+"/"+snfile
			
							logging.debug("uut_sf_file = [{0}]".format(uut_sf_file))
							req = get_txt_info(check_file)
							sf = get_txt_info(uut_sf_file)
							
							if req == 1:
								fail_to_find = "Failed to find the corresponding RM_ACTION file at: {0}".format(check_file)
								logging.error(fail_to_find)
								
							# Doesn't matter Work or not just clear the file
							# os.system("rm -rf {0}*".format(check_file))
							os.unlink(check_file)
							
							# both of them get will go next step 
							if req != 1 and sf != 1:
									action = get_single_info(req,ACTION)
									if action == ACTION_AC_CYCLE:
											#uut_mac = get_single_info(sf,"ETH0")
											location = get_single_info(sf,"LOCATION")
											rm_mac = get_single_info(sf,"RACK_MOUNT_MAC1")
											sku_info = getSku()
											cable_mapping = "{0}rm_table_{1}.txt".format(ccr_config,sku_info)	
											if not os.path.isfile(cable_mapping):
													log = "RM config file [{0}]doesn\'t exist.".format(cable_mapping)
													logging.error(log, FAIL)
											else :
													if rm_mac != 1:
															rm_ip = get_rm_ip(rm_mac)
													if rm_ip != 1:
															p = Process(target=
															do_AC_Cycle, args=(rm_ip,location))
															p.start()
															# firing too much RM command in short time could stuck RM login
															time.sleep(5)
									else :
										logging.error("NOT Support Action = [{0}]".format(action))
					
			else:
				# no more txt files to process
				break
			info = ""
	
	except Exception as err:
		logging.error("Exception error: {}, line:{}".format(err, err.__traceback__.tb_lineno))
		
		
