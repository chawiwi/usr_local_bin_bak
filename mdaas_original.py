# -*- coding: utf-8 -*-
# Copyright (C) 2019 Quanta Computer, Inc.
#
# This file is confidential and a trade secret of Quanta Computer, Inc.
# The receipt of or possession of this file does not convey any rights
# to reproduce or disclose its contents or to manufacture, use, or sell
# anything it may describe, in whole, or in part, without the specific
# written consent of Quanta Computer, Inc.
#
# File: mdaas.py
# Author: Jason.Cheng
# Date: 2021-04-14
# 

import sys
import os
import time
import subprocess
import threading
import shutil
import json
import traceback
import logging
import threading
import logging
import re
import glob
import requests as rq
import offline_upload_mdaas

# 0.4 change station indivdually
# 0.5 add try/except 
# 0.6 add mdaas change linux to winpe(ipxe)
# 0.7 add dimm screening mdaas
# 0.8.1 modify flow
# 0.8.1.1 fix can not get MDAAS status
mdaas_version = "0.8.1.1"
working_dir = "/mdaas"
win_dir = "/WIN"
tftp_location = "/tftpboot"
ipxe_location = "/home/container/ipxe"
station_list = ['MDAAS', 'FST', 'NETTEST']
mdaas_status = ['not started', 'starting', 'running', 'finishing', 'finished', 'crashed', 'exception']
mst_station = "DIMMSCREEN"

ESC_GREEN="\033[32m"
ESC_RED="\033[31m"
ESC_YELLOW_F="\033[33;1m"
ESC_YELLOW="\033[33m"
ESC_PINK="\033[35m"
ESC_LBLUE="\033[36m"
ESC_OFF="\033[0m"


#ADJUST TO GET IP AND RETRY COUNT
def get_txt_info(location):
	info = ""
	if not os.path.exists(location):
		logging.error ("Cannot get the file, path = {0}".format(location))
		return None

	fp = open(location, "r")
	info = fp.readlines()
	fp.close()
	return info

def getresult(arg1):
	p = subprocess.Popen(arg1, stdout=subprocess.PIPE, shell=True, text=True)
	(text, err) = p.communicate()
	return text

def sendlog(message,colour = 0):
	if colour == 1 :
		ESC_COLOUR = ESC_GREEN
	elif colour == 2 :
		ESC_COLOUR = ESC_RED
	elif colour == 3 :
		ESC_COLOUR = ESC_YELLOW
	elif colour == 4 :
		ESC_COLOUR = ESC_PINK
	elif colour == 5 :
		ESC_COLOUR = ESC_YELLOW_F
	elif colour == 6 :
		ESC_COLOUR = ESC_LBLUE
	else:
		ESC_COLOUR = ESC_OFF
		
	if colour == "PASS" or colour == "FAIL":
		if colour == "PASS":
			ESC_COLOUR = ESC_GREEN
		else :
			ESC_COLOUR = ESC_RED
		logging.info(str(message)+"........................."+ESC_COLOUR+"["+colour+"]"+ESC_OFF)
	else:
		logging.info(ESC_COLOUR+str(message)+ESC_OFF)
	cmd = ("echo '{0} ====>> {1}' >>{2}".format(time.strftime("%m-%d-%y-%H:%M:%S"), message, mdaas_dir+"/monitor.log"))
	os.system(cmd)

def get_set_start_time(running_flag):
	if not os.path.exists(running_flag):
		if not os.path.exists(os.path.dirname(running_flag)):
			os.makedirs(os.path.dirname(running_flag))
		start_time = time.strftime("%Y%m%d%H%M%S")
		with open(running_flag, mode="wt") as f:
			f.write("STARTTIME={0}".format(start_time))
		f.close()
		
	time.sleep(1)
	info = get_txt_info(running_flag)
	start_time = info[0].split("=")[1]
	return start_time

