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
# import configparser
# import shutil
import errno
# import commands
import re
#import paramiko
# import datetime
import base64

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
#Sai update 0.1.4 for support QMF 
#WeiKai update 2.0.5 for L15 L11
PASS			= "PASS"
FAIL			= "FAIL"
VERSION			= "2.0.5"
EDITOR			= "WeiKai"
RELEASE_DATE	= "2024/03/29"
#Sai modify location for QMF 
g_model = "MODEL"
g_project = "L15"
#QTMC####################
# g_log_folder = "/mnt/test_log/{0}/RM_logs".format(g_project.lower())
# g_mainlog_file = "{0}/monitor.log".format(g_log_folder)
# g_win_config_folder = "/win/{0}/response/config".format(g_project)
# g_win_prov_folder = "/win/{0}/keys/provisions".format(g_project)
# g_win_ccr_folder = "/win/{0}/CCR".format(g_project)
#########################
#QMF#####################
g_log_folder = "/RACKLOG/{0}/RM_logs".format(g_project.lower())
g_mainlog_file = "{0}/monitor.log".format(g_log_folder)
g_win_config_folder = "/WIN/{0}/response/config".format(g_project.upper())
g_win_prov_folder = "/WIN/{0}/keys/provisions".format(g_project.upper())
g_win_ccr_folder = "/WIN/{0}/CCR".format(g_project.upper())
#########################
g_dhcp_folder = ""
build_side = "QMF"
g_cp_tmp = "/tmp/"
#g_cp_FPGA_firmware="CelestialPeak_SysInt_4.1.1-70c6abd1_jic.rpd"
#g_cp_FPGA_firmware_loc="/project/firmware/{0}/{1}".format(g_project.lower(),g_cp_FPGA_firmware)
#QTMC####################
# tftp_ip = "172.51.0.1"
# tftp_user = "root"
# tftp_passwd = "2wsx@WSX"
#########################
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
#image_path = "firmware/Celestial_Peak/dropcp-2.15FW-stos2008.4.23031201/rMedia/"
rm_firmware_path = "firmware/{0}/RM/".format(g_project.lower())
#upgrade_image = "overlake-2008.4.23031201-prod.img"
upgrade_image = "overlake-{0}-prod.img"
#g_cp_Cerberus_fw="cerberus_v2.4.11.4.bin"
#g_cp_Cerberus_fw_loc="/project/firmware/{0}/cp/{1}".format(g_project.lower(),g_cp_Cerberus_fw)
g_overlake_md5sum = {"overlake-2008.6.23101601-prod.img":"784d222f1f8b233543be00c5c1c90bd3",
                     "overlake-2008.4.23031201-prod.img":"e46ab936432f817b4da8037239f44218",
                     "overlake-1908.5.22022401-prod.img":"06459d32386890fef25703de711f0fcb"}
replace_image_name = {"0002.17.240911-prd":["dropcp-2.17FW-stos2008.6.23101601","dropcp-2.17.1FW-stos2008.6.23101601"]}
replace_md5 = {"overlake-2008.6.23101601-prod.img":["784d222f1f8b233543be00c5c1c90bd3","e5075189b5e8cfdb0017e21a1d6b3d86"]}
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
g_cmd_del_tftp_file = "set manager tftp delete -f {0}"
g_cmd_install_catapult_driver = "modprobe catapult"
g_cmd_dumphealth = "fpgadiagnostics -dumpHealth"
g_cmd_reconfigGolden = "fpgadiagnostics -reconfigGolden"
g_cmd_reconfigapp = "fpgadiagnostics -reconfigApp"
g_cmd_fpgadiagnostics_list = "fpgadiagnostics -list"
g_cmd_show_system_state = "show system state -i {0}"
g_cmd_show_tftp = "show manager tftp list"
g_cmd_set_cmd = "set system cmd -i {0} -c {1}"
g_cmd_RM_FW_UPDATE = "set manager fwupdate -f {0}"
g_cmd_RM_FPGA_health = "show system fpga health -i {0}"
#####################
# RM Command Define #
#####################

#############################
# SoC Update Command Define #
#############################
g_cmd_get_soc_firmware_ver = "cat /proc/device-tree/firmware/version"
g_cmd_get_soc_nitro_firmware_ver = "cat /proc/device-tree/firmware/nitro-version"
g_cmd_get_soc_cerberus_firmware_ver = "cerberus_utility fwversion"
g_cmd_get_soc_os_ver = "cat /etc/os-release | grep 'VERSION_ID'"
g_cmd_copy_image_to_rm = "set manager tftp get -s {0} -f {1}/{2}"
g_cmd_mount_image_on_soc = "set system remotedrive mount -i {0} -b 1 -n {1}"
g_cmd_check_sda_exist = "lsblk | grep -i 'sda'"
g_cmd_set_bootmode_to_one = "bootmode set 1"
g_cmd_get_bootmode = "bootmode get"
g_cmd_reboot = "reboot"
g_cmd_socflash = "socflash"
g_cmd_mkdir_usb_folder = "mkdir -p /tmp/usb"
g_cmd_mount_usb_folder = "mount /dev/sda1 /tmp/usb"
g_cmd_check_bin_file_exist = "ls -al /tmp/usb"
#fip_pfm_file  = "A2040.FIP.PFM.46.bin"
#fip_fw_file = "fip.bin"
#nitro_pfm_file = "A2040.NITRO.PFM.46.bin"
#nitro_fw_file = "nitro.img"
#g_cmd_update_sop = ["cerberus_utility pfmupdate 0 /tmp/usb/{} 0".format(fip_pfm_file),
#                    "cerberus_utility socfwupdate 0 /tmp/usb/fip.bin 1",
#                    "cerberus_utility pfmupdate 1 /tmp/usb/{} 0".format(nitro_pfm_file),
#                    "cerberus_utility socfwupdate 1 /tmp/usb/nitro.img"]
g_cmd_cat_cp_logfile = "cat /tmp/cp_cmd.log"


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
g_cmd_search_ip_QTMC = "grep -B9 -A1 -i {0} /var/lib/dhcpd/dhcpd.leases | grep lease"
g_cmd_search_ip_QCI = "grep -B2 -A1 {0} /mnt/smbfs/__DHCP/dhcp2.txt | grep \"^192\" | awk -F \":\" '{{print $1}}'"
g_cmd_ping = "ping -c 3 {0}"
########################
# Other Command Define #
########################

############################
# Celestial Peak FW Define # #20230517 David: get from SFC
############################
# exp_soc_fw_ver = "0002.13.220324-prd"
# exp_soc_fw_nitro_ver = "0002.13.220324-prd"
############################
# Celestial Peak FW Define #
############################

####################################### #20231102 David add
# Celestial Peak Auto reconfig Define #
#######################################
auto_reconfig_service_server_loc = "/home/Monitor_reconfig_CP/SoCFPGATestSvc.service"
auto_reconfig_python_server_loc = "/home/Monitor_reconfig_CP/fpga.py"
auto_reconfig_service_soc_loc = "/vol/data/persistent/tests/systemd/SoCFPGATestSvc.service"
auto_reconfig_python_soc_loc = "/vol/data/persistent/tests/fpga.py"
auto_reconfig_soc_loc = "/vol/data/persistent/tests"
# g_cmd_remove_auto_reconfig = "rm -rf {}".format(auto_reconfig_service_soc_loc)
g_cmd_remove_auto_reconfig = "rm -rf /vol/data/persistent/tests"
g_cmd_copy_auto_service_to_loc_path = "cp -rf /tmp/SoCFPGATestSvc.service {}".format(auto_reconfig_service_soc_loc)
g_cmd_copy_auto_python_to_loc_path = "cp -rf /tmp/fpga.py {}".format(auto_reconfig_python_soc_loc)
g_cmd_find_auto_service = "find / -name *SoCFPGATestSvc.service*"
g_cmd_find_auto_python = "find / -name *fpga.py*"
g_cmd_mkdir_service_loc_path = "mkdir -p /vol/data/persistent/tests/systemd"
#######################################
# Celestial Peak Auto reconfig Define #
#######################################


#_*****************************************************************************
#_ Function   : gs_exec_cmd
#_ Description: Get the return value, stdout, stderr from input system command
#_ Inputs     : cmd: the command tobe execute
#_ Outputs    : return value, stdout, stderr from the result of input command
#_ Notice     : use subprocess.Popen(), no command result will show on screen
#_*****************************************************************************
def gs_exec_cmd(cmd):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout,stderr = p.communicate()
    output=stdout.strip()
    ret=p.returncode
    return ret,output.decode('utf-8'),stderr.decode('utf-8')
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

    # message = message.replace("'",'') #20230928 David add

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
    log_name = "{0}_update_flag.log".format(sn_info_list["CP_SN"])
    update_flag = "{0}/{1}".format(sn_log_folder, log_name)
    
    ##enhance flow
    updating_log_name = "{0}_updating.log".format(sn_info_list["sn"])
    updating_flag = "{0}/{1}".format(sn_log_folder, updating_log_name)
    
    #os.system("rm -rf {0}".format(update_flag))
    os.system("rm -rf {0}".format(updating_flag))
    sendlog("[RACKSN:{0} SN:{1}]update process fail! Clear all flag!".format(sn_info_list["RACKSN"],sn_info_list["sn"]), RED)
    

def check_version_in_log(sn_info_list, log_folder):
    
    uut_sn = sn_info_list["sn"]
    fpga_fw = sn_info_list["CP_GOLDEN_IMAGE"].split(',')[0]
    soc_fw = sn_info_list["CP_SOC_OS_FW"]
    cerberus_fw = sn_info_list["CP_CERBERUS_FW"]
    entrys = [ \
        {"pattern" : "\[FPGA-CONFIG-EX \].*", "version": fpga_fw, "path" : "chk_fpga_fw.log" }, \
        {"pattern" : "VERSION_ID=.*", "version": soc_fw, "path" : "chk_soc_fw.log" }, \
        {"pattern" : "Cerberus Version:.*", "version": cerberus_fw, "path" : "chk_soc_fw.log" }]
    
    file_list = []
    
    for entry in entrys:
        file_name = "{0}/{1}_{2}".format(log_folder, uut_sn, entry["path"])
        if os.path.exists(file_name) and time.time()-os.stat(file_name).st_mtime > 10800: #10800 = 3hours, align the timeout setting with check_flag.
            print(f"checking {file_name}")
            with open(file_name, 'r') as f:
                version_info = re.findall(entry["pattern"], f.read())
                print(version_info)
                if len([x for x in version_info if entry["version"] in x]) == 0:
                    sendlog("Expected version is {0}, clear all files...".format(entry["version"]), RED)
                    os.system("rm -rf {0}".format(log_folder))
                    return 1
            file_list.append(file_name)
    
    for file in file_list:
        os.utime(file)

    return 0
    

