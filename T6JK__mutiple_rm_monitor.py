# Copyright (C) 2019 Quanta Computer, Inc.
#
# This file is confidential and a trade secret of Quanta Computer, Inc.
# The receipt of or possession of this file does not convey any rights
# to reproduce or disclose its contents or to manufacture, use, or sell
# anything it may describe, in whole, or in part, without the specific
# written consent of Quanta Computer, Inc.
#
# File: rm_monitor.py
# Author: Jason.Cheng
# Date: 2021-01-22
# 

from multiprocessing import Process
import sys
import getopt
import os
import time 
import subprocess
import ConfigParser

#####################
# RM related define #
#####################
g_rm_pass 		= "$pl3nd1D"
g_cmd_RM_info	=	"show manager info"
g_cmd_AC_cycle	=	"set manager port {} -i {}" #on/off /index
g_log_RM_info	=	"/tmp/show_manager_info.txt"

#################
# global define #
#################
prj_build_site = "QCI"
prj_logserver_name = "test"
prj_logserver_pw = "qcitest"
testlog_path = "/RACKLOG"
rm_ip = "UNDEFINE"
testlog_ip = ""
prj_name = ""
rm_path = ""

def get_single_info(info, key):
	log = ""
	for line in info:
		line = line.strip()
		key_word=key+"="
		if key_word in line :
			get_info = line.split("=")[1]
			log = "[{0}] = [{1}]".format(key,get_info)
			sendlog (log)
			return get_info
	sendlog("get_single_info: Cannot get [{0}] info, Please check it!!".format(key))
	return -1

def get_txt_info(location):
	info = ""
	log = ""
	if not os.path.exists(location):
		log = "get_txt_info: Cannot get location [{0}]..Please Check it!!".format(location)
		sendlog(log)
		return 1
		
	fp = open(location, "r")
	info = fp.readlines()
	fp.close()
	return info

def getresult(cmd):
	p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
	(text, err) = p.communicate()
	res = text
	return res

def sendlog(message):
	print message
	cmd = ("echo '{0} ====>> {1}' >>{2}".format(time.strftime("%m-%d-%y-%H:%M:%S"), message, rm_path+"/monitor/monitor.log"))
	os.system(cmd)

def option_usage():
	print "\n	-p: project name"
	print "\n	-i: rack manager IP"
	print "\n   -m: log server IP, and mount test_log"
	print ""

def mount_testlog():
	os.system('umount {} > /dev/null'.format(testlog_path))
	os.system("mkdir -p {}".format(testlog_path))
	time.sleep(1)
	if prj_build_site == "QCI":
		cmd = 'mount -tcifs //{}/testlog {} -ousername={},password={},rw,vers=1.0'.format(testlog_ip, testlog_path, prj_logserver_name, prj_logserver_pw)
	else:
		cmd = 'mount -tcifs //{}/test_log {} -ousername={},password={},rw,vers=1.0'.format(testlog_ip, testlog_path, prj_logserver_name, prj_logserver_pw)
	for i in range(0, 3):
		ret = os.system(cmd)
		if ret == 0:
			print "Mount test log server success"
			break
		elif i == 2:
			sendlog("Cannot mount test log server")
			sys.exit(1)

def do_ssh_connect(cmd, ip, sshpass, location ="/dev/null"):
	ret = 0
	if os.path.exists(location):
		os.system("rm -rf "+ location)
		
	cmd = "sshpass -p '{0}' ssh -o \"StrictHostKeyChecking no\" root@{1} \"{2}\" > {3}".format(sshpass, ip, cmd, location)
	sendlog(cmd)
	ret = os.system(cmd)
	return ret

def do_AC_cycle(port, act):
	if port != "":
		cmd = g_cmd_AC_cycle.format(act, port)
		ret = do_ssh_connect(cmd, rm_ip, g_rm_pass)
		log = "Do AC cycle on {}'s port={}, action={}".format(rm_ip,port,act)
		if ret != 0:
			sendlog(log + "...... [FAIL]")
		sendlog(log + "...... [PASS]")
		return 0
	return 1

if __name__ == "__main__":

	# Get parameter
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hi:p:m:") # , ["rm_ip=","prj_name="]
	except getopt.GetoptError:
		print 'rm_monitor -i <RM IP> -p <project name>'
		sys.exit(1)
	for opt, arg in opts:
		if opt == '-h':
			option_usage()
			sys.exit(1)
		elif opt == "-i":
			rm_ip = arg
		elif opt == "-p":
			prj_name = arg
		elif opt == "-m":
			testlog_ip = arg
			mount_testlog()
		else:
			option_usage()
			sys.exit(1)
        ###DELAY TIME
	# if prj_name != "" and rm_ip != "":
	if prj_name != "":
		rm_path = "{}/{}/rm".format(testlog_path, prj_name)
		if not os.path.exists(rm_path):
			os.system("mkdir -p " + rm_path)

	# Find file
	while True:
		print "ls -al {0} | grep -i '.txt' | wc -l".format(rm_path)
		flag_cnt = getresult("ls -al {0} | grep -i '.txt' | wc -l".format(rm_path))
		if  int(flag_cnt.strip()):
			cmd = "ls -al {0} | grep -i '.txt' | tail -1 ".format(rm_path)
			print "======================================="
			info = getresult(cmd).strip()
			print cmd
			print info
			print "======================================="
			if len(info) > 10:
				# get config file with UUT request
				file_name = info.split(" ")[-1]
				print file_name
				print rm_path
				act_file = rm_path + "/" + file_name
				print act_file
				content = get_txt_info(act_file)
				if content != 1:
					action = get_single_info(content, "ACTION")
					uut_port = get_single_info(content, "PORT")
					rm_ip = get_single_info(content, "RMIP")
					delay_time = 10
					if delay_time != "":
						print "Sleep {} seconds, then do {}".format(delay_time, action)
						time.sleep(int(delay_time))
					if action == "AC_CYCLE" and uut_port != -1:
						p = Process(target = do_AC_cycle, args = (uut_port, "ON"))
						p.start()
						time.sleep(5)
						sendlog("AC On sucess, remove {}".format(act_file))
						os.system("rm {0}".format(act_file))
				else :
					sendlog("NO content in {}".format(act_file))
					os.system("rm {0}".format(act_file))
			time.sleep(5)
		else:
			break