def check_start_time_flag(log_type, sf_sn):
	running_flag = "{0}/MDAAS/{1}".format(running_flag_dir, sf_sn)

	if log_type.upper() == "PASS" or log_type.upper() == "FAIL":
		os.system("rm -f {0}/{1}.txt".format(mdaas_dir, sf_sn))
		os.system("rm -f " + running_flag)

def send_data_sf(message, log_type, sf_sn, mdaas_mode, start_time):
	st_file = "{0}/{1}.ST".format(working_dir, sf_sn)
	win_st_file = "{0}/{1}.ST".format(win_status, sf_sn)
	location = find_location(sf_sn)
	if "mst" in mdaas_mode:
		station = "DIMMSCREEN"
	else:
		station = "MDAAS"

	with open(st_file, mode="wt") as f:
		f.write("SERIAL={0}\n".format(sf_sn))
		f.write("ERRORS={0}\n".format(message))
		f.write("STATUS={0}\n".format(log_type))
		f.write("LOCATI={0}\n".format(location))
		f.write("STATIO={0}\n".format(station))
		#f.write("LOGFIL={0}\n".format(log_file))
		f.write("STARTT={0}\n".format(start_time))
		f.close()
	
	shutil.copyfile(st_file, win_st_file)
	retryc = 10
	count = 0
	if not os.path.exists(win_st_file) or count > retryc:
		shutil.copyfile(st_file, win_st_file)
		count += 1
	
	#shutil.copyfile(st_file, '{0}/{1}/request/mac/{2}.ST'.format(win_dir, project, sf_sn))
	# os.system("chmod 777 {0}/{1}/request/mac/{2}.ST".format(win_dir, project, sf_sn))
	os.system("rm -f {0}".format(st_file))

def send2sf(message, log_type, sf_sn, mdaas_mode):
	message = message.splitlines()[0] # add this to make sure no \r or \n in the end
	running_flag = "{0}/MDAAS/{1}.txt".format(running_flag_dir, sf_sn)
	start_time = get_set_start_time(running_flag)   #ADD
	send_data_sf(message, log_type, sf_sn, mdaas_mode, start_time)
	check_start_time_flag(log_type, sf_sn)
	

def find_location(sf_sn):
	sf_conf_file = "{0}/{1}.txt".format(win_response, sf_sn)
	info = get_txt_info(sf_conf_file)
	if info is not None:
		for line in info:
			if "LOCATION" in line:
				location = line.split("=")[1].strip()
				return location
	return "NA"

def find_uut_ip(text, uut_sn):
	uut_mac = ""
	# uut_sn = ""
	uut_ip = ""
	ip = ""
	for line in text:
		line = line.strip()
		for mac in line.split(","):
			# we have find_ip utility, it will return validate IP address
			# search_ip_cmd = "grep -i -B8 -A1 {0} /var/lib/dhcpd/dhcpd.leases | grep lease | sort | uniq".format(mac)
			search_ip_cmd = '/usr/local/bin/find_ip {0}'.format(mac)
			uut_ip = getresult(search_ip_cmd)  # .strip()
			# if it's ip format, we will have 4 sections
			if len(uut_ip.split('.')) == 4:
				uut_ip =  uut_ip.strip()
				log = "SN={0} MAC={1} IP={2}".format(uut_sn, mac, uut_ip)
				cmd = "ping -c 3 {0} > /dev/null".format(uut_ip)
				if os.system(cmd) == 0:
						sendlog(log)
						ip = uut_ip 
						running_flag = "{0}/MDAAS/{1}.txt".format(running_flag_dir, uut_sn)
						get_set_start_time(running_flag)
						break
				else: # ping fail
						logging.error("ping FAIL, SN={0}, IP={1}".format(uut_sn, uut_ip))
						ip = "NA"
			else:
				ip = "NA"
	return ip

def get_eth_mac(sf_sn):
	sf_conf_file = "{0}/{1}.txt".format(win_response, sf_sn)
	mac = getresult("cat {0} | grep -i 'ETH0'".format(sf_conf_file))
	mac = mac.split("=")[1].split(",")[0].strip()
	return mac