#*****************************************************************************
# Function	 : show_info
# Description: Show Monitor version history
# Inputs	 : NA
# Outputs	 : NA
# Notice	 : V0.3 modify get_ip() function log message, get_mac_address_by_rm_port() add message "failure" check
#*****************************************************************************
def show_info():
    sendlog ("\n")
    sendlog ("\033[1;36;40m********************************************************************************\033[0m")
    sendlog ("\033[1;36;40m*\033[1;33;40m CelestialPeak Config Check Program     -\033[0m  V{0} {1} Release By {2} \033[1;36;40m*\033[0m".format(VERSION, RELEASE_DATE, EDITOR))
    sendlog ("\033[1;36;40m********************************************************************************\033[0m")
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
    if not os.path.exists(win_st_file) or count < retryc:
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
        ssh_object = pxssh.pxssh(maxread=3000, timeout=5)
        sendlog("[rm_ip:{0:>12} rm_mac: {1} RACKSN:{2} SN:{3}] RM login1".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"],sn_info_list["RACKSN"],sn_info_list["sn"]))
        ssh_object.login(sn_info_list["rm_ip"], g_rm_username, g_rm_password, sync_multiplier=10, auto_prompt_reset=False)
        return ssh_object
    except pxssh.ExceptionPxssh as e:
        sendlog("[rm_ip:{0:>12} rm_mac: {1} RACKSN:{2} SN:{3}] login failed, delay 10s and retry".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"],sn_info_list["RACKSN"],sn_info_list["sn"]))
        time.sleep(10)
        try:
            ssh_object = pxssh.pxssh(maxread=3000, timeout=5)
            sendlog("[rm_ip:{0:>12} rm_mac: {1} RACKSN:{2} SN:{3}] RM login2".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"],sn_info_list["RACKSN"],sn_info_list["sn"]))
            ssh_object.login(sn_info_list["rm_ip"], g_rm_username, g_rm_password, sync_multiplier=10, auto_prompt_reset=False)
            return ssh_object
        except pxssh.ExceptionPxssh as e:
            sendlog("[rm_ip:{0:>12} rm_mac: {1} RACKSN:{2} SN:{3}] pxssh failed: login to RM.\n sterr:{4}".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"],sn_info_list["RACKSN"],sn_info_list["sn"], e), RED)
            return None
        # sendlog("[rm_ip:{0:>12} rm_mac: {1}] pxssh failed: login to RM.".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"]), RED)
        # sendlog(e, RED)
        # return None

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
            # print("return: "+ssh_object.before.decode ('utf-8').splitlines()[-1])
            if ssh_object.before.decode ('utf-8') == "" or "@localhost:" not in ssh_object.before.decode ('utf-8').splitlines()[-1]:
                #Login to RM switch
                #ssh_object = login_rm(sn_info_list)
                #if ssh_object == None:
                #    return 1
                #Disconnect other device
                #res = disconnect_cp_by_rm(ssh_object, sn_info_list)
                #if res == 1:
                #    return 1
                #Login to CP by port
                #res = connect_cp_by_rm(ssh_object, sn_info_list)
                #if res == 1:
                #    return 1
                #disconnect to CP
                ssh_object.sendline(g_cmd_disconnect_cp.format(sn_info_list["uut_to_rm_port"]))
                time.sleep(1)
                #connect to CP
                ssh_object.sendline(g_cmd_connect_cp.format(sn_info_list["uut_to_rm_port"]))
                ssh_object.sendline(" ")
                ssh_object.prompt()
                if ssh_object.before.decode ('utf-8') == "" or "@localhost:" not in ssh_object.before.decode ('utf-8').splitlines()[-1]:
                    sendlog("[rm_ip:{0:>12} rm_mac: {1} RACKSN:{2} SN:{3}] connect to CP fail".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"],sn_info_list["RACKSN"],sn_info_list["sn"]), RED)
                    return 1, None
        elif device == "RM":
            if ssh_object.before.decode ('utf-8') == "" or "WcsCli#" not in ssh_object.before.decode ('utf-8').splitlines()[-1]:
                #Login to RM switch
                ssh_object = login_rm(sn_info_list)
                if ssh_object == None:
                    return 1, None
            
        ssh_object.buffer = b"" #20230724 david
        sendlog("[rm_ip:{0:>12} rm_mac: {1} RACKSN:{2} SN:{3} {4}] cmd:{5}".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"], sn_info_list["RACKSN"],sn_info_list["sn"], device, cmd))
        # ssh_object.expect(r'.+')
        if device == "CP" and not (g_cmd_reset_soc in cmd or g_cmd_reboot in cmd or cmd.startswith(" ")):
            cmd = cmd + " | tee /tmp/cp_cmd.log"
        ssh_object.sendline(cmd)
        time.sleep(sleep_time)
        ssh_object.prompt()
        if device == "CP":
            # print("return: "+ssh_object.before.decode ('utf-8').splitlines()[-1])
            if ssh_object.before.decode ('utf-8') == "" or "@localhost:" not in ssh_object.before.decode ('utf-8').splitlines()[-1]:
                ssh_object.sendline(g_cmd_disconnect_cp.format(sn_info_list["uut_to_rm_port"]))
                time.sleep(1)
                #connect to CP
                ssh_object.sendline(g_cmd_connect_cp.format(sn_info_list["uut_to_rm_port"]))
                ssh_object.sendline(" ")
                ssh_object.prompt()
                if ssh_object.before.decode ('utf-8') == "" or "@localhost:" not in ssh_object.before.decode ('utf-8').splitlines()[-1]:
                    sendlog("[rm_ip:{0:>12} rm_mac: {1} RACKSN:{2} SN:{3}] connect to CP fail".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"],sn_info_list["RACKSN"],sn_info_list["sn"]), RED)
                    return 1, None
            if not (g_cmd_reset_soc in cmd or g_cmd_reboot in cmd or cmd.startswith(" ")):
                ssh_object.buffer = b""
                if "writeFlashjic" in cmd: #FPGA FW update command.
                    ssh_object.sendline(g_cmd_cat_cp_logfile+" | tail -10") #The full output about FPGA 4.4.4 update is too long to get cp prompt, only print the last 10 lines.
                else:
                    ssh_object.sendline(g_cmd_cat_cp_logfile)
                ssh_object.prompt()
                if ssh_object.before.decode ('utf-8') == "" or "@localhost:" not in ssh_object.before.decode ('utf-8').splitlines()[-1]:
                    sendlog("[rm_ip:{0:>12} rm_mac: {1} RACKSN:{2} SN:{3}] connect to CP fail".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"],sn_info_list["RACKSN"],sn_info_list["sn"]), RED)
                    return 1, None
        elif device == "RM":
            if ssh_object.before.decode ('utf-8') == "" or "WcsCli#" not in ssh_object.before.decode ('utf-8').splitlines()[-1]:
                #Login to RM switch
                ssh_object = login_rm(sn_info_list)
                if ssh_object == None:
                    return 1, None
        sendlog(ssh_object.before.decode ('utf-8').replace("'",''), 0, log_path) #20231101
        return 0, ssh_object.before.decode ('utf-8')
    except pxssh.ExceptionPxssh as e:
        sendlog("[rm_ip:{0:>12} rm_mac: {1} RACKSN:{2} SN:{3} {4}] pxssh failed: can not execute cmd:{5}".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"], sn_info_list["RACKSN"],sn_info_list["sn"], device, cmd), RED)
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
            if ssh_object.before.decode ('utf-8') == "" or "@localhost:" not in ssh_object.before.decode ('utf-8').splitlines()[-1]:
                #Login to RM switch
                #ssh_object = login_rm(sn_info_list)
                #if ssh_object == None:
                #    return 1
                #Disconnect other device
                #res = disconnect_cp_by_rm(ssh_object, sn_info_list)
                #if res == 1:
                #    return 1
                #Login to CP by port
                #res = connect_cp_by_rm(ssh_object, sn_info_list)
                #if res == 1:
                #    return 1
                #disconnect to CP
                ssh_object.sendline(g_cmd_disconnect_cp.format(sn_info_list["uut_to_rm_port"]))
                time.sleep(1)
                #connect to CP
                ssh_object.sendline(g_cmd_connect_cp.format(sn_info_list["uut_to_rm_port"]))
                ssh_object.sendline(" ")
                ssh_object.prompt()
                if ssh_object.before.decode ('utf-8') == "" or "@localhost:" not in ssh_object.before.decode ('utf-8').splitlines()[-1]:
                    sendlog("[rm_ip:{0:>12} rm_mac: {1} RACKSN:{2} SN:{3}] connect to CP fail".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"],sn_info_list["RACKSN"],sn_info_list["sn"]), RED)
                    return 1, None

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
        sendlog("[rm_ip:{0:>12} rm_mac: {1} RACKSN:{2} SN:{3} {4}] pxssh failed: can not execute cmd:{5}".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"], sn_info_list["RACKSN"],sn_info_list["sn"], device, cmd), RED)
        sendlog(e, RED)
        return 1, None
        
#_*****************************************************************************
#_ Function   : send_file_to_console
#_ Description: 
#_ Inputs     : cmd: the command tobe execute
#_ Outputs    : return value from the result of input command
#_ Notice     : 
#_*****************************************************************************
def send_file_to_console(ip,from_file,to_file,sn_info_list):
    # os.system("rm -rf /root/.ssh/known_hosts")
    result_str="Another instance of"
    while "Another instance of" in  result_str:
        cmdstr = "sshpass -p 'overlake' scp -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null {0} stuser@[{1}]:{2}".format(from_file, ip, to_file)
        sendlog("[RACKSN:{0} SN:{1}] cmdstr:{2}".format(sn_info_list["RACKSN"],sn_info_list["sn"],cmdstr))
        # (status,result) = commands.getstatusoutput(cmdstr)
        p = subprocess.Popen(cmdstr, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True,encoding="utf-8")
        stdout,stderr = p.communicate()
        output=stdout.strip() 
        ret=p.returncode
        status = ret
        result = output
        sendlog("[RACKSN:{0} SN:{1}] status:{2}".format(sn_info_list["RACKSN"],sn_info_list["sn"],status))
        sendlog("[RACKSN:{0} SN:{1}] result:{2}".format(sn_info_list["RACKSN"],sn_info_list["sn"],result))
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
def send_file_from_console(ip,from_file,to_file,sn_info_list):
    # os.system("rm -rf /root/.ssh/known_hosts")
    result_str="Another instance of"
    while "Another instance of" in  result_str:
        cmdstr = "sshpass -p 'overlake' scp -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@[{1}]:{0} {2} ".format(from_file, ip, to_file)
        sendlog("[RACKSN:{0} SN:{1}] cmdstr:{2}".format(sn_info_list["RACKSN"],sn_info_list["sn"],cmdstr))
        # (status,result) = commands.getstatusoutput(cmdstr)
        p = subprocess.Popen(cmdstr, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True,encoding="utf-8")
        stdout,stderr = p.communicate()
        output=stdout.strip() 
        ret=p.returncode
        status = ret
        result = output
        sendlog("[RACKSN:{0} SN:{1}] status:{2}".format(sn_info_list["RACKSN"],sn_info_list["sn"],status))
        sendlog("[RACKSN:{0} SN:{1}] result:{2}".format(sn_info_list["RACKSN"],sn_info_list["sn"],result))
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
        locallogin = False
        if ssh_object == None:
            ssh_object = pxssh.pxssh(timeout=5)
            ssh_object.login(sn_info_list["rm_ip"], g_rm_username, g_rm_password, sync_multiplier=10, auto_prompt_reset=False)
            locallogin = True
        ssh_object.buffer = b"" #20230724 david
        # ssh_object.expect(r'.+')
        ssh_object.sendline(g_cmd_disconnect_cp.format(sn_info_list["uut_to_rm_port"]))
        ssh_object.prompt()
        sendlog(ssh_object.before.decode ('utf-8'))
        if locallogin:
            ssh_object.logout()
        return 0
    except pxssh.ExceptionPxssh as e:
        sendlog("[rm_ip:{0:>12} rm_mac: {1} RACKSN:{2} SN:{3}] pxssh failed: can not disconnect other device".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"],sn_info_list["RACKSN"],sn_info_list["sn"]), RED)
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
        ssh_object.sendline(" ")
        ssh_object.prompt()
        sendlog(ssh_object.before.decode ('utf-8'))
        if ssh_object.before.decode ('utf-8') == "" or "@localhost:" not in ssh_object.before.decode ('utf-8').splitlines()[-1]:
            #disconnect to CP
            ssh_object.sendline(g_cmd_disconnect_cp.format(sn_info_list["uut_to_rm_port"]))
            time.sleep(1)
            #connect to CP
            ssh_object.sendline(g_cmd_connect_cp.format(sn_info_list["uut_to_rm_port"]))
            ssh_object.sendline(" ")
            ssh_object.prompt()
            #sendlog(ssh_object.before.decode ('utf-8'))
            if ssh_object.before.decode ('utf-8') == "" or "@localhost:" not in ssh_object.before.decode ('utf-8').splitlines()[-1]:
                sendlog("[rm_ip:{0:>12} rm_mac: {1} RACKSN:{2} SN:{3}] connect to CP fail".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"],sn_info_list["RACKSN"],sn_info_list["sn"]), RED)
                return 1
        return 0
    except pxssh.ExceptionPxssh as e:
        sendlog("[rm_ip:{0:>12} rm_mac: {1} RACKSN:{2} SN:{3}] pxssh failed: can not login to CP by port".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"],sn_info_list["RACKSN"],sn_info_list["sn"]), RED)
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
        sendlog("[RACKSN:{0} SN:{1}] make log folder ({2}) success".format(sn_info_list["RACKSN"],sn_info_list["sn"], sn_log_folder), GREEN)
    except OSError as e:
        if e.errno == errno.EEXIST:
            sendlog("[RACKSN:{0} SN:{1}] log folder ({2}) exist".format(sn_info_list["RACKSN"],sn_info_list["sn"],sn_log_folder), GREEN)
        else:
            sendlog("[RACKSN:{0} SN:{1}] {2}".format(sn_info_list["RACKSN"],sn_info_list["sn"],e))
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
                sendlog("[RACKSN:{0} SN:{1}] Get system info and mac address by port success !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
            else:
                sendlog("[RACKSN:{0} SN:{1}] Get system info and mac address by port fail !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                return 1
        else:
            sendlog("[RACKSN:{0} SN:{1}] Can not get result - get system info and mac address by port".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
            return 1
    
    SN = ""
    nic_mac_address = ""
    info = res.split("\n")
    for i in range(len(info)):
        if "Mac Address" in info[i]:
            nic_mac_address = info[i].split(": ")[1].strip()
            sendlog ("[RACKSN:{0} SN:{1}](Get port info) nic_mac_address = {2}".format(sn_info_list["RACKSN"],sn_info_list["sn"],nic_mac_address))
        if "SerialNumber" in info[i]:
            SN = info[i].split(": ")[1].strip()
            sendlog ("[RACKSN:{0} SN:{1}](Get port info) SerialNumber = {2}".format(sn_info_list["RACKSN"],sn_info_list["sn"],SN))
    
    if SN != sn_info_list["pdnum"]: 
        sendlog("[RACKSN:{0} SN:{1}] login to rm check SerialNumber FAIL : EXP = {2} GET = {3}.".format(sn_info_list["RACKSN"],sn_info_list["sn"],sn_info_list["pdnum"], SN),"FAIL")
        sendlog(sn_info_list,"FAIL")
        return 1
    
    if nic_mac_address != "":
        nic_mac_address = nic_mac_address.replace(":", "")
        
        #20210830 Ed add when C2080 is power off by Rack Manager, the mac adddress show failure
        if "failure" in nic_mac_address:
            return 1

        return nic_mac_address
    else:
        sendlog("[RACKSN:{0} SN:{1}] login to rm get mac adddress get fail ({1}.txt).".format(sn_info_list["RACKSN"],sn_info_list["sn"]), "FAIL")
        sendlog(sn_info_list,"FAIL")
        return 1
    

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
            "pdnum": "NA",
            "RACKSN": "NA",
            "rm_mac_addr": "NA",
            "rm_ip": "NA",
            "uut_mac_addr": "NA",
            "cp_mac_addr": "NA",
            "uut_ip": "NA",
            "cp_ip": "NA",
            "LOCATION": "NA",
            "STATION": "NA",
            "CP_GOLDEN_IMAGE": "NA",
            "CP_FACTORY_IMAGE": "NA",
            "CP_SOC_FIP_FW":"NA",
            "CP_SOC_FIP_PFMID":"NA",
            "CP_SOC_NITRO_FW":"NA",
            "CP_SOC_NITRO_PFMID":"NA",
            "CP_SOC_OS_FW":"NA",
            "CP_CERBERUS_FW":"NA",
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
                        
                if "ETH" in line and "MICROSOFT" in line.upper():
                    nic_info = line.split('=')[1].strip()
                    nic_info = nic_info.split(',')
                    if len(nic_info) != 0:
                        SNdict["cp_mac_addr"] = nic_info[0].strip()
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

                if "CP_CERBERUS_FW" in line:
                    SNdict["CP_CERBERUS_FW"] = line.split('=')[1].strip()
                
                #Get RACK_MOUNT_FW from SN.txt
                if "RACK_MOUNT_FW" in line:
                    SNdict["RACK_MOUNT_FW"] = line.split('=')[1].strip()
                
                #Get CSN from SN.txt
                if "CSN" in line:
                    SNdict["csn"] = line.split('=')[1].strip()
                    print ("CSN:{0}".format(SNdict["csn"]))

                if "PDNUM" in line:
                    SNdict["pdnum"] = line.split('=')[1].strip()
                    print ("PDNUM:{0}".format(SNdict["pdnum"]))
                
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
            print("master_node:{}".format(master_node))
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
            sendlog("get uut ip: [{0}]{1} mac:{2}".format(SNdict["LOCATION"],SNdict["sn"], SNdict["uut_mac_addr"]))
            SNdict["uut_ip"] = get_ip(SNdict["uut_mac_addr"])

            #Get CP ip from DHCP
            sendlog("get CP ip: [{0}]{1} mac:{2}".format(SNdict["LOCATION"],SNdict["sn"], SNdict["cp_mac_addr"]))
            SNdict["cp_ip"] = get_ip(SNdict["cp_mac_addr"])
            #Check reconfig flag
            if SNdict["uut_ip"] == 1 or SNdict["uut_ip"] == "":
                sendlog("get uut ip: [{0}]{1} set is_reconfig to False".format(SNdict["LOCATION"],SNdict["sn"]))
                SNdict["is_reconfig"] = False
            else:
                sendlog("[{0}]{1} is_reconfig is: {2}".format(SNdict["LOCATION"],SNdict["sn"], SNdict["is_reconfig"]))

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
        search_ip_cmd = g_cmd_search_ip_QTMC.format(mac_trans)
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
        #sendlog("Get_IP MAC = {0} IP = {1:.<12}".format(mac_trans,ip),"FAIL")
        return 1
    else:
        sendlog("Unknown build side","FAIL")
        return 1


#*****************************************************************************
# Function	 : rm_fpga_health_is_cp_golden_mode
# Description: Check CP is golden mode or not via RM FPGA health
# Inputs	 : sn_info_list: SN list information
# Outputs	 : True: golden mode 
#			 : False: not golden mode
# Notice	 : NA
#*****************************************************************************
def rm_fpga_health_is_cp_golden_mode(sn_info_list):
    try:
        ssh_object = pxssh.pxssh(maxread=3000, timeout=5)
        ssh_object.force_password = True
        sendlog ("[RACKSN:{0} SN:{1}] login... IP = {2}, user = {3}, password = {4}".format(sn_info_list["RACKSN"],sn_info_list["sn"],sn_info_list["rm_ip"], g_rm_username, g_rm_password))
        ssh_object.login(sn_info_list["rm_ip"], g_rm_username, g_rm_password, sync_multiplier=10, auto_prompt_reset=False)
        sendlog ("[RACKSN:{0} SN:{1}] check fpga health via RM".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
        ssh_object.sendline(g_cmd_RM_FPGA_health.format(sn_info_list["uut_to_rm_port"]))
        ssh_object.prompt()
    except pxssh.ExceptionPxssh as e:
        sendlog (str(e))
        sendlog ("[RACKSN:{0} SN:{1}] pxssh fail".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
        return 1
    time.sleep(1)
    is_find_str = False
    info = ssh_object.before.decode ('utf-8').split('\n')
    for line in info:
        print(line)
        if "PCIe HIP 1 Up" in line:
            is_find_str = True
            status = line.split(':')[1].strip()
            if status == "1":
                sendlog("[RACKSN:{0} SN:{1}] App mode".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                return 0
            else:
                sendlog("[RACKSN:{0} SN:{1}] Golden mode".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                return 2
    if is_find_str == False:
        sendlog ("[RACKSN:{0} SN:{1}] Cannot find FPGA-CONFIG string".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
        return 1
    
#*****************************************************************************
# Function	 : cp_ip_health_is_cp_golden_mode
# Description: Check CP is golden mode or not via CP IP
# Inputs	 : sn_info_list: SN list information
# Outputs	 : True: golden mode 
#			 : False: not golden mode
# Notice	 : 20231227 David add
#*****************************************************************************
def cp_ip_health_is_cp_golden_mode(sn_info_list):
    if sn_info_list["cp_ip"] == "NA" or sn_info_list["cp_ip"] == 1:
        sn_info_list["cp_ip"] = get_ip(sn_info_list["cp_mac_addr"])
        if sn_info_list["cp_ip"] == 1:
            return 1
    print ("[RACKSN:{0} SN:{1}] load CP driver via cp ip".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
    cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null -o ConnectTimeout=180 stuser@{} \"echo overlake | sudo -S /usr/sbin/modprobe catapult\"".format(sn_info_list["cp_ip"])
    getresult(cmd)

    print ("[RACKSN:{0} SN:{1}] dumpHealth via cp ip".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
    cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null -o ConnectTimeout=180 stuser@{} \"echo overlake | sudo -S /usr/bin/fpgadiagnostics -dumphealth\"".format(sn_info_list["cp_ip"])
    result = getresult(cmd)
    info = result.split('\n')

    for line in info:
        print(line)
        if "[FPGA-CONFIG    ]" in line:
            golden_str = line.split()[3].split(',')[0].strip()
            status = golden_str.split(':')[1]
            if status == "0":
                sendlog("[RACKSN:{0} SN:{1}] App mode".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                return 0
            else:
                sendlog("[RACKSN:{0} SN:{1}] Golden mode".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                return 2
    if "[FPGA-CONFIG    ]" not in result:
        sendlog ("[RACKSN:{0} SN:{1}] Cannot find FPGA-CONFIG string via cp ip".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
        return 1

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
        ssh_object = pxssh.pxssh(maxread=3000, timeout=5)
        ssh_object.force_password = True
        sendlog ("[RACKSN:{0} SN:{1}] login... IP = {2}, user = {3}, password = {4}".format(sn_info_list["RACKSN"],sn_info_list["sn"],sn_info_list["rm_ip"], g_rm_username, g_rm_password))
        ssh_object.login(sn_info_list["rm_ip"], g_rm_username, g_rm_password, sync_multiplier=10, auto_prompt_reset=False)
        sendlog ("[RACKSN:{0} SN:{1}] stop serial port".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
        ssh_object.sendline(g_cmd_disconnect_cp.format(sn_info_list["uut_to_rm_port"]))
        time.sleep(1)
        sendlog ("[RACKSN:{0} SN:{1}] start serial port".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
        ssh_object.sendline(g_cmd_connect_cp.format(sn_info_list["uut_to_rm_port"]))
        time.sleep(1)
        sendlog ("[RACKSN:{0} SN:{1}] install catapult driver".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
        ssh_object.sendline(g_cmd_install_catapult_driver)
        time.sleep(1)
        sendlog ("[RACKSN:{0} SN:{1}] dumpHealth".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
        ssh_object.sendline(g_cmd_dumphealth)
        ssh_object.prompt()
    except pxssh.ExceptionPxssh as e:
        sendlog (str(e))
        sendlog ("[RACKSN:{0} SN:{1}] pxssh fail".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
        return False
    time.sleep(1)
    is_find_str = False
    info = ssh_object.before.decode ('utf-8').split('\n')
    for line in info:
        print(line)
        if "[FPGA-CONFIG    ] OK " in line:
            is_find_str = True
            golden_str = line.split()[3].split(',')[0].strip()
            status = golden_str.split(':')[1]
            if status == "0":
                sendlog("[RACKSN:{0} SN:{1}] App mode".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                return False
            else:
                sendlog("[RACKSN:{0} SN:{1}] Golden mode".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                return 2
    if is_find_str == False:
        sendlog ("[RACKSN:{0} SN:{1}] Cannot find FPGA-CONFIG string".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
        return False
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
    
    update_flag = "{0}_update_flag.log".format(sn_info_list["CP_SN"])
    update_flag_path = "{0}/{1}".format(sn_log_folder, update_flag)

    if os.path.isfile(log_path):
        sendlog("[rm_ip:{0:>12} rm_mac: {1} rm_port: {2} RACKSN:{3} SN:{4}]CP record is already done ,please see {5}".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"], sn_info_list["uut_to_rm_port"], sn_info_list["RACKSN"],sn_info_list["sn"], log_path))
        return 0

    ###20211004 Jeffhung remove log_name everytime
    if os.path.isfile(log_path):
        os.remove(log_path)
    
    try:
        os.makedirs(sn_log_folder)
        sendlog("[RACKSN:{0} SN:{1}] make log folder ({2}) success".format(sn_info_list["RACKSN"],sn_info_list["sn"],sn_log_folder), GREEN)
    except OSError as e:
        if e.errno == errno.EEXIST:
            sendlog("[RACKSN:{0} SN:{1}] log folder ({2}) exist".format(sn_info_list["RACKSN"],sn_info_list["sn"], sn_log_folder), GREEN)
        else:
            sendlog("[RACKSN:{0} SN:{1}] {2}".format(sn_info_list["RACKSN"],sn_info_list["sn"], e))
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
        sendlog(ssh_object.before.decode ('utf-8').replace("'",''), 0, log_path)
    except pxssh.ExceptionPxssh as e:
        sendlog("[rm_ip:{0:>12} rm_mac: {1} RACKSN:{2} SN:{3}] pxssh failed: can not get CP chip id".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"],sn_info_list["RACKSN"],sn_info_list["sn"]), RED)
        sendlog(e, RED)
        return 1
    
    readflag = False
    info = ssh_object.before.decode ('utf-8').split("\n")
    for i in range(len(info)):
        if "Chip ID" in info[i]:
            line_next = info[i+1]
            CP_chip_id = re.findall(r'\S+',line_next)[1]
            sendlog ("[RACKSN:{0} SN:{1}] CP_chip_id:{2}".format(sn_info_list["RACKSN"],sn_info_list["sn"],CP_chip_id))
    
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
            sendlog(ssh_object.before.decode ('utf-8').replace("'",''), 0, log_path)
        except pxssh.ExceptionPxssh as e:
            sendlog("[rm_ip:{0:>12} rm_mac: {1} RACKSN:{2} SN:{3}] pxssh failed: can not {4}".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"], sn_info_list["RACKSN"],sn_info_list["sn"], action), RED)
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
     
    sendlog("[rm_ip:{0:>12} rm_mac: {1} rm_port: {2} RACKSN:{3} SN:{4}] golen_image_role_id = {5}".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"], sn_info_list["uut_to_rm_port"], sn_info_list["RACKSN"],sn_info_list["sn"], golen_image_role_id), 0, log_path)
    sendlog("[rm_ip:{0:>12} rm_mac: {1} rm_port: {2} RACKSN:{3} SN:{4}] golden_image_version = {5}".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"], sn_info_list["uut_to_rm_port"], sn_info_list["RACKSN"],sn_info_list["sn"], golden_image_version), 0, log_path)
    sendlog("[rm_ip:{0:>12} rm_mac: {1} rm_port: {2} RACKSN:{3} SN:{4}] golden_image_build_version = {5}".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"], sn_info_list["uut_to_rm_port"], sn_info_list["RACKSN"],sn_info_list["sn"], golden_image_build_version), 0, log_path)

    if golen_image_role_id == "" or golden_image_version == "" or golden_image_build_version == "": # 20240329 David modify
        sendlog("[rm_ip:{0:>12} rm_mac: {1} rm_port: {2} RACKSN:{3} SN:{4}] record golden image fail".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"], sn_info_list["uut_to_rm_port"],sn_info_list["RACKSN"],sn_info_list["sn"]))
        return 1
    
    sendlog("[rm_ip:{0:>12} rm_mac: {1} rm_port: {2} RACKSN:{3} SN:{4}] record golden image finish, full porocess please see {5}".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"], sn_info_list["uut_to_rm_port"],sn_info_list["RACKSN"],sn_info_list["sn"], log_path))
    ##20211130 jeffadd flag
    #os.system("touch {0}".format(update_flag_path)) #20240415 wkhuang move to the end of script
        
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
        sendlog("[RACKSN:{0} SN:{1}] make log folder ({2}) success".format(sn_info_list["RACKSN"],sn_info_list["sn"],sn_log_folder), GREEN)
    except OSError as e:
        if e.errno == errno.EEXIST:
            sendlog("[RACKSN:{0} SN:{1}]log folder ({2}) exist".format(sn_info_list["RACKSN"],sn_info_list["sn"],sn_log_folder), GREEN)
        else:
            sendlog("[RACKSN:{0} SN:{1}]{2}".format(sn_info_list["RACKSN"],sn_info_list["sn"],e))
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
                sendlog("[RACKSN:{0} SN:{1}]Show system state success !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
            else:
                sendlog("[RACKSN:{0} SN:{1}]Show system state fail !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                return 1
        else:
            sendlog("[RACKSN:{0} SN:{1}]Can not get result - show system state".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
            return 1
    
    #Check power state
    power_state_flag = False
    info = res.split("\n")
    for line in info:
        if "State" in line:
            if "ON" in line:
                power_state_flag = True
    
    if power_state_flag:
        sendlog("[rm_ip:{0:>12} rm_mac: {1} rm_port: {2} RACKSN:{3} SN:{4}] power on".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"], sn_info_list["uut_to_rm_port"],sn_info_list["RACKSN"],sn_info_list["sn"]))
        return 0
    else:
        sendlog("[rm_ip:{0:>12} rm_mac: {1} rm_port: {2} RACKSN:{3} SN:{4}] power off".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"], sn_info_list["uut_to_rm_port"],sn_info_list["RACKSN"],sn_info_list["sn"]))
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
    sendlog ("[RACKSN:{0} SN:{1}] sn = {1}".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
    sendlog ("[RACKSN:{0} SN:{1}] rm_mac_addr = {2}".format(sn_info_list["RACKSN"],sn_info_list["sn"], sn_info_list["rm_mac_addr"]))
    sendlog ("[RACKSN:{0} SN:{1}] rm_ip = {2}".format(sn_info_list["RACKSN"],sn_info_list["sn"], sn_info_list["rm_ip"]))
    sendlog ("[RACKSN:{0} SN:{1}] uut_mac_addr = {2}".format(sn_info_list["RACKSN"],sn_info_list["sn"], sn_info_list["uut_mac_addr"]))
    sendlog ("[RACKSN:{0} SN:{1}] uut_ip = {2}".format(sn_info_list["RACKSN"],sn_info_list["sn"], sn_info_list["uut_ip"]))
    sendlog ("[RACKSN:{0} SN:{1}] LOCATION = {2}".format(sn_info_list["RACKSN"],sn_info_list["sn"], sn_info_list["LOCATION"]))
    sendlog ("[RACKSN:{0} SN:{1}] STATION = {2}".format(sn_info_list["RACKSN"],sn_info_list["sn"], sn_info_list["STATION"]))
    sendlog ("[RACKSN:{0} SN:{1}] uut_to_rm_port = {2}".format(sn_info_list["RACKSN"],sn_info_list["sn"], sn_info_list["uut_to_rm_port"]))
    sendlog ("[RACKSN:{0} SN:{1}] is_dict_info_correct = {2}".format(sn_info_list["RACKSN"],sn_info_list["sn"], sn_info_list["is_dict_info_correct"]))
    sendlog ("[RACKSN:{0} SN:{1}] is_reconfig = {2}".format(sn_info_list["RACKSN"],sn_info_list["sn"], sn_info_list["is_reconfig"]))
    sendlog ("[RACKSN:{0} SN:{1} LOCATION:{2}] need record golden image and do reconfig".format(sn_info_list["RACKSN"],sn_info_list["sn"],sn_info_list["LOCATION"]))
    #step 1 : check uut power status
    if chk_uut_power_state(sn_info_list) != 0: 
        sendlog("[RACKSN:{0} SN: {1}] chk_uut_power_state FAIL".format(sn_info_list["RACKSN"], sn_info_list["sn"]), RED)
        return 1

    #step 2 : record CP golden image version
    if do_record_cp_golden_img_ver_connect_rm_port(sn_info_list) != 0:
        #sendlog("[RACKSN:{0}, SN: {1}] record CP golden image version FAIL".format(sn_info_list["RACKSN"], sn_info_list["sn"]), RED)
        msg = "record CP golden image version FAIL !"
        sendlog("[RACKSN:{0} SN:{1}] {2}".format(sn_info_list["RACKSN"],sn_info_list["sn"], msg))
        send_data_sf(time.strftime("%Y%m%d%H%M%S"),msg, "WARNING", sn_info_list["sn"], sn_info_list["LOCATION"], sn_info_list["STATION"], "")
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
                sendlog("[RACKSN:{0} SN:{1}] get_soc_version devroot:{2}".format(sn_info_list["RACKSN"], sn_info_list["sn"], line.split('root')[0]))
                return 0, line.split('root')[0]
            if "prdroot" in line:
                sendlog("[RACKSN:{0} SN:{1}] get_soc_version prdroot:{2}".format(sn_info_list["RACKSN"], sn_info_list["sn"], line.split('root')[0]))
                return 0, line.split('root')[0]
    else:
        return 1, None

#*****************************************************************************
# Function	 : soc_boot_mode_check
# Description: Check the boot mode of the SOC and perform necessary actions to set it to 0x00 if required.
# Inputs	 : ssh_object (object): SSH object for communication with the SOC.
#            : sn_info_list (dict): Dictionary containing the serial number information of the SOC.
#            : log_path (str): Path to the log file.
# Outputs	 : 0, if the SOC boot mode is successfully set to 0x00.
#			 : 1, otherwise
# Notice	 : NA
#*****************************************************************************
def soc_boot_mode_check(ssh_object, sn_info_list, log_path):
    #check boot mode
    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_get_bootmode, 0, log_path)
    if res != "":
        if "bootmode = 0x00" in res:
            sendlog("[RACKSN:{0} SN: {1}] SOC Boot mode get 0x00".format(sn_info_list["RACKSN"], sn_info_list["sn"]))
            return 0
        else:
            sendlog("[RACKSN:{0} SN: {1}] SOC Boot mode not 0x00, need set to 0".format(sn_info_list["RACKSN"], sn_info_list["sn"]))
            #Set bootmode to 0
            ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, log_path)
            if ret != 0:
                return 1
            else:
                if res != "":
                    if "boot mode is set to 0x00" in res:
                        sendlog("[RACKSN:{0} SN:{1}] Set boot mode to 0 success !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                    else:
                        sendlog("[RACKSN:{0} SN:{1}] Set boot mode to 0 fail !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                        return 1
                else:
                    sendlog("[RACKSN:{0} SN:{1}] Can not get result - set boot mode to 0".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                    return 1

            #Reboot the SoC
            # ssh_object.sendcontrol('c')
            ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_reboot, 60, log_path)
            if ret != 0:
                return 1

            ret, res = send_cmd_to_cp(ssh_object, sn_info_list, " ", 10, log_path)
            if ret != 0:
                    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, log_path)
                    return 1
            else:
                if res !="":
                    if "root@localhost:~#" in res.split("\n")[-1]:
                        sendlog("[RACKSN:{0} SN:{1}] Reboot SOC success !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                    else:
                        time.sleep(10)
                        ret, res = send_cmd_to_cp(ssh_object, sn_info_list, " ", 3, log_path)
                        if ret != 0:
                            ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, log_path)
                            return 1
                        else:
                            if res !="":
                                if "root@localhost:~#" in res.split("\n")[-1]:
                                    sendlog("[RACKSN:{0} SN:{1}] After Wait 10 second! Reboot SOC success !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                                else:
                                    sendlog("[RACKSN:{0} SN:{1}] After Wait 10 second! Reboot SOC fail!".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                                    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, log_path)
                                    return 1
                            else:
                                sendlog("[RACKSN:{0} SN:{1}] Can not get result - After reboot SOC!!".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                                ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, log_path)
                                return 1
                else:
                    sendlog("[RACKSN:{0} SN:{1}] Can not get result - After reboot SOC!!".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                    return 1
            #check after set to zero and reboot
            ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_get_bootmode, 0, log_path)
            if res != "":
                if "bootmode = 0x00" in res:
                    sendlog("[RACKSN:{0} SN: {1}] SOC Boot mode get 0x00".format(sn_info_list["RACKSN"], sn_info_list["sn"]))
                    return 0
            else:
                sendlog("[RACKSN:{0} SN: {1}] SOC Boot mode not 0x00 after reboot".format(sn_info_list["RACKSN"], sn_info_list["sn"]))
                return 1
    else:
        sendlog("[RACKSN:{0} SN: {1}] Cannot get SOC Boot mode".format(sn_info_list["RACKSN"], sn_info_list["sn"]))
        return 1
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
    # sn_log_folder = "{0}/{1}".format(g_log_folder, sn_info_list["sn"])
    # flag_name = "{0}_first_update_soc_fw.log".format(sn_info_list["sn"])
    # flag_path = "{0}/{1}".format(sn_log_folder, flag_name)
    ret = chk_soc_fw(sn_info_list)
    if ret != 0:
        if ret == 2:
            sendlog("[RACKSN:{0} SN: {1}] SoC firmware is error and need to update".format(sn_info_list["RACKSN"], sn_info_list["sn"]))
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
    # elif not os.path.isfile(flag_path) or chk_pfmid(sn_info_list) != 0: #20230724 David add chk_pfmid
    elif chk_pfmid(sn_info_list) != 0:
        sendlog("[RACKSN:{0} SN: {1}] First SoC firmware update and do PFM active".format(sn_info_list["RACKSN"], sn_info_list["sn"]))
        ret = first_update_soc_fw(sn_info_list)
        if ret != 0:
            sendlog("[RACKSN:{0} SN:{1}] update SoC firmware FAIL".format(sn_info_list["RACKSN"],sn_info_list["sn"]), RED)
            # os.system("rm -rf {}".format(flag_path))
            return 1
        else:
            sendlog("[RACKSN:{0} SN:{1}] update SoC firmware PASS".format(sn_info_list["RACKSN"],sn_info_list["sn"]), GREEN)
            return 0
    else:
        sendlog("[RACKSN:{0} SN:{1}] check SoC firmware PASS. no need to update".format(sn_info_list["RACKSN"],sn_info_list["sn"]), GREEN)
        if chk_pfmid(sn_info_list) != 0: # 20220525 David add PFM check
            sendlog("[RACKSN:{0} SN:{1}] SoC PFM FAIL".format(sn_info_list["RACKSN"],sn_info_list["sn"]), RED)
            return 1
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
        sendlog("[RACKSN:{0} SN:{1}] make log folder ({2}) success".format(sn_info_list["RACKSN"],sn_info_list["sn"], sn_log_folder), GREEN)
    except OSError as e:
        if e.errno == errno.EEXIST:
            sendlog("[RACKSN:{0} SN:{1}] log folder ({2}) exist".format(sn_info_list["RACKSN"],sn_info_list["sn"], sn_log_folder), GREEN)
        else:
            sendlog("[RACKSN:{0} SN:{1}] {2}".format(sn_info_list["RACKSN"],sn_info_list["sn"], e))
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
    
    try:
        #Check SoC bootmode
        ret = soc_boot_mode_check(ssh_object, sn_info_list, log_path)
        if ret != 0:
            sendlog("[RACKSN:{0} SN:{1}] SoC boot mode check fail!".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
            return 1

        #Get SoC firmware version
        ret, res = get_soc_version(ssh_object, sn_info_list, g_cmd_get_soc_firmware_ver, log_path)
        if ret != 0:
            sendlog("[RACKSN:{0} SN:{1}] Can not get SoC firmware version !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
            return 1
        else:
            get_soc_fw_ver = res
            sendlog("[RACKSN:{0} SN:{1}] get_soc_fw_ver = {2}".format(sn_info_list["RACKSN"],sn_info_list["sn"], get_soc_fw_ver))
        
        #Get SoC Nitro firmware version
        ret, res = get_soc_version(ssh_object, sn_info_list, g_cmd_get_soc_nitro_firmware_ver, log_path)
        if ret != 0:
            sendlog("[RACKSN:{0} SN:{1}] Can not get SoC Nitro firmware version !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
            return 1
        else:
            get_soc_fw_nitro_ver = res
            sendlog("[RACKSN:{0} SN:{1}] get_soc_fw_nitro_ver = {2}".format(sn_info_list["RACKSN"],sn_info_list["sn"], get_soc_fw_nitro_ver))
        
        #Get SoC cerberus firmware version
        ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_get_soc_cerberus_firmware_ver+" | grep 'Cerberus Version'", 0, log_path)
        if ret != 0 or res == "":
            sendlog("[RACKSN:{0} SN:{1}] Can not get SoC cerberus firmware version !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
            return 1
        else:
            get_soc_cerberus_fw_ver = ""
            res = res.split("\n")
            for line in res:
                if "Cerberus Version:" in line:
                    get_soc_cerberus_fw_ver = line.split(':')[1].strip()
            sendlog("[RACKSN:{0} SN:{1}] get_soc_cerberus_fw_ver = {2}".format(sn_info_list["RACKSN"],sn_info_list["sn"], get_soc_cerberus_fw_ver))

        #Get SoC OS version
        ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_get_soc_os_ver, 0, log_path)
        if ret != 0 or res == "":
            sendlog("[RACKSN:{0} SN:{1}] Can not get SoC OS version !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
            return 1
        else:
            get_soc_os_fw_ver = ""
            res = res.split("\n")
            for line in res:
                if "VERSION_ID=" in line:
                    get_soc_os_fw_ver = line.split('=')[1].replace('"','').strip()
            sendlog("[RACKSN:{0} SN:{1}] get_soc_os_fw_ver = {2}".format(sn_info_list["RACKSN"],sn_info_list["sn"], get_soc_os_fw_ver))
            
        #Disconnect other device
        if disconnect_cp_by_rm(None, sn_info_list) == 1:
            return 1
        ssh_object.logout() #logout current RM session
        
        #Judge SoC firmware/Nitro firmware version are as expected or not
        if sn_info_list["CP_SOC_FIP_FW"] != get_soc_fw_ver:
            sendlog("[RACKSN:{2} SN:{3}] SoC firmware version check FAIL ! exp:{0}, get:{1}".format(sn_info_list["CP_SOC_FIP_FW"], get_soc_fw_ver, sn_info_list["RACKSN"], sn_info_list["sn"]), RED)
            return 2
        else:
            sendlog("[RACKSN:{2} SN:{3}] SoC firmware version check PASS ! exp:{0}, get:{1}".format(sn_info_list["CP_SOC_FIP_FW"], get_soc_fw_ver, sn_info_list["RACKSN"], sn_info_list["sn"]), GREEN)
            if sn_info_list["CP_SOC_NITRO_FW"] != get_soc_fw_nitro_ver:
                sendlog("[RACKSN:{2} SN:{3}] SoC firmware Nitro version check FAIL ! exp:{0}, get:{1}".format(sn_info_list["CP_SOC_NITRO_FW"], get_soc_fw_nitro_ver, sn_info_list["RACKSN"], sn_info_list["sn"]), RED)
                return 2
            else:
                sendlog("[RACKSN:{2} SN:{3}] SoC firmware Nitro version check PASS ! exp:{0}, get:{1}".format(sn_info_list["CP_SOC_NITRO_FW"], get_soc_fw_nitro_ver, sn_info_list["RACKSN"], sn_info_list["sn"]), GREEN)
            
            #Check cerberus firmware version
            if sn_info_list["CP_CERBERUS_FW"] != get_soc_cerberus_fw_ver:
                sendlog("[RACKSN:{2} SN:{3}] Cerberus firmware version check FAIL ! exp:{0}, get:{1}".format(sn_info_list["CP_CERBERUS_FW"], get_soc_cerberus_fw_ver, sn_info_list["RACKSN"], sn_info_list["sn"]), RED)
                return 2
            else:
                sendlog("[RACKSN:{2} SN:{3}] Cerberus firmware version check PASS ! exp:{0}, get:{1}".format(sn_info_list["CP_CERBERUS_FW"], get_soc_cerberus_fw_ver, sn_info_list["RACKSN"], sn_info_list["sn"]), GREEN)
                
            #Check os version
            if sn_info_list["CP_SOC_OS_FW"] != get_soc_os_fw_ver:
                sendlog("[RACKSN:{2} SN:{3}] SOC OS version check FAIL ! exp:{0}, get:{1}".format(sn_info_list["CP_SOC_OS_FW"], get_soc_os_fw_ver, sn_info_list["RACKSN"], sn_info_list["sn"]), RED)
                return 2
            else:
                sendlog("[RACKSN:{2} SN:{3}] SOC OS version check PASS ! exp:{0}, get:{1}".format(sn_info_list["CP_SOC_OS_FW"], get_soc_os_fw_ver, sn_info_list["RACKSN"], sn_info_list["sn"]), GREEN)
    except Exception as e:
        sendlog("[RACKSN:{0} SN:{1}] Script Exception: {2}".format(sn_info_list["RACKSN"], sn_info_list["sn"], str(e)), RED)
        return 1
            
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

def remove_uuts_flag(rack_sn):
    pattern = f"{g_win_config_folder}/*.txt"
    cmd = f"grep {rack_sn} {pattern}"
    output = getresult(cmd)
    if output != 0:
        for line in output.split('\n'):
            match = re.search(r"P\d+", line)
            if match:  
                extracted_value = match.group() 
                sn_log_folder = f"{g_log_folder}/{extracted_value}/*updating*"
                sendlog(f"sn_log_folder: {sn_log_folder}")
                os.system(f"rm -rf {sn_log_folder}")
                sendlog(f"remove {sn_log_folder}")
          
            
def is_rm_updated(sn_info_list):    
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

    if sn_info_list["STATION"] == "PRETEST":	
        ret, res = send_cmd_to_rm(ssh_object, sn_info_list, "show manager version", 20, log_path)
        if ret != 0:
            return 1
        else:
            if res != "":
                if sn_info_list["RACK_MOUNT_FW"] in res:
                    return 0
                else:
                    return 1

    ssh_object.logout() #logout current RM session
    return 0
    
#*****************************************************************************
# Function	 : get_image_directory
# Description: Retrieves the correct image path for the firmware
# Inputs	 : sn_info_list: SN list information
# Outputs	 : str: directory contianing image path
#			 : None: FAIL
# Notice	 : NA
#*****************************************************************************
def get_image_directory(sn_info_list):
    # Get correct directory by checking which one contains the correct nitro file
    nitro_pfm_file = "A2040.NITRO.PFM.{}.bin".format(int(sn_info_list["CP_SOC_NITRO_PFMID"], 16))
    upgrade_image_file = upgrade_image.format(sn_info_list["CP_SOC_OS_FW"])
    res = getresult(f"find /tftpboot/firmware/Celestial_Peak/ -name {upgrade_image_file}")
    if res != "":
        check_directories = res.splitlines()
        image_path = None
        for directory in check_directories:
            path = directory.split(upgrade_image_file)[0]
            base_path = re.match(r"(/tftpboot/firmware/Celestial_Peak/.*?/)", path)[0]

            # Check whether other firmware files are in this directory
            res = getresult(f"find {base_path} -name {nitro_pfm_file}")
            if res != "":
                image_path = path
                break

        if image_path is None:
            image_path = path

        image_path = image_path.replace("/tftpboot/", "")
        if sn_info_list["CP_SOC_FIP_FW"] in replace_image_name and sn_info_list["CP_SOC_NITRO_FW"] in replace_image_name:
            image_path = image_path.replace(replace_image_name[sn_info_list["CP_SOC_FIP_FW"]][0],replace_image_name[sn_info_list["CP_SOC_FIP_FW"]][1])
        
        return image_path
    else:
        sendlog("[RACKSN:{0} SN:{1}] Cannot find CP SOC image path".format(sn_info_list["RACKSN"], sn_info_list["sn"]), RED)
        return None
    
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
    upload_img_flag = "{0}/{1}_overlakeimg_flag_{2}.log".format(g_log_folder,sn_info_list["RACKSN"], sn_info_list["master_rm_port"])
    
    image_path = get_image_directory(sn_info_list)
    if image_path is None:
        return 1

    try:
        os.makedirs(sn_log_folder)
        sendlog("[RACKSN:{0} SN:{1}] make log folder ({2}) success".format(sn_info_list["RACKSN"], sn_info_list["sn"], sn_log_folder), GREEN)
    except OSError as e:
        if e.errno == errno.EEXIST:
            sendlog("[RACKSN:{0} SN:{1}] log folder ({2}) exist".format(sn_info_list["RACKSN"], sn_info_list["sn"], sn_log_folder), GREEN)
        else:
            sendlog("[RACKSN:{0} SN:{1}] {2}".format(sn_info_list["RACKSN"], sn_info_list["sn"], e))
            return 1
    
    #Login to RM switch
    ssh_object = login_rm(sn_info_list)
    if ssh_object == None:
        return 1
    
    #Disconnect other device
    if disconnect_cp_by_rm(ssh_object, sn_info_list) == 1:
        return 1

    #check tftp list from RM #20231102 David add
    ret, res = send_cmd_to_rm(ssh_object, sn_info_list, g_cmd_show_tftp, 60, log_path)
    if ret != 0:
        return 1
    else:
        if res != "":
            if upgrade_image.format(sn_info_list["CP_SOC_OS_FW"]) in res:
                #20250421WayneXu add md5 check
                if upgrade_image.format(sn_info_list["CP_SOC_OS_FW"]) in g_overlake_md5sum:
                    overlake_md5 = g_overlake_md5sum[upgrade_image.format(sn_info_list["CP_SOC_OS_FW"])]
                    #20250421 WayneXu 0002.17.240911-prd use the same image name compare to previous version
                    if sn_info_list["CP_SOC_FIP_FW"] in replace_image_name and sn_info_list["CP_SOC_NITRO_FW"] in replace_image_name:
                        overlake_md5 = replace_md5[upgrade_image.format(sn_info_list["CP_SOC_OS_FW"])][1]
                    get_md5 = ""
                    lines = res.strip().split('\n')
                    for i, line in enumerate(lines):
                        if sn_info_list["CP_SOC_OS_FW"] in line:
                            get_md5 = lines[i-2].split(":")[1].strip()
                    if get_md5 != overlake_md5:
                        sendlog("overlake md5sum not equal with database!! get: {0}  expect: {1}".format(get_md5, overlake_md5), 0, log_path)
                        #Remove file on RM
                        ret, res = send_cmd_to_rm(ssh_object, sn_info_list, g_cmd_del_tftp_file.format(upgrade_image.format(sn_info_list["CP_SOC_OS_FW"])), 10, log_path)
                        if ret != 0:
                            return 1
                        else:
                            if res != "":
                                if is_success(res):
                                    sendlog("[RACKSN:{0} SN:{1}] Remove file from RM success !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                                else:
                                    sendlog("[RACKSN:{0} SN:{1}] Remove file from RM fail !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                                    return 1
                            else:
                                sendlog("[RACKSN:{0} SN:{1}] Can not get result - Remove file from RM".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                                return 1
                        #Copy image from TFTP to RM
                        ret, res = send_cmd_to_rm(ssh_object, sn_info_list, g_cmd_copy_image_to_rm.format(tftp_ip, image_path, upgrade_image.format(sn_info_list["CP_SOC_OS_FW"])), 200, log_path)
                        if ret != 0:
                            return 1
                        else:
                            if res != "":
                                if is_success(res):
                                    os.system("touch {0}".format(upload_img_flag))
                                    sendlog("[RACKSN:{0} SN:{1}] Copy image from TFTP to RM success !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                                else:
                                    sendlog("[RACKSN:{0} SN:{1}] Copy image from TFTP to RM fail !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                                    return 1
                            else:
                                sendlog("[RACKSN:{0} SN:{1}] Can not get result - copy image from TFTP to RM".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                                return 1
                    else:
                        sendlog("overlake md5sum check successfully!! get: {0}  expect: {1}".format(get_md5, overlake_md5), 0, log_path)
                sendlog("[RACKSN:{0} SN:{1}] {2} image from TFTP to RM success !".format(sn_info_list["RACKSN"],sn_info_list["sn"], upgrade_image.format(sn_info_list["CP_SOC_OS_FW"])))
            else:
                #Copy image from TFTP to RM
                ret, res = send_cmd_to_rm(ssh_object, sn_info_list, g_cmd_copy_image_to_rm.format(tftp_ip, image_path, upgrade_image.format(sn_info_list["CP_SOC_OS_FW"])), 200, log_path)
                if ret != 0:
                    return 1
                else:
                    if res != "":
                        if is_success(res):
                            os.system("touch {0}".format(upload_img_flag))
                            sendlog("[RACKSN:{0} SN:{1}] Copy image from TFTP to RM success !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                        else:
                            sendlog("[RACKSN:{0} SN:{1}] Copy image from TFTP to RM fail !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                            return 1
                    else:
                        sendlog("[RACKSN:{0} SN:{1}] Can not get result - copy image from TFTP to RM".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                        return 1
        else:
            sendlog("[RACKSN:{0} SN:{1}] Can not get result - check image on SoC".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
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
                    sendlog("[RACKSN:{0} SN:{1}]RM FW is {2}!".format(sn_info_list["RACKSN"],sn_info_list["sn"],sn_info_list["RACK_MOUNT_FW"]))
                    return 0
                else:
                    sendlog("[RACKSN:{0} SN:{1}]RM FW is {2}, trying to update to {3}!".format(sn_info_list["RACKSN"],sn_info_list["sn"],res,sn_info_list["RACK_MOUNT_FW"]))
                    ##start to update RM FW
                    ret, res = send_cmd_to_rm(ssh_object, sn_info_list, g_cmd_show_tftp, 60, log_path)
                    if ret != 0:
                        return 1
                    else:
                        if res != "":
                            if rmfw_image in res:
                                sendlog("[RACKSN:{0} SN:{1}]{2} image from TFTP to RM success !".format(sn_info_list["RACKSN"],sn_info_list["sn"],rmfw_image))
                            else:
                                #Copy image from TFTP to RM
                                ret, res = send_cmd_to_rm(ssh_object, sn_info_list, g_cmd_copy_image_to_rm.format(tftp_ip, rm_firmware_path, rmfw_image), 200, log_path)
                                if ret != 0:
                                    return 1
                                else:
                                    if res != "":
                                        if is_success(res):
                                            sendlog("[RACKSN:{0} SN:{1}]Copy RM FW image from TFTP to RM success !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                                            
                                        else:
                                            sendlog("[RACKSN:{0} SN:{1}] Copy RM FW image from TFTP to RM fail !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                                            return 1
                                    else:
                                        sendlog("[RACKSN:{0} SN:{1}] Can not get result - copy RM FW image from TFTP to RM".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                                        return 1
                            
                            
                            ###update RM FW (g_cmd_RM_FW_UPDATE)
                            for i in range(3):
                                time.sleep(5)
                                os.system("ssh-keygen -R {0} > /dev/null".format(sn_info_list["rm_ip"]))
                                time.sleep(5)
                                
                                cmd = "sshpass -p '{0}' ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null {1}@{2} -c aes256-cbc '{3}' > {4}".format(g_rm_password, g_rm_username, sn_info_list["rm_ip"], g_cmd_RM_FW_UPDATE.format(rmfw_image), log_path)
                                sendlog("[RACKSN:{0} SN:{1}-{2}] Update RM command: {3}".format(sn_info_list["RACKSN"],sn_info_list["sn"],sn_info_list["LOCATION"], cmd))
                            
                                ret,output,stderr = gs_exec_cmd(cmd)
                                sendlog("[RACKSN:{0} SN:{1}-{2}] Output: {3}".format(sn_info_list["RACKSN"],sn_info_list["sn"],sn_info_list["LOCATION"], output))
                                if ret != 0:
                                    sendlog("[RACKSN:{0} SN:{1}-{2}] stderr: {3}".format(sn_info_list["RACKSN"],sn_info_list["sn"],sn_info_list["LOCATION"],stderr))
                                    continue
                                else:
                                    break
                            
                            #Jenny_tmp
                            sendlog("[RACKSN:{0} SN:{1}]update RM FW image. Need to sleep 600s!".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                            time.sleep(600)
                            return 0                        
                        else:
                            sendlog("[RACKSN:{0}SN:{1}] Can not get result - For RM FW IMAGE!".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                            return 1
    ssh_object.logout() #logout current RM session
    
    
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
    CP_IP=""

    fip_pfm_file  = "A2040.FIP.PFM.{}.bin".format(int(sn_info_list["CP_SOC_FIP_PFMID"],16))
    fip_fw_file = "fip.bin"
    nitro_pfm_file = "A2040.NITRO.PFM.{}.bin".format(int(sn_info_list["CP_SOC_NITRO_PFMID"],16))
    nitro_fw_file = "nitro.img"

    g_cp_Cerberus_fw="cerberus_v{0}.bin".format(sn_info_list["CP_CERBERUS_FW"])
    g_cp_Cerberus_fw_loc="/project/firmware/{0}/cp/{1}".format(g_project.lower(),g_cp_Cerberus_fw)

    image_path = get_image_directory(sn_info_list)
    if image_path is None:
        return 1

    try:
        os.makedirs(sn_log_folder)
        sendlog("[RACKSN:{0} SN:{1}]make log folder ({2}) success".format(sn_info_list["RACKSN"],sn_info_list["sn"], sn_log_folder), GREEN)
    except OSError as e:
        if e.errno == errno.EEXIST:
            sendlog("[RACKSN:{0} SN:{1}]log folder ({2}) exist".format(sn_info_list["RACKSN"],sn_info_list["sn"], sn_log_folder), GREEN)
        else:
            sendlog("[RACKSN:{0} SN:{1}]{2}".format(sn_info_list["RACKSN"],sn_info_list["sn"], e))
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
            if upgrade_image.format(sn_info_list["CP_SOC_OS_FW"]) in res:
                sendlog("[RACKSN:{0} SN:{1}] {2} image from TFTP to RM success !".format(sn_info_list["RACKSN"],sn_info_list["sn"], upgrade_image.format(sn_info_list["CP_SOC_OS_FW"])))
            else:
                #Copy image from TFTP to RM
                ret, res = send_cmd_to_rm(ssh_object, sn_info_list, g_cmd_copy_image_to_rm.format(tftp_ip, image_path, upgrade_image.format(sn_info_list["CP_SOC_OS_FW"])), 200, log_path)
                if ret != 0:
                    return 1
                else:
                    if res != "":
                        if is_success(res):
                            os.system("touch {0}".format(upload_img_flag))
                            sendlog("[RACKSN:{0} SN:{1}] Copy image from TFTP to RM success !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                        else:
                            sendlog("[RACKSN:{0} SN:{1}] Copy image from TFTP to RM fail !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                            return 1
                    else:
                        sendlog("[RACKSN:{0} SN:{1}] Can not get result - copy image from TFTP to RM".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                        return 1
        else:
            sendlog("[RACKSN:{0} SN:{1}] Can not get result - check image on SoC".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
            return 1
    
    #Mount image on SoC
    ret, res = send_cmd_to_rm(ssh_object, sn_info_list, g_cmd_mount_image_on_soc.format(sn_info_list["uut_to_rm_port"], upgrade_image.format(sn_info_list["CP_SOC_OS_FW"])), 20, log_path)
    if ret != 0:
        return 1
    else:
        if res != "":
            if is_success(res):
                sendlog("[RACKSN:{0} SN:{1}] Mount image on SoC success !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
            else:
                sendlog("[RACKSN:{0} SN:{1}] Mount image on SoC fail !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                send_cmd_to_rm(ssh_object, sn_info_list, "set system boot -t eMMC -i {0} -b 1".format(sn_info_list["uut_to_rm_port"]), 5, log_path)
                send_cmd_to_rm(ssh_object, sn_info_list, "set system reset -i {0} -b 1".format(sn_info_list["uut_to_rm_port"]), 5, log_path)
                send_cmd_to_rm(ssh_object, sn_info_list, "set system remotedrive unmount -i {0} -b 1".format(sn_info_list["uut_to_rm_port"]), 5, log_path)
                send_cmd_to_rm(ssh_object, sn_info_list, "set system cmd -i {0} -c mc reset cold".format(sn_info_list["uut_to_rm_port"]), 5, log_path)
                time.sleep(200) #for BMC reset
                return 1
        else:
            sendlog("[RACKSN:{0} SN:{1}] Can not get result - mount image on SoC".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
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
                sendlog("[RACKSN:{0} SN:{1}] Check sda drive mounted success !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
            else:
                sendlog("[RACKSN:{0} SN:{1}] Check sda drive mounted fail !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                return 1
        else:
            sendlog("[RACKSN:{0} SN:{1}] Can not get result - check sda drive mounted".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
            return 1

    #Set bootmode to 1
    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_one, 0, log_path)
    if ret != 0:
        return 1
    else:
        if res != "":
            if "boot mode is set to 0x01" in res:
                sendlog("[RACKSN:{0} SN:{1}] Set boot mode to 1 success !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
            else:
                sendlog("[RACKSN:{0} SN:{1}] Set boot mode to 1 fail !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                return 1
        else:
            sendlog("[RACKSN:{0} SN:{1}] Can not get result - set boot mode to 1".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
            return 1
    
    #Reboot the SoC
    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_reboot, 150, log_path)
    if ret != 0:
        ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, log_path)
        return 1

    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, " ", 10, log_path)
    if ret != 0:
            ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, log_path)
            return 1
    else:
        if res !="":
            #print "DBG:{0}".format(res)
            if "@localhost:" in res.split("\n")[-1]:
                sendlog("[RACKSN:{0} SN:{1}] Reboot SOC success !".format(sn_info_list["RACKSN"],sn_info_list["sn"])) 
            else:
                time.sleep(10)
                ret, res = send_cmd_to_cp(ssh_object, sn_info_list, " ", 3, log_path)
                if ret != 0:
                    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, log_path)
                    return 1
                else:
                    if res !="":
                        if "@localhost:" in res.split("\n")[-1]:
                            sendlog("[RACKSN:{0} SN:{1}] Reboot SOC success !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                        else:
                            sendlog("[RACKSN:{0} SN:{1}] Reboot SOC fail!".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                            ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, log_path)
                            return 1
                    else:
                        sendlog("[RACKSN:{0} SN:{1}] Can not get result - After reboot SOC!!".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                        ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, log_path)
                        return 1
        else:
            sendlog("[RACKSN:{0} SN:{1}] Can not get result - After reboot SOC!!".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
            return 1

    #Execute "socflash" command
    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_socflash, 300, log_path)#20250505 WayneXu BSL return CP card need more time
    if ret != 0:
        ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, log_path)
        return 1
    sendlog("[RACKSN:{0} SN:{1}] Execute socflash command success!!!".format(sn_info_list["RACKSN"],sn_info_list["sn"]))

    #Create /tmp/usb folder
    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_mkdir_usb_folder, 0, log_path)
    if ret != 0:
        ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, log_path)
        return 1
    sendlog("[RACKSN:{0} SN:{1}] Create /tmp/usb folder success!!".format(sn_info_list["RACKSN"],sn_info_list["sn"]))

    #Mount /tmp/usb to /dev/sda1
    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_mount_usb_folder, 0, log_path)
    if ret != 0:
        ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, log_path)
        return 1
    sendlog("[RACKSN:{0} SN:{1}] Mount /tmp/usb to /dev/sda1 success!!".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
    
    #Check bin files exist or not
    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_check_bin_file_exist, 0, log_path)
    if ret != 0:
        ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, log_path)
        return 1
    else:
        if res != "":
            try:
                fip_fw_file = re.search("fip.*?bin", res).group() # Most of FIP FW is named fip.bin but it is named fip_padded.bin in v2.17 SoC.
                nitro_fw_file = re.search("nitro.*?img", res).group()
            except:
                pass
            if fip_pfm_file and fip_fw_file and nitro_pfm_file and nitro_fw_file in res:
                sendlog("[RACKSN:{0} SN:{1}] Check bin files success !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
            else:
                sendlog("[RACKSN:{0} SN:{1}] Check bin files fail !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, log_path)
                return 1
        else:
            sendlog("[RACKSN:{0} SN:{1}] Can not get result - check bin files".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
            ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, log_path)
            return 1
        

    g_cmd_update_sop = ["cerberus_utility pfmupdate 0 /tmp/usb/{} 0".format(fip_pfm_file),
                        "cerberus_utility socfwupdate 0 /tmp/usb/{} 1".format(fip_fw_file),
                        "cerberus_utility pfmupdate 1 /tmp/usb/{} 0".format(nitro_pfm_file),
                        "cerberus_utility socfwupdate 1 /tmp/usb/{}".format(nitro_fw_file)]
        
    #do update FW
    fip_ret = chk_pfmid_single(ssh_object,sn_info_list,"FIP")
    if fip_ret == 2:
        for cmd in g_cmd_update_sop[0:2]:
            ret, res = send_cmd_to_cp(ssh_object, sn_info_list, cmd, 150, log_path)
            if ret != 0:
                ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, log_path)
                return 1

            if res != "":
                if "Cerberus command completed successfully" in res:
                    sendlog("[RACKSN:{0} SN:{1}] Use update command success.".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                else:
                    sendlog("[RACKSN:{0} SN:{1}] Use update command fail: {2}".format(sn_info_list["RACKSN"],sn_info_list["sn"],cmd))
                    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, log_path)
                    return 1
            else:
                sendlog("[RACKSN:{0} SN:{1}] Can not get cmd result: {2}".format(sn_info_list["RACKSN"],sn_info_list["sn"],cmd))
                ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, log_path)
                return 1
    elif fip_ret == 1:
        sendlog("[RACKSN:{0} SN:{1}] Can not get FIP status".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
        ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, log_path)
        return 1
    elif fip_ret == 0:
        cmd = g_cmd_update_sop[1]
        ret, res = send_cmd_to_cp(ssh_object, sn_info_list, cmd, 120, log_path)
        if ret != 0:
            ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, log_path)
            return 1

        if res != "":
            if "Cerberus command completed successfully" in res:
                sendlog("[RACKSN:{0} SN:{1}] Use update command success.".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
            else:
                sendlog("[RACKSN:{0} SN:{1}] Use update command fail: {2}".format(sn_info_list["RACKSN"],sn_info_list["sn"],cmd))
                ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, log_path)
                return 1
        else:
            sendlog("[RACKSN:{0} SN:{1}] Can not get cmd result: {2}".format(sn_info_list["RACKSN"],sn_info_list["sn"],cmd))
            ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, log_path)
            return 1
    nitro_ret = chk_pfmid_single(ssh_object,sn_info_list,"NITRO")
    if nitro_ret == 2:
        for cmd in g_cmd_update_sop[2:4]:
            ret, res = send_cmd_to_cp(ssh_object, sn_info_list, cmd, 120, log_path)
            if ret != 0:
                ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, log_path)
                return 1

            if res != "":
                if "Cerberus command completed successfully" in res:
                    sendlog("[RACKSN:{0} SN:{1}] Use update command success.".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                else:
                    sendlog("[RACKSN:{0} SN:{1}] Use update command fail: {2}".format(sn_info_list["RACKSN"],sn_info_list["sn"],cmd))
                    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, log_path)
                    return 1
            else:
                sendlog("[RACKSN:{0} SN:{1}] Can not get cmd result: {2}".format(sn_info_list["RACKSN"],sn_info_list["sn"],cmd))
                ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, log_path)
                return 1
    elif nitro_ret == 1:
        sendlog("[RACKSN:{0} SN:{1}] Can not get NITRO status".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
        ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, log_path)
        return 1
    elif nitro_ret == 0:
        cmd = g_cmd_update_sop[3]
        ret, res = send_cmd_to_cp(ssh_object, sn_info_list, cmd, 120, log_path)
        if ret != 0:
            ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, log_path)
            return 1

        if res != "":
            if "Cerberus command completed successfully" in res:
                sendlog("[RACKSN:{0} SN:{1}] Use update command success.".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
            else:
                sendlog("[RACKSN:{0} SN:{1}] Use update command fail: {2}".format(sn_info_list["RACKSN"],sn_info_list["sn"],cmd))
                ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, log_path)
                return 1
        else:
            sendlog("[RACKSN:{0} SN:{1}] Can not get cmd result: {2}".format(sn_info_list["RACKSN"],sn_info_list["sn"],cmd))
            ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, log_path)
            return 1

    # for cmd in g_cmd_update_sop:
    # 	ret, res = send_cmd_to_cp(ssh_object, sn_info_list, cmd, 120, log_path)
    # 	if ret != 0:
    # 		return 1

    # 	if res != "":
    # 		if "Cerberus command completed successfully" in res:
    # 			sendlog("Use update command success.")
    # 		else:
    # 			sendlog("Use update command fail: {0}".format(cmd))
    # 			return 1
    # 	else:
    # 		sendlog("Can't get cmd result: {0}".format(cmd))
    # 		return 1

    #do Cerberus FW update
    sendlog ("[RACKSN:{0} SN:{1}] Copy Cerberus FW from TFTP to CP SoC".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
    #Find CP SOC IP
    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, "ifconfig", 0, log_path)
    if ret != 0:
        ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, log_path)
        return 1, None
    if res != "":
        for line in res.splitlines():
            # if "inet addr:" in line:
            if "inet" in line and "inet6" not in line: #20230927 david change query message, os change
                if "127.0.0.1" in line:
                    continue
                if "addr:" in line:
                    CP_IP = line.split()[1].split(":")[1]
                else:
                    CP_IP = line.split()[1]
                ret = os.system(g_cmd_ping.format(CP_IP))
                if ret == 0:
                    sendlog("[RACKSN:{0} SN:{1}] Get_CP_IP IP = {2}".format(sn_info_list["RACKSN"], sn_info_list["sn"], CP_IP),"PASS")
                    break
            
    #Copy image to CP SOC
    sendlog("[RACKSN:{0} SN:{1}] Copy {2} to CP {3}".format(sn_info_list["RACKSN"], sn_info_list["sn"], g_cp_Cerberus_fw_loc,g_cp_tmp))
    g_cmd_copy_image_to_soc = "scp {0}@{1}:{2} {3}".format(tftp_user,tftp_ip,g_cp_Cerberus_fw_loc,g_cp_tmp)
    #send_file_to_console(CP_IP,g_cp_Cerberus_fw_loc,g_cp_tmp,sn_info_list)
    #Copy image from TFTP to CP SoC
    ret, res = scp_send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_copy_image_to_soc, 20, log_path)
    if ret != 0:
        ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, log_path)
        return 1
    sendlog ("[RACKSN:{0} SN:{1}] Update CP Cerberus FW".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
    cmd = "cerberus_utility fwupdate /tmp/{}".format(g_cp_Cerberus_fw)
    sendlog ("[RACKSN:{0} SN:{1}] cmd:{2}".format(sn_info_list["RACKSN"],sn_info_list["sn"], cmd))
    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, cmd, 120, log_path)
    if ret != 0:
        sendlog("[RACKSN:{0} SN:{1}] Use update command fail: {2}".format(sn_info_list["RACKSN"],sn_info_list["sn"],cmd))
        ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, log_path)
        return 1	
    sendlog(res.split('\n'), 0, log_path)
    if res == "":
        sendlog("[RACKSN:{0} SN:{1}] Cannot get cmd result: {2}".format(sn_info_list["RACKSN"],sn_info_list["sn"], cmd))
        ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, log_path)
        return 1
    elif "Cerberus command completed successfully" in res:
        sendlog("[RACKSN:{0} SN:{1}] Use update command success.".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
    else:
        sendlog("[RACKSN:{0} SN:{1}] Use update command fail: {2}".format(sn_info_list["RACKSN"],sn_info_list["sn"],cmd))
        ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, log_path)
        return 1
        
    #Set bootmode to 0
    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, log_path)
    if ret != 0:
        ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, log_path)
        return 1
    else:
        if res != "":
            if "boot mode is set to 0x00" in res:
                sendlog("[RACKSN:{0} SN:{1}] Set boot mode to 0 success !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
            else:
                sendlog("[RACKSN:{0} SN:{1}] Set boot mode to 0 fail !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                return 1
        else:
            sendlog("[RACKSN:{0} SN:{1}] Can not get result - set boot mode to 0".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
            return 1
        
    #Reset SoC
    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_reset_soc, 90, log_path)
    if ret != 0:
        return 1	

    #Check SoC bootmode
    ret = soc_boot_mode_check(ssh_object, sn_info_list, log_path)
    if ret != 0:
        sendlog("[RACKSN:{0} SN:{1}] SoC boot mode check fail!".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
        return 1

    os.system("touch {0}".format(flag_path))

    #Disconnect other device
    if disconnect_cp_by_rm(None, sn_info_list) == 1:
        return 1
    ssh_object.logout() #logout current RM session

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

    fip_pfm_file  = "A2040.FIP.PFM.{}.bin".format(int(sn_info_list["CP_SOC_FIP_PFMID"],16))
    fip_fw_file = "fip.bin"
    nitro_pfm_file = "A2040.NITRO.PFM.{}.bin".format(int(sn_info_list["CP_SOC_NITRO_PFMID"],16))
    nitro_fw_file = "nitro.img"
    g_cmd_update_sop = ["cerberus_utility pfmupdate 0 /tmp/usb/{} 0".format(fip_pfm_file),
                        "cerberus_utility socfwupdate 0 /tmp/usb/fip.bin 1",
                        "cerberus_utility pfmupdate 1 /tmp/usb/{} 0".format(nitro_pfm_file),
                        "cerberus_utility socfwupdate 1 /tmp/usb/nitro.img"]

    image_path = get_image_directory(sn_info_list)
    if image_path is None:
        return 1

    try:
        os.makedirs(sn_log_folder)
        sendlog("[RACKSN:{0} SN:{1}] make log folder ({2}) success".format(sn_info_list["RACKSN"],sn_info_list["sn"], sn_log_folder), GREEN)
    except OSError as e:
        if e.errno == errno.EEXIST:
            sendlog("[RACKSN:{0} SN:{1}] log folder ({2}) exist".format(sn_info_list["RACKSN"],sn_info_list["sn"],sn_log_folder), GREEN)
        else:
            sendlog("[RACKSN:{0} SN:{1}] {2}".format(sn_info_list["RACKSN"],sn_info_list["sn"], e))
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

    g_cmd_copy_image_to_soc = "scp {0}@{1}:/tftpboot/{2}{3} /tmp/".format(tftp_user,tftp_ip,image_path,upgrade_image.format(sn_info_list["CP_SOC_OS_FW"]))
    #Copy image from TFTP to CP SoC
    ret, res = scp_send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_copy_image_to_soc, 20, log_path)
    if ret != 0:
        return 1
    else:
        if res != "":
            if "100%" in res:
                sendlog("[RACKSN:{0} SN:{1}] copy image from TFTP to SoC success !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
            else:
                sendlog("[RACKSN:{0} SN:{1}] copy image from TFTP to SoC fail ! res:\n{2}".format(sn_info_list["RACKSN"],sn_info_list["sn"],res))
                return 1
        else:
            sendlog("[RACKSN:{0} SN:{1}] Can not get result - copy image from TFTP to SoC".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
            return 1

    
    g_cmd_losetup_image = "losetup -f -P /tmp/{}".format(upgrade_image.format(sn_info_list["CP_SOC_OS_FW"]))
    #Execute "losetup_image" command
    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_losetup_image, 0, log_path)
    if ret != 0:
        return 1
    sendlog("[RACKSN:{0} SN:{1}] Execute losetup command success!!!".format(sn_info_list["RACKSN"],sn_info_list["sn"]))

    g_cmd_check_loop2_exist = "lsblk"
    #Check "loop2" drive losetup
    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_check_loop2_exist, 0, log_path)
    if ret != 0:
        return 1
    else:
        if res != "":
            if "loop2p1" in res:
                sendlog("[RACKSN:{0} SN:{1}] Check loop2p1 drive losetup success !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
            else:
                sendlog("[RACKSN:{0} SN:{1}] Check loop2p1 drive losetup fail !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                return 1
        else:
            sendlog("[RACKSN:{0} SN:{1}] Can not get result - check loop2 drive losetup".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
            return 1

    #Create /tmp/usb folder
    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_mkdir_usb_folder, 0, log_path)
    if ret != 0:
        return 1
    sendlog("[RACKSN:{0} SN:{1}] Create /tmp/usb folder success!!".format(sn_info_list["RACKSN"],sn_info_list["sn"]))

    g_cmd_mount_usb_loop2p1_folder = "mount /dev/loop2p1 /tmp/usb/"
    #Mount /tmp/usb to /dev/loop2p1
    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_mount_usb_loop2p1_folder, 0, log_path)
    if ret != 0:
        return 1
    sendlog("[RACKSN:{0} SN:{1}] Mount /tmp/usb to /dev/loop2p1 success!!".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
    
    #Check bin files exist or not
    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_check_bin_file_exist, 0, log_path)
    if ret != 0:
        return 1
    else:
        if res != "":
            if fip_pfm_file and fip_fw_file and nitro_pfm_file and nitro_fw_file in res:
                sendlog("[RACKSN:{0} SN:{1}] Check bin files success !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
            else:
                sendlog("[RACKSN:{0} SN:{1}] Check bin files fail !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                return 1
        else:
            sendlog("[RACKSN:{0} SN:{1}] Can not get result - check bin files".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
            return 1

    #do update FW
    fip_ret = chk_pfmid_single(ssh_object,sn_info_list,"FIP")
    if fip_ret == 2:
        for cmd in g_cmd_update_sop[0:2]:
            ret, res = send_cmd_to_cp(ssh_object, sn_info_list, cmd, 120, log_path)
            if ret != 0:
                return 1

            if res != "":
                if "Cerberus command completed successfully" in res:
                    sendlog("[RACKSN:{0} SN:{1}] Use update command success.".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                else:
                    sendlog("[RACKSN:{0} SN:{1}] Use update command fail: {2}".format(sn_info_list["RACKSN"],sn_info_list["sn"],cmd))
                    return 1
            else:
                sendlog("[RACKSN:{0} SN:{1}] Can not get cmd result: {2}".format(sn_info_list["RACKSN"],sn_info_list["sn"],cmd))
                return 1
    elif fip_ret == 1:
        sendlog("[RACKSN:{0} SN:{1}] Can not get FIP status".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
        return 1
    elif fip_ret == 0:
        cmd = g_cmd_update_sop[1]
        ret, res = send_cmd_to_cp(ssh_object, sn_info_list, cmd, 120, log_path)
        if ret != 0:
            return 1

        if res != "":
            if "Cerberus command completed successfully" in res:
                sendlog("[RACKSN:{0} SN:{1}] Use update command success.".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
            else:
                sendlog("[RACKSN:{0} SN:{1}] Use update command fail: {2}".format(sn_info_list["RACKSN"],sn_info_list["sn"],cmd))
                return 1
        else:
            sendlog("[RACKSN:{0} SN:{1}] Can not get cmd result: {2}".format(sn_info_list["RACKSN"],sn_info_list["sn"],cmd))
            return 1
    nitro_ret = chk_pfmid_single(ssh_object,sn_info_list,"NITRO")
    if nitro_ret == 2:
        for cmd in g_cmd_update_sop[2:4]:
            ret, res = send_cmd_to_cp(ssh_object, sn_info_list, cmd, 120, log_path)
            if ret != 0:
                return 1

            if res != "":
                if "Cerberus command completed successfully" in res:
                    sendlog("[RACKSN:{0} SN:{1}] Use update command success.".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                else:
                    sendlog("[RACKSN:{0} SN:{1}] Use update command fail: {2}".format(sn_info_list["RACKSN"],sn_info_list["sn"],cmd))
                    return 1
            else:
                sendlog("[RACKSN:{0} SN:{1}] Can not get cmd result: {2}".format(sn_info_list["RACKSN"],sn_info_list["sn"],cmd))
                return 1
    elif nitro_ret == 1:
        sendlog("[RACKSN:{0} SN:{1}] Can not get NITRO status".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
        return 1
    elif nitro_ret == 0:
        cmd = g_cmd_update_sop[3]
        ret, res = send_cmd_to_cp(ssh_object, sn_info_list, cmd, 120, log_path)
        if ret != 0:
            return 1

        if res != "":
            if "Cerberus command completed successfully" in res:
                sendlog("[RACKSN:{0} SN:{1}] Use update command success.".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
            else:
                sendlog("[RACKSN:{0} SN:{1}] Use update command fail: {2}".format(sn_info_list["RACKSN"],sn_info_list["sn"],cmd))
                return 1
        else:
            sendlog("[RACKSN:{0} SN:{1}] Can not get cmd result: {2}".format(sn_info_list["RACKSN"],sn_info_list["sn"],cmd))
            return 1
    # for cmd in g_cmd_update_sop:
    # 	ret, res = send_cmd_to_cp(ssh_object, sn_info_list, cmd, 120, log_path)
    # 	if ret != 0:
    # 		return 1

    # 	if res != "":
    # 		if "Cerberus command completed successfully" in res:
    # 			sendlog("Use update command success.")
    # 		else:
    # 			sendlog("Use update command fail: {0}".format(cmd))
    # 			return 1
    # 	else:
    # 		sendlog("Can't get cmd result: {0}".format(cmd))
    # 		return 1
        
    #Reset SoC
    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_reset_soc, 60, log_path)
    if ret != 0:
        return 1
    #Check SoC PFM status
    if chk_pfmid(sn_info_list) != 0: # 20220525 David add PFM check
        sendlog("[RACKSN:{0} SN:{1}] SoC PFM FAIL".format(sn_info_list["RACKSN"],sn_info_list["sn"]), RED)
        return 1

    #Disconnect other device
    if disconnect_cp_by_rm(None, sn_info_list) == 1:
        return 1
    ssh_object.logout() #logout current RM session

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
                sendlog("[RACKSN:{0} SN:{1}] get_fpga_version ver:{2}, role:{3}".format(sn_info_list["RACKSN"],sn_info_list["sn"], ver, role))
        return 0, res,ver,role
    else:
        sendlog("[RACKSN:{0} SN:{1}] cannot get ver and role info in get_fpga_version".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
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
        sendlog("[RACKSN:{0} SN:{1}] make log folder ({2}) success".format(sn_info_list["RACKSN"], sn_info_list["sn"], sn_log_folder), GREEN)
    except OSError as e:
        if e.errno == errno.EEXIST:
            sendlog("[RACKSN:{0} SN:{1}] log folder ({2}) exist".format(sn_info_list["RACKSN"], sn_info_list["sn"], sn_log_folder), GREEN)
        else:
            sendlog("[RACKSN:{0} SN:{1}] {2}".format(sn_info_list["RACKSN"], sn_info_list["sn"], e))
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
    
    #Check FPGA version
    ret, res, ver, role = get_fpga_version(ssh_object, sn_info_list, g_cmd_dumphealth, log_path)
    if ret != 0:
        sendlog("[RACKSN:{0} SN:{1}] Can not get FPGA firmware version !".format(sn_info_list["RACKSN"], sn_info_list["sn"]))
        return 1
    else:
        get_fpga_fw_ver = ver+','+role
        sendlog("[RACKSN:{0} SN:{1}] GOLDEN:get_fpga_fw_ver = {2}".format(sn_info_list["RACKSN"], sn_info_list["sn"], get_fpga_fw_ver))
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
    if disconnect_cp_by_rm(None, sn_info_list) == 1:
        return 1
    ssh_object.logout() #logout current RM session
    
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

    g_cp_FPGA_firmware=""
    g_cp_FPGA_firmware_loc=""
    cmd = "find /project/firmware/{0}/ -name *{1}*.rpd".format(g_project.lower(),sn_info_list["CP_GOLDEN_IMAGE"].split(',')[0])
    res = getresult(cmd)
    if res != "":
        g_cp_FPGA_firmware = res.split('/')[-1].strip()
        g_cp_FPGA_firmware_loc=res.strip()
    else:
        sendlog("[RACKSN:{0} SN:{1}] Cannot find cp FPGA firmware file name".format(sn_info_list["RACKSN"], sn_info_list["sn"]), RED)
        return 1

    try:
        os.makedirs(sn_log_folder)
        sendlog("[RACKSN:{0} SN:{1}] make log folder ({2}) success".format(sn_info_list["RACKSN"], sn_info_list["sn"], sn_log_folder), GREEN)
    except OSError as e:
        if e.errno == errno.EEXIST:
            sendlog("[RACKSN:{0} SN:{1}] log folder ({2}) exist".format(sn_info_list["RACKSN"], sn_info_list["sn"], sn_log_folder), GREEN)
        else:
            sendlog("[RACKSN:{0} SN:{1}] {2}".format(sn_info_list["RACKSN"], sn_info_list["sn"], e))
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
            # if "inet addr:" in line:
            if "inet" in line and "inet6" not in line: #20230927 david change query message, os change
                if "127.0.0.1" in line:
                    continue
                if "addr:" in line:
                    CP_IP = line.split()[1].split(":")[1]
                else:
                    CP_IP = line.split()[1]
                ret = os.system(g_cmd_ping.format(CP_IP))
                if ret == 0:
                    sendlog("[RACKSN:{0} SN:{1}] Get_CP_IP IP = {2}".format(sn_info_list["RACKSN"], sn_info_list["sn"], CP_IP),"PASS")
                    break
            
    #Copy image to CP SOC
    sendlog("[RACKSN:{0} SN:{1}] Copy {2} to CP {3}".format(sn_info_list["RACKSN"], sn_info_list["sn"], g_cp_FPGA_firmware_loc,g_cp_tmp))    
    g_cmd_copy_image_to_soc = "scp {0}@{1}:{2} {3}".format(tftp_user,tftp_ip,g_cp_FPGA_firmware_loc,g_cp_tmp)
    #send_file_to_console(CP_IP,g_cp_FPGA_firmware_loc,g_cp_tmp,sn_info_list)
    #Copy image from TFTP to CP SoC
    ret, res = scp_send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_copy_image_to_soc, 20, log_path)
    
    if ret != 0:
        return 1

    #update FPGA image
    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_update_fpga.format(g_cp_tmp+g_cp_FPGA_firmware), 900, log_path) #Increase update timeout since the 4.4.4 need more time to upgrade FPGA FW
    if ret != 0:
        return 1
    else:
        if res != "":
            if re.search("Exiting WriteFlashSlot FPGA_STATUS 0x0", res):
                sendlog("[RACKSN:{0} SN:{1}] CP FPGA image update success !".format(sn_info_list["RACKSN"], sn_info_list["sn"]))
            else:
                sendlog("[RACKSN:{0} SN:{1}] CP FPGA image update fail !".format(sn_info_list["RACKSN"], sn_info_list["sn"]))
                return 1
        else:
            sendlog("[RACKSN:{0} SN:{1}] Can not get result - CP FPGA update".format(sn_info_list["RACKSN"], sn_info_list["sn"]))
            return 1
    
    ##reconfig to app then reconfig back to golden
    #Change FPGA slot to App
    ret, res = reconfig_fpga_slot(ssh_object, sn_info_list, g_cmd_reconfigapp, log_path)
    if ret != 0:
        sendlog("[RACKSN:{0} SN:{1}] Can not reconfig CP FPGA slot successfully![DBG]:{2}".format(sn_info_list["RACKSN"], sn_info_list["sn"], res.replace("'",'')))
        return 1
        
    #Change FPGA slot to Golden
    ret, res = reconfig_fpga_slot(ssh_object, sn_info_list, g_cmd_reconfigGolden, log_path)
    if ret != 0:
        sendlog("[RACKSN:{0} SN:{1}] Can not reconfig CP FPGA slot successfully![DBG]:{2}".format(sn_info_list["RACKSN"], sn_info_list["sn"], res.replace("'",'')))
        return 1
    sendlog("[RACKSN:{0} SN:{1}] CP FPGA has been reconfig to golden mode, create power cycle flag!".format(sn_info_list["RACKSN"], sn_info_list["sn"]))
    gs_exec_cmd("touch {0}/{1}_reboot".format(sn_log_folder, sn_info_list["sn"]))

    #Disconnect other device
    if disconnect_cp_by_rm(None, sn_info_list) == 1:
        return 1
    ssh_object.logout() #logout current RM session

    
    return 0

#*****************************************************************************
# Function	 : chk_pfmid
# Description: Check CP PFMID
# Inputs	 : sn_info_list: SN list information
# Outputs	 : True : already provision
#			 : False : not provision
# Notice	 : NA
#*****************************************************************************
def chk_pfmid(sn_info_list, type=""):
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
        sendlog("[RACKSN:{0} SN:{1}] Can not get cerberus provision status!".format(sn_info_list["RACKSN"], sn_info_list["sn"]))
        return 1
    get_fip_pfmid = ""
    for line in res.splitlines():
        if  "Cerberus PFM ID:" in line:
            get_fip_pfmid = line.split()[3]
            sendlog ("[RACKSN:{0} SN:{1}] get_fip_pfmid:{2}".format(sn_info_list["RACKSN"], sn_info_list["sn"], get_fip_pfmid))
        elif "No valid PFM found" in line:
            sendlog ("[RACKSN:{0} SN:{1}] Cerberus FIP No PFM".format(sn_info_list["RACKSN"], sn_info_list["sn"]))
            return 2
            
    
    #check cerberus NITRO_PFMID
    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_cerberus_pfm_chk.format(1), 3, log_path)
    if ret != 0:
        sendlog("[RACKSN:{0} SN:{1}] Can not get cerberus provision status!".format(sn_info_list["RACKSN"], sn_info_list["sn"]))
        return 1
    get_nitro_pfmid = ""
    for line in res.splitlines():
        if  "Cerberus PFM ID:" in line:
            get_nitro_pfmid = line.split()[3]
            sendlog ("[RACKSN:{0} SN:{1}] get_nitro_pfmid:{2}".format(sn_info_list["RACKSN"], sn_info_list["sn"], get_nitro_pfmid))
        elif "No valid PFM found" in line:
            sendlog ("[RACKSN:{0} SN:{1}] Cerberus NITRO No PFM".format(sn_info_list["RACKSN"], sn_info_list["sn"]))
            return 2
    
    #Judge SoC FIP/NITRO PFMID are as expected or not
    if sn_info_list["CP_SOC_FIP_PFMID"].lower() != get_fip_pfmid.lower():
        sendlog("[RACKSN:{0} SN:{1}]SoC FIP PFMID FAIL ! exp:{2}, get:{3}".format(sn_info_list["RACKSN"],sn_info_list["sn"],sn_info_list["CP_SOC_FIP_PFMID"].lower(), get_fip_pfmid.lower()), RED)
        return 2
    else:
        sendlog("[RACKSN:{0} SN:{1}]SoC FIP PFMID check PASS ! exp:{2}, get:{3}".format(sn_info_list["RACKSN"],sn_info_list["sn"],sn_info_list["CP_SOC_FIP_PFMID"].lower(), get_fip_pfmid.lower()), GREEN)
        if sn_info_list["CP_SOC_NITRO_PFMID"].lower() != get_nitro_pfmid.lower():
            sendlog("[RACKSN:{0} SN:{1}]SoC NITRO PFMID check FAIL ! exp:{2}, get:{3}".format(sn_info_list["RACKSN"],sn_info_list["sn"],sn_info_list["CP_SOC_NITRO_PFMID"].lower(), get_nitro_pfmid.lower()), RED)
            return 2
        else:
            sendlog("[RACKSN:{0} SN:{1}]SoC NITRO PFMID check PASS ! exp:{2}, get:{3}".format(sn_info_list["RACKSN"].lower(),sn_info_list["sn"],sn_info_list["CP_SOC_NITRO_PFMID"], get_nitro_pfmid.lower()), GREEN)

    #Disconnect other device
    if disconnect_cp_by_rm(None, sn_info_list) == 1:
        return 1
    ssh_object.logout() #logout current RM session
    
    sendlog("[RACKSN:{0} SN:{1}] CP is Provision~~".format(sn_info_list["RACKSN"], sn_info_list["sn"]))
    return 0

#*****************************************************************************
# Function	 : chk_pfmid_single
# Description: Check CP PFMID
# Inputs	 : sn_info_list: SN list information
# Outputs	 : True : already provision
#			 : False : not provision
# Notice	 : NA
#*****************************************************************************
def chk_pfmid_single(ssh_object, sn_info_list, type=""):
    sn_log_folder = "{0}/{1}".format(g_log_folder, sn_info_list["sn"])
    log_name = "{0}_cp_pfmid.log".format(sn_info_list["sn"])
    log_path = "{0}/{1}".format(sn_log_folder, log_name)
    # #Login to RM switch
    # ssh_object = login_rm(sn_info_list)
    # if ssh_object == None:
    # 	return 1
    
    # #Disconnect other device
    # if disconnect_cp_by_rm(ssh_object, sn_info_list) == 1:
    # 	return 1
    
    # #Login to CP by port
    # if connect_cp_by_rm(ssh_object, sn_info_list) == 1:
    # 	return 1	
        
    if type == "FIP":
        #check cerberus FIP_PFMID
        ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_cerberus_pfm_chk.format(0), 3, log_path)
        if ret != 0:
            sendlog("[RACKSN:{0} SN:{1}] Can not get cerberus provision status!".format(sn_info_list["RACKSN"], sn_info_list["sn"]))
            return 1
        get_fip_pfmid = ""
        for line in res.splitlines():
            if  "Cerberus PFM ID:" in line:
                get_fip_pfmid = line.split()[3]
                sendlog ("[RACKSN:{0} SN:{1}] get_fip_pfmid:{2}".format(sn_info_list["RACKSN"], sn_info_list["sn"], get_fip_pfmid))
            elif "No valid PFM found" in line:
                sendlog ("[RACKSN:{0} SN:{1}] Cerberus FIP No PFM".format(sn_info_list["RACKSN"], sn_info_list["sn"]))
                return 2
        if sn_info_list["CP_SOC_FIP_PFMID"].lower() != get_fip_pfmid.lower():
            sendlog("[RACKSN:{0} SN:{1}]SoC FIP PFMID FAIL ! exp:{2}, get:{3}".format(sn_info_list["RACKSN"],sn_info_list["sn"],sn_info_list["CP_SOC_FIP_PFMID"].lower(), get_fip_pfmid.lower()), RED)
            return 2
        else:
            sendlog("[RACKSN:{0} SN:{1}]SoC FIP PFMID check PASS ! exp:{2}, get:{3}".format(sn_info_list["RACKSN"],sn_info_list["sn"],sn_info_list["CP_SOC_FIP_PFMID"].lower(), get_fip_pfmid.lower()), GREEN)
            
    elif type == "NITRO":
        #check cerberus NITRO_PFMID
        ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_cerberus_pfm_chk.format(1), 3, log_path)
        if ret != 0:
            sendlog("[RACKSN:{0} SN:{1}] Can not get cerberus provision status!".format(sn_info_list["RACKSN"], sn_info_list["sn"]))
            return 1
        get_nitro_pfmid = ""
        for line in res.splitlines():
            if  "Cerberus PFM ID:" in line:
                get_nitro_pfmid = line.split()[3]
                sendlog ("[RACKSN:{0} SN:{1}] get_nitro_pfmid:{2}".format(sn_info_list["RACKSN"], sn_info_list["sn"], get_nitro_pfmid))
            elif "No valid PFM found" in line:
                sendlog ("[RACKSN:{0} SN:{1}] Cerberus NITRO No PFM".format(sn_info_list["RACKSN"], sn_info_list["sn"]))
                return 2
            
        if sn_info_list["CP_SOC_NITRO_PFMID"].lower() != get_nitro_pfmid.lower():
            sendlog("[RACKSN:{0} SN:{1}]SoC NITRO PFMID check FAIL ! exp:{2}, get:{3}".format(sn_info_list["RACKSN"],sn_info_list["sn"],sn_info_list["CP_SOC_NITRO_PFMID"].lower(), get_nitro_pfmid.lower()), RED)
            return 2
        else:
            sendlog("[RACKSN:{0} SN:{1}]SoC NITRO PFMID check PASS ! exp:{2}, get:{3}".format(sn_info_list["RACKSN"].lower(),sn_info_list["sn"],sn_info_list["CP_SOC_NITRO_PFMID"], get_nitro_pfmid.lower()), GREEN)
        
    #Disconnect other device
    # if disconnect_cp_by_rm(ssh_object, sn_info_list) == 1:
    # 	return 1
    
    sendlog("[RACKSN:{0} SN:{1}] CP {2} is Active~~".format(sn_info_list["RACKSN"], sn_info_list["sn"], type))
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
        sendlog("[RACKSN:{0} SN:{1}] Can not get cerberus provision status!".format(sn_info_list["RACKSN"], sn_info_list["sn"]))
        return 1
    
    if "Device Certificate State" not in res: #20230803 David add
        sendlog("[RACKSN:{0} SN:{1}] Cannot get cerberus provision status. res:{2}".format(sn_info_list["RACKSN"], sn_info_list["sn"], res))
        return 1
        
    for line in res.splitlines():
        if  "Device Certificate State: Device certificate chain is incomplete or invalid" in line: # 20230724 David remove error code message
            sendlog("[RACKSN:{0} SN:{1}]  Not Provision! {2}".format(sn_info_list["RACKSN"], sn_info_list["sn"], line))
            return 1
    
    #Disconnect other device
    if disconnect_cp_by_rm(None, sn_info_list) == 1:
        return 1
    ssh_object.logout() #logout current RM session
    
    sendlog("[RACKSN:{0} SN:{1}] CP is Provision~~".format(sn_info_list["RACKSN"], sn_info_list["sn"]))
    return 0

#*****************************************************************************
# Function	 : do_cp_provision
# Description: Do CP provision
# Inputs	 : sn_info_list: SN list information
# Outputs	 : 0 - provision success
#			 : 1 - do provision fail
# Notice	 : NA
#*****************************************************************************
def do_cp_provision(sn_info_list):
    sendlog("[RACKSN:{0} SN:{1}] do cp provision!".format(sn_info_list["RACKSN"], sn_info_list["sn"]))
    #Sai modify .log to .txt
    try:#20230728 David add try except for run crash
        prov_file = "{0}/{1}.txt".format(g_win_prov_folder, sn_info_list["CP_SN"])

        if not os.path.isfile(prov_file):
            sendlog("[RACKSN:{0} SN:{1}] There is no key file in {2} folder!!".format(sn_info_list["RACKSN"],sn_info_list["sn"],g_win_prov_folder),"FAIL")
            return 1	
        cfg = cfg_parser_file(prov_file)
        print (cfg)
        if cfg == 1 : 
            sendlog ("[RACKSN:{0} SN:{1}] Cant get the key!! please check it .".format(sn_info_list["RACKSN"],sn_info_list["sn"]), "FAIL")
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
                        
        sendlog ("[RACKSN:{0} SN:{1}] key file is ready.".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
        
        # Compare Public Key
        if compare_public_key(sn_info_list)!=0:
            sendlog("[RACKSN:{0} SN:{1}] Cerberus Public Key Check FAIL.".format(sn_info_list["RACKSN"],sn_info_list["sn"]),"FAIL")
            return 1

        # Fuse Certificate
        ## Device ID: HWKey1
        if cerberus_fuse (sn_info_list,0, 1):
            sendlog ("[RACKSN:{0} SN:{1}] Device ID fuse certificate success.".format(sn_info_list["RACKSN"],sn_info_list["sn"]), "PASS")
        else:
            sendlog ("[RACKSN:{0} SN:{1}] Device ID fuse certificate fault.".format(sn_info_list["RACKSN"],sn_info_list["sn"]), "FAIL")
            return 1
        
        ## Root CA: HWKey3
        if cerberus_fuse (sn_info_list,1, 3):
            sendlog ("[RACKSN:{0} SN:{1}] Root CA fuse certificate success.".format(sn_info_list["RACKSN"],sn_info_list["sn"]), "PASS")
        else:
            sendlog ("[RACKSN:{0} SN:{1}] Root CA fuse certificate fault.".format(sn_info_list["RACKSN"],sn_info_list["sn"]), "FAIL")
            return 1

        ## Intermediate CA: HWKey2
        if cerberus_fuse (sn_info_list,2, 2):
            sendlog ("[RACKSN:{0} SN:{1}] Intermediate CA fuse certificate success.".format(sn_info_list["RACKSN"],sn_info_list["sn"]), "PASS")
        else:
            sendlog ("[RACKSN:{0} SN:{1}] Intermediate CA fuse certificate fault.".format(sn_info_list["RACKSN"],sn_info_list["sn"]), "FAIL")
            return 1
        
        if is_provision(sn_info_list) != 0:
            sendlog ("[RACKSN:{0} SN:{1}] Cerberus Provision Fail.".format(sn_info_list["RACKSN"],sn_info_list["sn"]), "FAIL")
            return 1
    except:
        sendlog ("[RACKSN:{0} SN:{1}] Cerberus Provision Fail. function crash".format(sn_info_list["RACKSN"],sn_info_list["sn"]), "FAIL")
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

    sendlog("[RACKSN:{0} SN:{1}] pub_file location:{2}".format(sn_info_list["RACKSN"], sn_info_list["sn"], pub_file))	
    if not os.path.isfile(pub_file):
        sendlog ("[RACKSN:{0} SN:{1}] SF Public Key file does not exist: {2}".format(sn_info_list["RACKSN"], sn_info_list["sn"], pub_file), "FAIL")
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
        sendlog("[RACKSN:{0} SN:{1}] Execute cerberus exportcsr fail!DBG:{2}".format(sn_info_list["RACKSN"], sn_info_list["sn"],res))
        return False
    else:
        sendlog("[RACKSN:{0} SN:{1}] Execute cerberus exportcsr PASS!DBG:{2}".format(sn_info_list["RACKSN"], sn_info_list["sn"],res))
    
    #Find CP SOC IP
    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, "ifconfig", 0, log_path)
    if ret != 0:
        return 1, None
    if res != "":
        for line in res.splitlines():
            # if "inet addr:" in line:
            if "inet" in line and "inet6" not in line: #20230927 david change query message, os change
                if "127.0.0.1" in line:
                    continue
                if "addr:" in line:
                    CP_IP = line.split()[1].split(":")[1]
                else:
                    CP_IP = line.split()[1]
                ret = os.system(g_cmd_ping.format(CP_IP))
                if ret == 0:
                    sendlog("[RACKSN:{0} SN:{1}] Get_CP_IP IP = {2}".format(sn_info_list["RACKSN"], sn_info_list["sn"],CP_IP),"PASS")
                    break
    #Copy public key to local
    send_file_from_console(CP_IP, "/tmp/{0}.bin".format(sn_info_list["CP_SN"]), g_win_prov_folder,sn_info_list)
    
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
    
    #Disconnect other device
    if disconnect_cp_by_rm(None, sn_info_list) == 1:
        return 1
    ssh_object.logout() #logout current RM session

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
                # if "inet addr:" in line and "127.0.0.1" not in line:
                if "inet" in line and "inet6" not in line: #20230927 david change query message, os change
                    if "127.0.0.1" in line:
                        continue
                    if "addr:" in line:
                        CP_IP = line.split()[1].split(":")[1]
                    else:
                        CP_IP = line.split()[1]
                    ret = os.system(g_cmd_ping.format(CP_IP))
                    if ret == 0:
                        sendlog("Get_CP_IP IP = {0}".format(CP_IP),"PASS")
                        break
            retry += 1
    
    ###send HWKEY bin to console    
    send_file_to_console(CP_IP,key_file_bin,g_cp_tmp,sn_info_list)
    
    # Do Fuse Certification
    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_cerberus_prov_import.format(cert_idx, key_file_bin_soc), 5, log_path)
    if ret != 0:
        sendlog("[RACKSN:{0} SN:{1}] Execute cerberus importsignedcert fail!DBG:{2}".format(sn_info_list["RACKSN"], sn_info_list["sn"], res))
        return False
    else:
        sendlog("[RACKSN:{0} SN:{1}] Execute cerberus importsignedcert PASS!DBG:{2}".format(sn_info_list["RACKSN"], sn_info_list["sn"], res))
    
    #Disconnect other device
    if disconnect_cp_by_rm(None, sn_info_list) == 1:
        return 1
    ssh_object.logout() #logout current RM session
        
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
# Function   : remove_auto_reconfig_file()
# Description: remove auto reconfig file
# Inputs     : 
# Outputs    : 
# Notice     : 20231102 David add
#*****************************************************************************
def remove_auto_reconfig_file(sn_info_list):
    sn_log_folder = "{0}/{1}".format(g_log_folder, sn_info_list["sn"])
    log_name = "{0}_cp_auto_reconfig.log".format(sn_info_list["sn"])
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
    
    
    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_remove_auto_reconfig, 0, log_path)
    if ret != 0:
        sendlog("[RACKSN:{0} SN:{1}] Remove {2} fail!!DBG:{3}".format(sn_info_list["RACKSN"], sn_info_list["sn"],auto_reconfig_service_soc_loc,res))
        return 1
    
    #check auto reconfig exist
    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_find_auto_service, 0, log_path)
    if ret != 0:
        return 1	
    if auto_reconfig_service_soc_loc in res:
        sendlog("[RACKSN:{0} SN:{1}] File {2} still exist at soc.".format(sn_info_list["RACKSN"],sn_info_list["sn"],auto_reconfig_soc_loc))
        return 1
    elif "@localhost:" not in res:
        sendlog("[RACKSN:{0} SN:{1}] No response from CP".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
        return 1
    
    #load driver
    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_install_catapult_driver, 0, log_path)
    if ret != 0:
        sendlog("[RACKSN:{0} SN:{1}] Load capatule driver fail!!DBG:{2}".format(sn_info_list["RACKSN"], sn_info_list["sn"],res))
        return 1
    
    #reconfig golden
    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_reconfigGolden, 0, log_path)
    if ret != 0:
        sendlog("[RACKSN:{0} SN:{1}] Reconfig Golden fail!!DBG:{2}".format(sn_info_list["RACKSN"], sn_info_list["sn"],res))
        return 1
    sendlog("[RACKSN:{0} SN:{1}] CP FPGA has been reconfig to golden mode, create power cycle flag!".format(sn_info_list["RACKSN"], sn_info_list["sn"]))
    gs_exec_cmd("touch {0}/{1}_reboot".format(sn_log_folder, sn_info_list["sn"]))

    #Reboot the SoC
    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_reboot, 60, log_path)
    if ret != 0:
        return 1

    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, " ", 10, log_path)
    if ret != 0:
            return 1
    else:
        if res !="":
            #print "DBG:{0}".format(res)
            if "@localhost:" in res.split("\n")[-1]:
                sendlog("[RACKSN:{0} SN:{1}] Reboot SOC success !".format(sn_info_list["RACKSN"],sn_info_list["sn"])) 
            else:
                time.sleep(10)
                ret, res = send_cmd_to_cp(ssh_object, sn_info_list, " ", 3, log_path)
                if ret != 0:
                    return 1
                else:
                    if res !="":
                        if "@localhost:" in res.split("\n")[-1]:
                            sendlog("[RACKSN:{0} SN:{1}] After Wait 10 second! Reboot SOC success !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                        else:
                            sendlog("[RACKSN:{0} SN:{1}] After Wait 10 second! Reboot SOC fail!".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                            return 1
                    else:
                        sendlog("[RACKSN:{0} SN:{1}] Can not get result - After reboot SOC!!".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                        return 1
        else:
            sendlog("[RACKSN:{0} SN:{1}] Can not get result - After reboot SOC!!".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
            return 1

    #Disconnect other device
    if disconnect_cp_by_rm(None, sn_info_list) == 1:
        return 1
    ssh_object.logout() #logout current RM session
    
    return 0

#*****************************************************************************
# Function   : create_auto_reconfig_file()
# Description: create auto reconfig file
# Inputs     : 
# Outputs    : 
# Notice     : 20231102 David add
#*****************************************************************************
def create_auto_reconfig_file(sn_info_list):
    sn_log_folder = "{0}/{1}".format(g_log_folder, sn_info_list["sn"])
    log_name = "{0}_cp_auto_reconfig.log".format(sn_info_list["sn"])
    log_path = "{0}/{1}".format(sn_log_folder, log_name)
    CP_IP=""
    
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
    
    #check auto reconfig exist
    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_find_auto_service, 0, log_path)
    if ret != 0:
        return 1, None
    
    if auto_reconfig_service_soc_loc in res:
        sendlog("[RACKSN:{0} SN:{1}] File {2} exist at soc.".format(sn_info_list["RACKSN"],sn_info_list["sn"],auto_reconfig_service_soc_loc))
        ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_find_auto_python, 0, log_path)
        if ret != 0:
            return 1, None
        if auto_reconfig_python_soc_loc in res:
            sendlog("[RACKSN:{0} SN:{1}] File {2} exist at soc.".format(sn_info_list["RACKSN"],sn_info_list["sn"],auto_reconfig_python_soc_loc))
            if is_cp_golden_mode(sn_info_list) == 2:
                try:
                    if not sn_info_list["is_reconfig"]:
                        sendlog("[rm_ip:{0:>12} rm_mac: {1} rm_port: {2} RACKSN:{3} SN:{4}]do reconfig Celestial Peak.".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"], sn_info_list["uut_to_rm_port"],sn_info_list["RACKSN"],sn_info_list["sn"]))
                        sendlog("[RACKSN:{0} SN:{1}] Need reconfig Celestial Peak".format(sn_info_list["RACKSN"],sn_info_list["sn"]), 0, log_path)
                        # ssh_object.sendline(g_cmd_install_catapult_driver)
                        # ssh_object.prompt()
                        # ssh_object.sendline(g_cmd_reconfigapp)
                        # ssh_object.prompt()
                        # sendlog(ssh_object.before.decode ('utf-8').replace("'",''), 0, log_path)
                        ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_install_catapult_driver+';'+g_cmd_reconfigapp, 0, log_path)
                        sendlog(res.replace("'",''), 0, log_path)
                        if sn_info_list["STATION"] == "PRETEST" or sn_info_list["STATION"] == "TOR":
                            log_type="PASS"
                            message = "CP reconfig FINISH !"
                            start_time=time.strftime("%Y%m%d%H%M%S")
                            log_file =""
                            send_data_sf(start_time,message, log_type, sn_info_list["sn"], sn_info_list["LOCATION"], sn_info_list["STATION"], log_file)
                        return 0
                    else:
                        return 0
                except pxssh.ExceptionPxssh as e:
                    sendlog("[rm_ip:{0:>12} rm_mac: {1} rm_port: {2} RACKSN:{3} SN:{4}]pxssh failed: reconfig Celestial Peak.".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"], sn_info_list["uut_to_rm_port"],sn_info_list["RACKSN"],sn_info_list["sn"]), RED)
                    sendlog(e, RED)
                    return 1
            else:
                sendlog("[RACKSN:{0} SN:{1}] Auto reconfig PASS!!".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                return 0
            
    sendlog("[RACKSN:{0} SN:{1}] Create auto reconfig Celestial Peak".format(sn_info_list["RACKSN"],sn_info_list["sn"]), 0)
    #Find CP SOC IP
    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, "ifconfig", 0, log_path)
    if ret != 0:
        return 1, None
    retry = 0 #20230724 David add retry
    if res != "":
        while CP_IP == "" and retry < 3:
            for line in res.splitlines():
                # if "inet addr:" in line and "127.0.0.1" not in line:
                if "inet" in line and "inet6" not in line: #20230927 david change query message, os change
                    if "127.0.0.1" in line:
                        continue
                    if "addr:" in line:
                        CP_IP = line.split()[1].split(":")[1]
                    else:
                        CP_IP = line.split()[1]
                    ret = os.system(g_cmd_ping.format(CP_IP))
                    if ret == 0:
                        sendlog("Get_CP_IP IP = {0}".format(CP_IP),"PASS")
                        break
            retry += 1
    
    ###send auto_reconfig_service to console
    send_file_to_console(CP_IP,auto_reconfig_service_server_loc,g_cp_tmp,sn_info_list)
            
    ###send auto_reconfig_python to console
    send_file_to_console(CP_IP,auto_reconfig_python_server_loc,g_cp_tmp,sn_info_list)
    
    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_mkdir_service_loc_path, 5, log_path)
    if ret != 0:
        sendlog("[RACKSN:{0} SN:{1}] Create service path fail!DBG:{2}".format(sn_info_list["RACKSN"], sn_info_list["sn"], res))
        return 1
    else:
        sendlog("[RACKSN:{0} SN:{1}] Create service path PASS!DBG:{2}".format(sn_info_list["RACKSN"], sn_info_list["sn"], res))
    
    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_copy_auto_service_to_loc_path, 5, log_path)
    if ret != 0:
        sendlog("[RACKSN:{0} SN:{1}] Copy SoCFPGATestSvc.service file fail!DBG:{2}".format(sn_info_list["RACKSN"], sn_info_list["sn"], res))
        return 1
    else:
        sendlog("[RACKSN:{0} SN:{1}] Copy SoCFPGATestSvc.service file PASS!DBG:{2}".format(sn_info_list["RACKSN"], sn_info_list["sn"], res))
    
    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_copy_auto_python_to_loc_path, 5, log_path)
    if ret != 0:
        sendlog("[RACKSN:{0} SN:{1}] Copy SoCFPGATestSvc.service file fail!DBG:{2}".format(sn_info_list["RACKSN"], sn_info_list["sn"], res))
        return 1
    else:
        sendlog("[RACKSN:{0} SN:{1}] Copy SoCFPGATestSvc.service file PASS!DBG:{2}".format(sn_info_list["RACKSN"], sn_info_list["sn"], res))

    #Reboot the SoC
    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_reboot, 60, log_path)
    if ret != 0:
        return 1
    
    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, " ", 10, log_path)
    if ret != 0:
            return 1
    else:
        if res !="":
            #print "DBG:{0}".format(res)
            if "@localhost:" in res.split("\n")[-1]:
                sendlog("[RACKSN:{0} SN:{1}] Reboot SOC success !".format(sn_info_list["RACKSN"],sn_info_list["sn"])) 
            else:
                time.sleep(10)
                ret, res = send_cmd_to_cp(ssh_object, sn_info_list, " ", 3, log_path)
                if ret != 0:
                    return 1
                else:
                    if res !="":
                        if "@localhost:" in res.split("\n")[-1]:
                            sendlog("[RACKSN:{0} SN:{1}] After Wait 10 second! Reboot SOC success !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                        else:
                            sendlog("[RACKSN:{0} SN:{1}] After Wait 10 second! Reboot SOC fail!".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                            return 1
                    else:
                        sendlog("[RACKSN:{0} SN:{1}] Can not get result - After reboot SOC!!".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                        return 1
        else:
            sendlog("[RACKSN:{0} SN:{1}] Can not get result - After reboot SOC!!".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
            return 1

    #Disconnect other device
    if disconnect_cp_by_rm(None, sn_info_list) == 1:
        return 1
    ssh_object.logout() #logout current RM session

    time.sleep(15)
    if is_cp_golden_mode(sn_info_list) == 2:
        sendlog("[RACKSN:{0} SN:{1}] Auto reconfig FAIL!!".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
        return 1
    else:
        sendlog("[RACKSN:{0} SN:{1}] Auto reconfig PASS!!".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
        return 0

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
        
        sn_log_folder = "{0}/{1}".format(g_log_folder, sn_info_list["sn"])
        log_name = "{0}_update_flag.log".format(sn_info_list["CP_SN"]) # 20240329 David modify to CP SN for prevent replace card not updating
        update_flag = "{0}/{1}".format(sn_log_folder, log_name)
        
        rm_flag_name = "{0}_rm_update_flag_{1}.log".format(sn_info_list["RACKSN"], sn_info_list["master_rm_port"])
        rm_updated_flag = "{0}/{1}".format(g_log_folder, rm_flag_name)
        
        ##enhance flow
        updating_log_name = "{0}_updating.log".format(sn_info_list["sn"])
        updating_flag = "{0}/{1}".format(sn_log_folder, updating_log_name)
        
        golden_log_name = "{0}_do_record_cp_golden_image_version.log".format(sn_info_list["sn"])
        golden_log_path = "{0}/{1}".format(sn_log_folder, golden_log_name)
    
        if not os.path.isfile(updating_flag):
            os.system("touch {0}".format(updating_flag))
            
            ret = check_version_in_log(sn_info_list, sn_log_folder)
            os.system("rm -rf {0}".format(updating_flag))
            if ret != 0:
                return 1
        
        if sn_info_list["is_reconfig"]:
            if not os.path.isfile(update_flag):
                sendlog(sn_info_list["sn"] + " need to check fw and update")
            elif not os.path.isfile(golden_log_path) and sn_info_list["STATION"] == "PRETEST":
                sendlog(sn_info_list["sn"] + " need do record golden log.")
            else:
                sendlog(sn_info_list["sn"] + " reconfig finish")
                return 0
        sendlog("[RACKSN:{0} SN:{1}] start to do soc fw chk and then reconfig!!".format(sn_info_list["RACKSN"], sn_info_list["sn"]))
        
        try:
            os.makedirs(sn_log_folder)
            sendlog("[RACKSN:{0} SN:{1}] make log folder ({2}) success".format(sn_info_list["RACKSN"], sn_info_list["sn"],sn_log_folder), GREEN)
        except OSError as e:
            if e.errno == errno.EEXIST:
                sendlog("[RACKSN:{0} SN:{1}] log folder ({2}) exist".format(sn_info_list["RACKSN"], sn_info_list["sn"],sn_log_folder), GREEN)
            else:
                sendlog("[RACKSN:{0} SN:{1}] {2}".format(sn_info_list["RACKSN"], sn_info_list["sn"],e))
                return 1
        
        if not os.path.isfile(updating_flag):
            os.system("touch {0}".format(updating_flag))
            
            if sn_info_list["STATION"] == "PRETEST" or sn_info_list["STATION"] == "TOR":
                if sn_info_list["LOCATION"] == sn_info_list["master_rm_port"]:
                    ret=update_rm_fw(sn_info_list)
                    if ret == 0:
                        os.system("touch {0}".format(rm_updated_flag))
                    else:
                        msg = "Update RM Fw FAIL !"
                        sendlog("[RACKSN:{0} SN:{1}] {2}".format(sn_info_list["RACKSN"],sn_info_list["sn"], msg))
                        send_data_sf(time.strftime("%Y%m%d%H%M%S"),msg, "WARNING", sn_info_list["sn"], sn_info_list["LOCATION"], sn_info_list["STATION"], "")
                        clear_flag(sn_info_list)
                        return 1 
                else:
                    while not os.path.isfile(rm_updated_flag):
                        sendlog("[RACKSN:{} SN:{}] rm_updated_flag:{}".format(sn_info_list["RACKSN"], sn_info_list["sn"], rm_updated_flag))
                        sendlog("[RACKSN:{0} SN:{1}] waiting for Master UUT upload RM FW~~~~~~~~~".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                        time.sleep(60)
                                    
            if not os.path.isfile(update_flag):
                if sn_info_list["STATION"] == "PRETEST" or sn_info_list["STATION"] == "TOR":
                    log_type="START"
                    message = "Start to do CP reconfig and update!"
                    start_time=time.strftime("%Y%m%d%H%M%S")
                    log_file =""
                    send_data_sf(start_time,message, log_type, sn_info_list["sn"], sn_info_list["LOCATION"], sn_info_list["STATION"], log_file)
                    if remove_auto_reconfig_file(sn_info_list) != 0: #20231102 David add
                        msg = "remove_auto_reconfig_file FAIL !"
                        sendlog("[RACKSN:{0} SN:{1}] {2}".format(sn_info_list["RACKSN"],sn_info_list["sn"], msg))
                        send_data_sf(time.strftime("%Y%m%d%H%M%S"),msg, "WARNING", sn_info_list["sn"], sn_info_list["LOCATION"], sn_info_list["STATION"], "")
                        clear_flag(sn_info_list)
                        return 1
                    ##about 8 minutes 
                    if is_provision(sn_info_list) != 0:
                        if do_cp_provision(sn_info_list) != 0:
                            msg = "CP Provision FAIL !"
                            send_data_sf(time.strftime("%Y%m%d%H%M%S"),msg, "WARNING", sn_info_list["sn"], sn_info_list["LOCATION"], sn_info_list["STATION"], "")
                            clear_flag(sn_info_list)
                            return 1
                    send_data_sf(time.strftime("%Y%m%d%H%M%S"),"CP provision finish! Start to do soc fw chk and active CP in SOC update", "RUNNING", sn_info_list["sn"], sn_info_list["LOCATION"], sn_info_list["STATION"], "")
                    sendlog("[RACKSN:{0} SN:{1}] CP is provision! Start to do soc fw chk and active CP in SOC update~~~".format(sn_info_list["RACKSN"],sn_info_list["sn"]))

                    if do_soc_fw_chk(sn_info_list) != 0:
                        msg = "do_soc_fw_chk FAIL !"
                        sendlog("[RACKSN:{0} SN:{1}] {2}".format(sn_info_list["RACKSN"],sn_info_list["sn"], msg))
                        send_data_sf(time.strftime("%Y%m%d%H%M%S"),msg, "WARNING", sn_info_list["sn"], sn_info_list["LOCATION"], sn_info_list["STATION"], "")
                        clear_flag(sn_info_list)
                        return 1
                    send_data_sf(time.strftime("%Y%m%d%H%M%S"),"CP SOC check finish! Start to do fpga fw chk and update", "RUNNING", sn_info_list["sn"], sn_info_list["LOCATION"], sn_info_list["STATION"], "")
                    sendlog("[RACKSN:{0} SN:{1}] CP SOC is right FW version~~~".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                    
                    if do_cp_fpga_upgrade (sn_info_list) != 0:
                        msg = "do_cp_fpga_upgrade FAIL !"
                        send_data_sf(time.strftime("%Y%m%d%H%M%S"),msg, "WARNING", sn_info_list["sn"], sn_info_list["LOCATION"], sn_info_list["STATION"], "")
                        clear_flag(sn_info_list)
                        return 1
                    sendlog("[RACKSN:{0} SN:{1}] CP FPGA is right FW version~~~".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
            
                    log_type="RUNNING"
                    message = "Start to do record CP and reconfig !"
                    start_time=time.strftime("%Y%m%d%H%M%S")
                    log_file =""
                    send_data_sf(start_time,message, log_type, sn_info_list["sn"], sn_info_list["LOCATION"], sn_info_list["STATION"], log_file)

            #20230824 David modify to check network again
            sendlog("get uut ip: [{0}]{1}".format(sn_info_list["LOCATION"],sn_info_list["sn"]))
            sn_info_list["uut_ip"] = get_ip(sn_info_list["uut_mac_addr"])

            if not os.path.isfile(update_flag):
                os.system("touch {0}".format(update_flag))
                if sn_info_list["STATION"] == "PRETEST" or sn_info_list["STATION"] == "TOR":
                    log_type="PASS"
                    message = "CP update FINISH !"
                    start_time=time.strftime("%Y%m%d%H%M%S")
                    log_file =""
                    send_data_sf(start_time,message, log_type, sn_info_list["sn"], sn_info_list["LOCATION"], sn_info_list["STATION"], log_file)
                if create_auto_reconfig_file(sn_info_list) != 0: #20231102 David add auto reconfig
                    sendlog("[RACKSN:{0}, SN: {1}] create auto reconfig file FAIL".format(sn_info_list["RACKSN"], sn_info_list["sn"]), RED)
            os.system("rm -rf {0}".format(updating_flag))
        else: #isfile(updating_flag)
            #handle the case that stuck in checking RM
            if sn_info_list["STATION"] == "PRETEST":
                if not os.path.isfile(rm_updated_flag):
                    ret=is_rm_updated(sn_info_list)
                    if ret == 0:
                        if sn_info_list["LOCATION"] == sn_info_list["master_rm_port"]:					
                            remove_uuts_flag(sn_info_list["RACKSN"])
                            os.system("touch {0}".format(rm_updated_flag))
            check_flag(sn_info_list)
            sendlog("[RACKSN:{0} SN:{1}]doing update~~~".format(sn_info_list["RACKSN"],sn_info_list["sn"]), GREEN)

        if not os.path.isfile(updating_flag):
            os.system("touch {0}".format(updating_flag))
            log_name = "{0}_chk_fpga_fw.log".format(sn_info_list["sn"])
            log_path = "{0}/{1}".format(sn_log_folder, log_name)
            #Check reconfig flag
            if not os.path.isfile(golden_log_path) and sn_info_list["STATION"] == "PRETEST" and os.path.isfile(log_path):
                
                if remove_auto_reconfig_file(sn_info_list) != 0: #20231102 David add
                    msg = "remove_auto_reconfig_file FAIL !"
                    sendlog("[RACKSN:{0} SN:{1}] {2}".format(sn_info_list["RACKSN"],sn_info_list["sn"], msg))
                    send_data_sf(time.strftime("%Y%m%d%H%M%S"),msg, "WARNING", sn_info_list["sn"], sn_info_list["LOCATION"], sn_info_list["STATION"], "")
                    clear_flag(sn_info_list)
                    return 1
                
                if do_record_cp_and_reconfig(sn_info_list) != 0:
                    sendlog("[RACKSN:{0} SN:{1}] do_record_cp_and_reconfig FAIL !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                    clear_flag(sn_info_list)
                    return 1

            if sn_info_list["uut_ip"] == 1 or sn_info_list["uut_ip"] == "":	
                if create_auto_reconfig_file(sn_info_list) != 0: #20231102 David add auto reconfig
                    sendlog("[RACKSN:{0}, SN: {1}] create auto reconfig file FAIL".format(sn_info_list["RACKSN"], sn_info_list["sn"]), RED)
                    os.system("rm -rf {0}".format(updating_flag))
                    return 1

            reboot_flag = "{0}/{1}_reboot".format(sn_log_folder, sn_info_list["sn"])
            if os.path.isfile(reboot_flag):
                sendlog("[RACKSN:{0} SN:{1}] reboot flag found! Going to power cycle".format(sn_info_list["RACKSN"], sn_info_list["sn"]))
                
                ssh_object = login_rm(sn_info_list)
                if ssh_object == None:
                    gs_exec_cmd("rm -rf {0}".format(updating_flag))
                    return 1
                ret, res = send_cmd_to_rm(ssh_object, sn_info_list, g_cmd_set_cmd.format(sn_info_list["uut_to_rm_port"], "power cycle"), 0)
                if ret != 0:
                    gs_exec_cmd("rm -rf {0}".format(updating_flag))
                    return 1
                else:
                    gs_exec_cmd("rm -rf {0}".format(reboot_flag))
                
            os.system("rm -rf {0}".format(updating_flag))

        
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

    if not os.path.exists("/home/Monitor_reconfig_CP"): #20231102 David add
        os.system("mkdir /home/Monitor_reconfig_CP")
    
    if not os.path.isfile(auto_reconfig_service_server_loc):
        sendlog("File {} not exist, please check it!!".format(auto_reconfig_service_server_loc))
        sys.exit(1)
    
    if not os.path.isfile(auto_reconfig_python_server_loc):
        sendlog("File {} not exist, please check it!!".format(auto_reconfig_python_server_loc))
        sys.exit(1)

    show_info()

    if build_side != "QMF":			
        while True:
            #initialize
            print("rm -rf /root/.ssh/known_hosts...")
            os.system("rm -rf /root/.ssh/known_hosts")

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
                    
            time.sleep(600)
            print("==============next loop for cp_reconfig===================")
            print("==============next loop for cp_reconfig===================")
            print("==============next loop for cp_reconfig===================")
            os.system("cp -f /var/lib/dhcpd/dhcpd.leases /project/ ")
    else:
        #initialize
        print("rm -rf /root/.ssh/known_hosts...")
        os.system("rm -rf /root/.ssh/known_hosts")

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
            #if "P90265195003001E" not in sf_file_list[i]:
               # continue
            p = Process(target=check_sf_and_soc_fw_chk_and_reconfig_cp_chk, args=(sf_file_list[i],))
            if p != "":
                p.start()
            if i != 0 and i%11 == 0: #20230829 David add prevent server busy
                time.sleep(10)
        #20230829 David add END#######################################################################
    
        os.system("cp -f /var/lib/dhcpd/dhcpd.leases /project/ ")
        sys.exit(0)