def check_in_mdaas(sf_sn, exp_station):
	sf_conf_file = "{0}/{1}.txt".format(win_response, sf_sn)
	if os.path.exists(sf_conf_file):
		station = getresult("cat {0} | grep -i 'station'".format(sf_conf_file))
		station = station.split("=")[1].strip()
		sendlog("{0} is in {1}".format(sf_sn, station))
		if station == exp_station: #  in MDAAS
			return True
		else:
			return False
	else:
		# SF config not exists
		return False

def goto_next_station(sf_sn):
	sf_conf_file = "{0}/{1}.txt".format(win_response, sf_sn)
	local_sf_file = "{0}/{1}_SF.txt".format(working_dir, sf_sn)
	os.system("cp {0} {1}".format(sf_conf_file, local_sf_file))

	if check_in_mdaas(sf_sn, station_list[0]):
		info = get_txt_info(sf_conf_file)
		next_station = station_list[1] # FST
		if "GEN8.1" in info:
			next_station = station_list[2] # NETTEST
		sendlog("{0} goto {1} station".format(sf_sn, next_station))
		cmd = "sed -i 's/STATION={0}/STATION={1}/g' {2}".format(station_list[0], next_station, local_sf_file)
		logging.debug(cmd)
		os.system(cmd)
		os.system("cp {0} {1}".format(local_sf_file, sf_conf_file))
		os.system("rm -f {0}".format(local_sf_file))
		return 0
	else:
		sendlog("{0} is not in {1} station".format(sf_sn, station_list[0]))
		os.system("rm -f {0}".format(local_sf_file))
		return 1

def mst_goto_pretest_station(sf_sn):
	sf_conf_file = "{0}/{1}.txt".format(win_response, sf_sn)
	local_sf_file = "{0}/{1}_SF.txt".format(working_dir, sf_sn)
	os.system("cp {0} {1}".format(sf_conf_file, local_sf_file))

	if check_in_mdaas(sf_sn, mst_station):		
		next_station = "PRETEST" 		
		sendlog("{0} goto {1} station".format(sf_sn, next_station))
		cmd = "sed -i 's/{0}/{1}/g' {2}".format(mst_station, next_station, local_sf_file)
		logging.debug(cmd)
		os.system(cmd)
		os.system("cp {0} {1}".format(local_sf_file, sf_conf_file))
		os.system("rm -f {0}".format(local_sf_file))
		return 0
	else:
		sendlog("{0} is not in {1} station".format(sf_sn, station_list[0]))
		os.system("rm -f {0}".format(local_sf_file))
		return 1

def change_ipxe_menu(uut_mac, original, next):
	uut_mac = uut_mac.lower()
	ipxe_file = "{6}/{0}-{1}-{2}-{3}-{4}-{5}_menu.ipxe".format(uut_mac[0:2], uut_mac[2:4], uut_mac[4:6], uut_mac[6:8], uut_mac[8:10], uut_mac[10:12], ipxe_location)
	cmd = "sed -i 's/set menu-default {0}/set menu-default {1}/' {2}".format(original, next, ipxe_file)
	logging.debug(cmd)
	os.system(cmd)

def mst_goto_diag_test(uut_mac):
	uut_mac = uut_mac.lower()
	ipxe_file = "{6}/{0}-{1}-{2}-{3}-{4}-{5}_menu.ipxe".format(uut_mac[0:2], uut_mac[2:4], uut_mac[4:6], uut_mac[6:8], uut_mac[8:10], uut_mac[10:12], ipxe_location)
	cmd = "rm -f {0}".format(ipxe_file)
	logging.debug(cmd)
	os.system(cmd)

def linux_goto_winpe_mdaas_test(uut_mac):
	uut_mac = uut_mac.lower()
	ipxe_file = "{6}/{0}-{1}-{2}-{3}-{4}-{5}_menu.ipxe".format(uut_mac[0:2], uut_mac[2:4], uut_mac[4:6], uut_mac[6:8], uut_mac[8:10], uut_mac[10:12], ipxe_location)
	cmd = "cp -rf {0}/menu.ipxe_MDAAS_WINDOWS {1}".format(ipxe_location, ipxe_file)
	logging.debug(cmd)
	os.system(cmd)

def winpe_goto_diag_test(uut_mac):
	uut_mac = uut_mac.lower()
	ipxe_file = "{6}/{0}-{1}-{2}-{3}-{4}-{5}_menu.ipxe".format(uut_mac[0:2], uut_mac[2:4], uut_mac[4:6], uut_mac[6:8], uut_mac[8:10], uut_mac[10:12], ipxe_location)
	cmd = "rm -f {0}".format(ipxe_file)
	logging.debug(cmd)
	os.system(cmd)

def change_image(mac):
	#tftp_default_file = "{0}/efidefault".format(tftp_location)
	mac = mac.upper()
	#To remove the MAC on tftpboot
	image_mac_file = "{6}/01-{0}-{1}-{2}-{3}-{4}-{5}".format(mac[0:2], mac[2:4], mac[4:6], mac[6:8], mac[8:10], mac[10:12], tftp_location)
	cmd = "rm -f {0}".format(image_mac_file)
	logging.debug(cmd)
	os.system(cmd)

def get_rm_ip(sf_sn):
	sf_conf_file = "{0}/{1}.txt".format(win_response, sf_sn)
	if os.path.exists(sf_conf_file):
		RACK_MOUNT_MAC = getresult("cat {0} | grep -i 'RACK_MOUNT_MAC1'".format(sf_conf_file))
		RACK_MOUNT_MAC = RACK_MOUNT_MAC.split("=")[1].strip()
		RACK_MOUNT_MAC_TRANS=(RACK_MOUNT_MAC[:2]+':'+RACK_MOUNT_MAC[2:4]+':'+RACK_MOUNT_MAC[4:6]+':'+RACK_MOUNT_MAC[6:8]+':'+RACK_MOUNT_MAC[8:10]+':'+RACK_MOUNT_MAC[10:12])
		RACK_MOUNT_MAC_TRANS = RACK_MOUNT_MAC_TRANS.lower()

		search_ip_cmd = "grep -i -B8 -A1 {0} /var/lib/dhcpd/dhcpd.leases | grep lease | sort | uniq".format(RACK_MOUNT_MAC_TRANS)
		ip = getresult(search_ip_cmd)
		if len(ip) >= 1:
			ip =  ip.strip().split("{")
			for line in ip:
				if line != "":
					line = line.split(" ")[1]
					log = "get_rm_ip  MAC = {0} IP ={1}".format(RACK_MOUNT_MAC_TRANS,line)
					sendlog(log)

					log = "Check RM Connection IP ={}".format(line)
					cmd = "ping -c 3 {}".format(line)
					if os.system(cmd) == 0:
						sendlog(log)
						return line
					else:
						continue
				else:
					break
		return 1

def reboot_uut(sf_sn):
	sf_conf_file = "{0}/{1}.txt".format(win_response, sf_sn)
	# Need to use RM to do power cycle
	rm_ip = get_rm_ip(sf_sn)
	location = getresult("cat {0} | grep -i 'LOCATION'".format(sf_conf_file)).split("=")[1].strip().replace("F", "")
	pwr_cmd = "set system reset -i {0}".format(location) #20220524 David modify
	ssh_cmd = "sshpass -p '$pl3nd1D' ssh -o 'StrictHostKeyChecking no' -o 'UserKnownHostsFile=/dev/null' root@{0} '{1}'".format(rm_ip, pwr_cmd)
	logging.debug(ssh_cmd)
	os.system(ssh_cmd)

def power_off_uut(sf_sn):#20220606 David add
	sf_conf_file = "{0}/{1}.txt".format(win_response, sf_sn)
	# Need to use RM to do power off
	rm_ip = get_rm_ip(sf_sn)
	location = getresult("cat {0} | grep -i 'LOCATION'".format(sf_conf_file)).split("=")[1].strip().replace("F", "")
	pwr_cmd = "set system off -i {0}".format(location) 
	ssh_cmd = "sshpass -p '$pl3nd1D' ssh -o 'StrictHostKeyChecking no' -o 'UserKnownHostsFile=/dev/null' root@{0} '{1}'".format(rm_ip, pwr_cmd)
	logging.debug(ssh_cmd)
	os.system(ssh_cmd)

def check_SF_flag(sf_sn):
	sf_conf_file = "{0}/{1}.txt".format(win_response, sf_sn)
	rack_sn = getresult("cat {0} | grep -i 'RACKSN'".format(sf_conf_file)).split("=")[1].strip()
	# FIXME: need to modify the flag path
	SF_flag = "{0}/{1}_mdaas.txt".format("test", rack_sn)

	if os.path.isfile(SF_flag):
		return True
	else:
		return False

def get_log_from_mdass(ip, mdaas_mode):
	cmd = "curl -k https://{0}:5003/mdaas/blob_list".format(ip)
	ret = getresult(cmd)
	log_list = ret.split("[")[1].split("]")[0].split(",")
	for log in log_list:
		log = log.strip().replace("\"", "")
		if "START.zip" in log or "END.zip" in log:
			cmd = "curl -k -O https://{0}:5003{1}".format(ip, log)
			logging.info(cmd)
			os.system(cmd)
			if "mst" in mdaas_mode:
				#/RACKLOG/t6ub/MDAAS/DIMM_SCREENING
				log_path = "/RACKLOG/{0}/MDAAS/DIMM_SCREENING/{1}".format(project.lower(), time.strftime("%Y%m%d"))
			else:
				#/RACKLOG/t6ub/MDAAS
				log_path = "/RACKLOG/{0}/MDAAS/{1}".format(project.lower(), time.strftime("%Y%m%d"))
			if not os.path.exists(log_path):
				os.system("mkdir -p {}".format(log_path))
			
			log_file = log.split("/")[-1]

			#Changed log name to include the MDAAS Mode
			try:
				os.system(f"cp {log_file} {log_path}/{mdaas_mode}_{log_file}") 
			except Exception as e:
				print (e)

			os.system("mv {0} {1}".format(log_file, log_path))

def query_mdaas_status(chs_sn, ip):
	query_cmd = "curl -k https://{0}:5003/mdaas/status".format(ip)
	logging.info(query_cmd)
	if ip != "NA" and ip != "":
		ret = getresult(query_cmd)
		if "status" not in ret:
			sendlog("Can not get MDAAS status")
			return 1
		temp = json.loads(ret)
		try:
			mdaas_mode = temp["detail"]["mdaas_mode"].strip()
		except KeyError:
			mdaas_mode = "Unknown"
		test_finish = False
		log = "MDAAS test"
		if "status" in temp:
			status = temp["status"].strip()
			logging.debug(f'mdaas status:{status}')
			if status == "finished":
				url = f"https://{ip}:5003/mdaas/configs" #Status return 200 for golden config ready 
				response = rq.get(url, verify = False)    	
				status_code = response.status_code
				if status_code == 200 and mdaas_mode == "L10__genconfig": #L10__genconfig is golden config generating step
					download_cmd = "cd /home/container/configs; curl -k https://{0}:5003/mdaas/configs -O -J".format(ip)
					logging.info(download_cmd)
					ret = getresult(download_cmd)
					time.sleep(1)
					mdaas_cmd = "curl -X POST -k https://{0}:5003/mdaas/workflow -H 'Content-Type: application/json' -d ".format(ip)
					mdaas_cmd = mdaas_cmd + "'{\"flow\": \"L10\", \"site\": \"QMF\"}'"
					logging.info(mdaas_cmd)
					ret = getresult(mdaas_cmd)
				elif mdaas_mode == "L10" or mdaas_mode == "windows":
					test_finish = True 
			elif status != "not started":
				progress = " {0}, {1}/{2}".format(temp["desc"], temp['current'], temp['items'])
				send2sf(log + progress, status.replace(" ", "").upper(), chs_sn, mdaas_mode)
			elif status == "not started":
				genconfig_cmd = "curl -X POST -k https://{0}:5003/mdaas/workflow -H 'Content-Type: application/json' -d ".format(ip)
				genconfig_cmd = genconfig_cmd + "'{\"genconfig_mode\": \"true\", \"site\": \"QMF\", \"flow\": \"L10\"}'"
				logging.info(genconfig_cmd)
				ret = getresult(genconfig_cmd)

		if test_finish:
			test_result = temp["test_result"].strip()
			azure_upload = temp["azure_upload"].strip() 
			azure = temp['detail'].get('azure')
			mdaas_mode = temp["detail"]["mdaas_mode"].strip() 

			logging.debug(f'test_result:{test_result}, azure_upload:{azure_upload}, azure:{azure}')
			
			if azure is None:
				return
			azure = azure.strip()

			# get MDaAS log
			get_log_from_mdass(ip, mdaas_mode)
			log = "MDAAS"
			if "passed" in test_result and "succeeded" in azure_upload and "up" in azure:  #PASS
				if "windows" not in mdaas_mode: # 20220524 David add	
					win_ipxe_file = "{0}/menu.ipxe_MDAAS_WINDOWS".format(ipxe_location)
					if not os.path.exists(win_ipxe_file):
						sendlog("{0} FINISH".format(log))
						send2sf("{0} FINISH".format(log), "PASS", chs_sn, mdaas_mode)
						check_start_time_flag("PASS", chs_sn)

						uut_mac = get_eth_mac(chs_sn)
						winpe_goto_diag_test(uut_mac)
						goto_next_station(chs_sn)
						power_off_uut(chs_sn)
					else:
						sendlog("{0} Linux FINISH, goto MDAAS windows test".format(log))
						uut_mac = get_eth_mac(chs_sn)	
						linux_goto_winpe_mdaas_test(uut_mac)
						reboot_uut(chs_sn)
				else:
					sendlog("{0} Windows FINISH".format(log))
					send2sf("{0} FINISH".format(log), "PASS", chs_sn, mdaas_mode)
					check_start_time_flag("PASS", chs_sn)

					uut_mac = get_eth_mac(chs_sn)
					# change_image(uut_mac)
					winpe_goto_diag_test(uut_mac)
					#change_ipxe_menu(uut_mac, "winpe", "diag")
					goto_next_station(chs_sn)
					#reboot_uut(chs_sn)
					power_off_uut(chs_sn)
			elif "mst" in mdaas_mode: # 20220601 David add (MST test result will not upload to Azure)	
				if 	"passed" in test_result:
					sendlog("{0} DIMMSCREEN FINISH".format(log))
					send2sf("{0} DIMMSCREEN FINISH".format(log), "PASS", chs_sn, mdaas_mode)
					check_start_time_flag("PASS", chs_sn)
					uut_mac = get_eth_mac(chs_sn)
					mst_goto_diag_test(uut_mac)
					mst_goto_pretest_station(chs_sn)
					reboot_uut(chs_sn)
				elif "fail" in test_result:
					check_start_time_flag("FAIL", chs_sn)
					fail_msg = ""
					for item in temp["history"]:
						if "fail" in item["status"]:
							fail_msg = fail_msg + item["err_msg"] + " "
					sendlog("{0} DIMMSCREEN FAIL, {1}".format(log, fail_msg))
					send2sf("{0} DIMMSCREEN FAIL, {1}".format(log, fail_msg), "FAIL", chs_sn, mdaas_mode)
				else:
					check_start_time_flag("FAIL", chs_sn)
					send2sf("Test result not expected", "FAIL", chs_sn, mdaas_mode)
			else:
				
				
				if "passed" in test_result and "succeeded" not in azure_upload:
					try:
						sendlog(f"{chs_sn} : curl_result : {ret}")
					except Exception as e:
						print (e)
					sendlog("{0} MDaaS Data Upload Failed - Attempting Retry ".format(chs_sn))
					send2sf("{0} MDaaS Data Upload Failed - Attempting Retry".format(chs_sn), "WARNING", chs_sn, mdaas_mode)
					result = get_log_from_mdass_and_upload(chs_sn, ip, mdaas_mode) 
					if result == 'PASS':
						if "windows" not in mdaas_mode:
							win_ipxe_file = "{0}/menu.ipxe_MDAAS_WINDOWS".format(ipxe_location)
							if not os.path.exists(win_ipxe_file):
								sendlog("{0} FINISH".format(log))
								send2sf("{0} FINISH".format(log), "PASS", chs_sn, mdaas_mode)
								check_start_time_flag("PASS", chs_sn)

								uut_mac = get_eth_mac(chs_sn)
								winpe_goto_diag_test(uut_mac)
								goto_next_station(chs_sn)
								power_off_uut(chs_sn)
							else:
								sendlog("{0} Linux FINISH, goto MDAAS windows test".format(log))
								uut_mac = get_eth_mac(chs_sn)	
								linux_goto_winpe_mdaas_test(uut_mac)
								reboot_uut(chs_sn)						
						else:
							sendlog("{0} FINISH - Data Uploaded by Offline".format(log))
							send2sf("{0} FINISH - Data Uploaded by Offline".format(log), "PASS", chs_sn, mdaas_mode)
							check_start_time_flag("PASS", chs_sn)
							uut_mac = get_eth_mac(chs_sn)
							winpe_goto_diag_test(uut_mac)
							goto_next_station(chs_sn)
							power_off_uut(chs_sn)
						
				elif "passed" in test_result and "up" not in azure:
					sendlog("{0} MDaaS Network Connection Failed - Attempting Retry ".format(chs_sn))
					send2sf("{0} MDaaS Network Connection Failed - Attempting Retry".format(chs_sn), "WARNING", chs_sn, mdaas_mode)
					result = get_log_from_mdass_and_upload(chs_sn, ip, mdaas_mode)
					if result == 'PASS':
						if "windows" not in mdaas_mode:
							win_ipxe_file = "{0}/menu.ipxe_MDAAS_WINDOWS".format(ipxe_location)
							if not os.path.exists(win_ipxe_file):
								sendlog("{0} FINISH".format(log))
								send2sf("{0} FINISH".format(log), "PASS", chs_sn, mdaas_mode)
								check_start_time_flag("PASS", chs_sn)

								uut_mac = get_eth_mac(chs_sn)
								winpe_goto_diag_test(uut_mac)
								goto_next_station(chs_sn)
								power_off_uut(chs_sn)
							else:
								sendlog("{0} Linux FINISH, goto MDAAS windows test".format(log))
								uut_mac = get_eth_mac(chs_sn)	
								linux_goto_winpe_mdaas_test(uut_mac)
								reboot_uut(chs_sn)						
						else:
							sendlog("{0} FINISH - Data Uploaded by Offline".format(log))
							send2sf("{0} FINISH - Data Uploaded by Offline".format(log), "PASS", chs_sn, mdaas_mode)
							check_start_time_flag("PASS", chs_sn)
							uut_mac = get_eth_mac(chs_sn)
							winpe_goto_diag_test(uut_mac)
							goto_next_station(chs_sn)
							power_off_uut(chs_sn)
				elif "fail" in test_result:
					check_start_time_flag("FAIL", chs_sn)
					fail_msg = ""
					for item in temp["history"]:
						if "fail" in item["status"]:
							fail_msg = fail_msg + item["err_msg"] + " "
					sendlog("{0} FAIL, {1}".format(log, fail_msg))
					send2sf("{0} FAIL, {1}".format(log, fail_msg), "FAIL", chs_sn, mdaas_mode)
				else:
					check_start_time_flag("FAIL", chs_sn)
					send2sf("Test result not expected", "FAIL", chs_sn, mdaas_mode)
					
				
				
				

def get_log_from_mdass_and_upload(chs_sn, ip, mdaas_mode):
	cmd = "curl -k https://{0}:5003/mdaas/blob_list".format(ip)
	ret = getresult(cmd)
	log_list = ret.split("[")[1].split("]")[0].split(",")
	files_to_upload = []
	for log in log_list:
		log = log.strip().replace("\"", "")
		if "START.zip" in log or "END.zip" in log:
			cmd = "curl -k -O https://{0}:5003{1}".format(ip, log)
			logging.info(cmd)
			os.system(cmd)
			log_file = log.split("/")[-1]
			files_to_upload.append(log_file)
	status_result = offline_upload_mdaas.upload_files(files_to_upload)
	result = ''
	if (len(status_result)>0):
		if ('FAIL' in status_result):
			sendlog("{0} MDaaS Data Upload Failed - Attempting Retry ".format(chs_sn))
			send2sf("{0} MDaaS Data Upload Failed WARNING".format(chs_sn), "WARNING", chs_sn, mdaas_mode)
			result = 'FAIL'
		else:
			result = 'PASS'

	for file in files_to_upload:
		os.system("rm {0}".format(file))

	return result


def monitor_by_blade(chs_sn):
	mac_file = mdaas_dir+"/"+chs_sn+".txt"
	# Get blade mac
	info = get_txt_info(mac_file)
	# Use mac to find UUT IP
	ip = find_uut_ip(info, chs_sn)
	# Use IP to query MDAAS status
	if ip == 'NA':
		file_time = os.path.getmtime(mac_file)
		# if file is 3 days older, then delete it.
		if (time.time() - file_time) /3600 > 24*3:
			os.unlink(mac_file)
	query_mdaas_status(chs_sn, ip)

def init_monitor():
	if not os.path.isdir(working_dir):
		os.system("mkdir -p " + working_dir)

	if not os.path.isdir(mdaas_dir):
		os.system("mkdir -p " + mdaas_dir)

	if not os.path.isdir(running_flag_dir):
		os.system("mkdir -p " + running_flag_dir)

def usage():
	print("{0}: <Project code>".format(sys.argv[0]))


if __name__ == "__main__":

	if len(sys.argv) == 1:
		usage()
		exit(1)

	if len(sys.argv) > 1:
		project = sys.argv[1]


	logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')	
	win_status = "{0}/{1}/status".format(win_dir, project)
	win_response = "{0}/{1}/response/config".format(win_dir, project)  # by project list?
	mdaas_dir = "{0}/{1}/MDAAS".format(win_dir, project) #"/SFC/{0}/response/MDAAS".format(project)
	running_flag_dir = "{0}/{1}/running_flag".format(win_dir, project)

	init_monitor()
	cmd = "ls {0}| egrep -i '\.txt'".format(mdaas_dir)
	try:
		ret = getresult(cmd).strip()
		if ret != "":
			for line in ret.split("\n"):
				chs_sn = line.split(".")[0]
				t = threading.Thread(target=monitor_by_blade, args=(chs_sn,))
				t.start()
				time.sleep(1)
	except Exception as e:
		error_class = e.__class__.__name__  #取得錯誤類型
		detail = e.args[0] #取得詳細內容
		cl, exc, tb = sys.exc_info() #取得Call Stack
		lastCallStack = traceback.extract_tb(tb)[-1] #取得Call Stack的最後一筆資料
		fileName = lastCallStack[0] #取得發生的檔案名稱
		lineNum = lastCallStack[1]  #取得發生的行號
		funcName = lastCallStack[2] #取得發生的函數名稱
		errMsg = "File \"{0}\", line {1}, in {2}: [{3}] {4}".format(fileName, lineNum, funcName, error_class, detail)
		sendlog (errMsg)