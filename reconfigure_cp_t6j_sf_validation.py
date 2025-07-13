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
import re

ESC_GREEN       = "\033[32m"
ESC_RED         = "\033[31m"
ESC_YELLOW_F    = "\033[33;1m"
ESC_YELLOW      = "\033[33m"
ESC_PINK        = "\033[35m"
ESC_LBLUE       = "\033[36m"
ESC_OFF         = "\033[0m"

GREEN           = 1
RED             = 2 
YELLOW          = 3
PINK            = 4
ORANGE          = 5
BLUE            = 6

PASS            = "PASS"
FAIL            = "FAIL"

g_Model = "MODEL"
g_project = "t6j"
g_log_folder = "/RACKLOG/{}/RM_logs".format(g_project) #QMF
#g_log_folder = "/mnt/test_log/{}/RM_logs".format(g_project) #QTMC
g_sf_config_folder = "/WIN/{}/sfconfig".format(g_project) #QMF2
#g_sf_config_folder = "/win/monitor/Manual/" #QTMC
#g_sf_config_folder = "monitor/" #QCI
g_win_folder = "/WIN"
g_DHCP_folder = ""
g_PXE_grub_folder = "/tftpboot/pxelinux.cfg"
g_tftp_ip = "10.0.3.254"
g_tftp_user = "root"
g_tftp_passwd = "M1cr0$0ft"
#build_side = "QTMC"
#build_side = "QCI"
build_side = "QMF"
g_reboot_flag = False
g_cp_FPGA_firmware="CelestialPeak_SysInt_{}_jic.rpd"
g_cp_FPGA_firmware_loc="/project/firmware/{}/cp/{}".format(g_project,g_cp_FPGA_firmware)
g_overlake_image_path = "/tftpboot/firmware/Celestial_Peak/dropcp-{}FW-stos{}/rMedia"
upgrade_image = "overlake-{}-prod.img"
file_path = os.path.abspath(__file__)
root_path, filename = os.path.split(file_path)
g_cmd_search_ip_QCI = "grep -B2 -A1 {0} /mnt/smbfs/__DHCP/dhcp2.txt | grep \"^192\" | awk -F \":\" '{{print $1}}'"
g_cmd_search_ip_QTMC = "grep -B8 -A1 -i {0} /var/lib/dhcpd/dhcpd.leases | grep lease"
g_cmd_search_ip_QMF = "grep -B9 -A1 -i {0} /var/lib/dhcp/dhcpd.leases | grep lease"
g_cmd_search_ip_QCG = "grep -B8 -A1 -i {0} /var/lib/dhcp/dhcpd.leases | grep lease"
g_cmd_ping = "ping -c 3 {0}"
g_bsl_return_folder = "/RACKLOG/{}/BSL_return".format(g_project)
###############
##BMC command define
###############
g_bmc_username      = "admin"
g_bmc_password      = "admin"
g_bmc_port_to_CP    = "8295"

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
g_cmd_mkdir_usb_folder = "mkdir -p /tmp/usb"
g_cmd_mount_usb_folder = "mount /dev/sda1 /tmp/usb"
g_cmd_check_bin_file_exist = "ls -al /tmp/usb"
fip_fw_file = "fip.bin"
nitro_fw_file = "nitro.img"

g_cmd_set_bootmode_to_zero = "bootmode set 0"
g_cmd_reset_soc = "cerberus_utility socreset"
g_cmd_update_fpga = "fpgadiagnostics -writeFlashjic {0}"
g_cmd_cerberus_prov_chk = "cerberus_utility getcertstate"
g_cmd_cerberus_pfm_chk = "cerberus_utility pfmid {0} 0"
g_cmd_cerberus_exportcsr = "cerberus_utility exportcsr /tmp/{0}"
g_cmd_cerberus_prov_import = "cerberus_utility importsignedcert {0} /tmp/{1}"
g_stos_md5sum = {"4.4.1":"a2dccd23325b2ab000276607aa7ca098",
                 "4.4.4":"8b247aa17bf21c9b140afcf0bbd7b76f"}
g_overlake_md5sum = {"overlake-2008.6.23101601-prod.img":"784d222f1f8b233543be00c5c1c90bd3",
                     "overlake-2008.4.23031201-prod.img":"e46ab936432f817b4da8037239f44218",
                     "overlake-1908.5.22022401-prod.img":"06459d32386890fef25703de711f0fcb",
                     "overlake-2008.6.23101601-prod-stos.img":"e5075189b5e8cfdb0017e21a1d6b3d86"}


# 2023.11.13, Martin, Add Auto reconfig
####################################### 
# Celestial Peak Auto reconfig Define #
#######################################
auto_reconfig_service_server_loc = "{}/auto_reconfig/SoCFPGATestSvc.service".format(root_path)
auto_reconfig_python_server_loc = "{}/auto_reconfig/fpga.py".format(root_path)
auto_reconfig_service_soc_loc = "/vol/data/persistent/tests/systemd/SoCFPGATestSvc.service"
auto_reconfig_python_soc_loc = "/vol/data/persistent/tests/fpga.py"
auto_reconfig_soc_loc = "/vol/data/persistent/tests"
g_cmd_remove_auto_reconfig = "rm -rf {}".format(auto_reconfig_soc_loc)
g_cmd_copy_auto_service_to_loc_path = "cp -rf /tmp/SoCFPGATestSvc.service {}".format(auto_reconfig_service_soc_loc)
g_cmd_copy_auto_python_to_loc_path = "cp -rf /tmp/fpga.py {}".format(auto_reconfig_python_soc_loc)
g_cmd_find_auto_service = "find / -name *SoCFPGATestSvc.service*"
g_cmd_find_auto_python = "find / -name *fpga.py*"
g_cmd_mkdir_service_loc_path = "mkdir -p /vol/data/persistent/tests/systemd"
#######################################
# Celestial Peak Auto reconfig Define #
#######################################


#*****************************************************************************
# Function   : getresult
# Description: Get the return value, stdout, stderr from input system command 
# Inputs     : arg1: the command tobe execute
# Outputs    : return value, stdout, stderr from the result of input command
# Notice     : use subprocess.Popen(), no command result will show on screen
#*****************************************************************************
def getresult(arg1):
    print ("CMD = {0}".format(arg1))
    try:
        p = subprocess.Popen(arg1, stdout=subprocess.PIPE, shell=True, encoding="utf-8")
        (text, err) = p.communicate()
        if p.returncode != 0:
            sendlog(f"Get Result Error p return: {err}")
        res = text
    except Exception as e:
        sendlog(f"Exception: {e}")
        os.system(arg1)
    
    return res
    
#*****************************************************************************
# Function   : sendlog
# Description: Get log message then input to log file
# Inputs     : message: log message, color: defult white, file: log file name
# Outputs    : NA
# Notice     : NA
#*****************************************************************************
def sendlog(message = "", color = 0, file = "/RACKLOG/t6j/RM_logs/monitor.log"):
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
    sendlog ("\033[1;36;40m*\033[1;33;40m MSFT_Monitor_Reconfig_CP  -\033[0m  V0.16 2024/04/12 Release By Martin \033[1;36;40m*\033[0m")
    sendlog ("\033[1;36;40m*\033[1;33;40m MSFT_Monitor_Reconfig_CP  -\033[0m  V0.17 2024/09/26 Release By Weikai/Phuc \033[1;36;40m*\033[0m")
    sendlog ("\033[1;36;40m*\033[1;33;40m MSFT_Monitor_Reconfig_CP  -\033[0m  V0.18 2024/10/22 Release By Weikai \033[1;36;40m*\033[0m")
    sendlog ("\033[1;36;40m*\033[1;33;40m MSFT_Monitor_Reconfig_CP  -\033[0m  V0.19 2024/11/22 Release By Weikai \033[1;36;40m*\033[0m")
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
    mac_trans = (mac_addr[:2]+':'+mac_addr[2:4]+':'+mac_addr[4:6]+':'+mac_addr[6:8]+':'+mac_addr[8:10]+':'+mac_addr[10:12])
    mac_trans = mac_trans.lower()
    if build_side == "QTMC" or build_side == "QMF" or build_side == "QCG":
        search_ip_cmd = "grep -B8 -A1 {0} /var/lib/dhcpd/dhcpd.leases | grep lease".format(mac_trans)
        ip = getresult(search_ip_cmd)
        log = "get_ip MAC = {0}  IP ={1}".format(mac_trans,ip)
        if len(ip) >= 1 : 
            ip =  ip.strip().split("{")
            for line in ip:
                if line != "" :
                    line = line.split(" ")[1]
                    log = "get_ip MAC = {0} IP ={1}".format(mac_trans,line)
                    cmd = "ping -c 3 {0}".format(line)
                    if os.system(cmd) == 0:
                        log = "get_ip MAC = {0} IP ={1}".format(mac_trans,line)
                        sendlog(log, PASS)
                        return line
                else:
                    break
        sendlog(log, FAIL)
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
                sendlog(log, PASS)
                return tmp
        log = "get_ip  MAC = {0} IP ={1}".format(mac_trans,ip)
        sendlog(log, FAIL)
        return 1
    else:
        msg = "unknown build side"
        sendlog(msg, FAIL)
        return 1

def update_cp_fpga_fw(MBSNdict, log_path):
    cmd = "find /project/firmware/{0}/ -name *{1}*.rpd".format(g_project.lower(),MBSNdict["CP_GOLDEN_IMAGE"].split(',')[0])
    res = getresult(cmd)
    if res != "":
        g_cp_FPGA_firmware = res.split('/')[-1]
        g_cp_FPGA_firmware_loc= res.strip()
        sendlog("g_cp_FPGA_firmware_loc = {0}".format(g_cp_FPGA_firmware_loc), 0, log_path)
        sendlog("g_cp_FPGA_firmware = {0}".format(g_cp_FPGA_firmware), 0, log_path)
    result_str="Another instance of"
    while "Another instance of" in  result_str:
        cmdstr = "sshpass -p 'overlake' scp -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null {0} stuser@[{1}]:{2}".format(g_cp_FPGA_firmware_loc, MBSNdict["cp_ip"], "/tmp/")
        result = getresult(cmdstr)
        print ("result:{0}".format(result))
        result_str = result
        time.sleep(1)
    sendlog("Copy {0} to CP {1}".format(g_cp_FPGA_firmware_loc,"/tmp/"), 0, log_path)

    sendlog("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Update FPGA image".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
    cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/{}\"".format(MBSNdict["cp_ip"], g_cmd_update_fpga.format("/tmp/"+g_cp_FPGA_firmware.format(MBSNdict["CP_GOLDEN_IMAGE"][:5])))
    result = getresult(cmd)
    sendlog(result, 0, log_path)
    info = result
    if info != "":
        if "Exiting WriteFlashSlot FPGA_STATUS 0x0" in info:
            sendlog("CP FPGA image update success !", 0, log_path)
        else:
            sendlog("CP FPGA image update fail !", 0, log_path)
            return 1
    else:
        sendlog("Can't get result - CP FPGA update", 0, log_path)
        return 1
    
    return 0


def check_cp_fpga_fw(MBSNdict, mode, log_path):
    if mode == "golden":
        expfw = MBSNdict["CP_GOLDEN_IMAGE"]
        sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Change FPGA slot to Golden".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
        cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/fpgadiagnostics -reconfiggolden\"".format(MBSNdict["cp_ip"])
        swgol = getresult(cmd)
        sendlog(swgol, 0, log_path)
        time.sleep(5)
        sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] dumpHealth".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
        cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/fpgadiagnostics -dumphealth\"".format(MBSNdict["cp_ip"])
        result = getresult(cmd)
        sendlog(result, 0, log_path)
    else:
        expfw = MBSNdict["CP_FACTORY_IMAGE"]
        sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] ".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
        cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/fpgadiagnostics -reconfigApp\"".format(MBSNdict["cp_ip"])
        swapp = getresult(cmd)
        for line in swapp.split('\n'):
            if "Reconfig failed" in line:
                sendlog("Reconfig failed", 0, log_path)
                return 1
        sendlog(swapp, 0, log_path)
        time.sleep(5)
        sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] dumpHealth".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
        cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/fpgadiagnostics -dumphealth\"".format(MBSNdict["cp_ip"])
        result = getresult(cmd)
        sendlog(result, 0, log_path)
        time.sleep(5)
        sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] dumpHealth".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
        cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/fpgadiagnostics -reconfiggolden\"".format(MBSNdict["cp_ip"])
        swgol = getresult(cmd)
        sendlog(swgol, 0, log_path)


    info = result.split('\n')
    ver = ""
    role = ""
    for line in info:
        if "[FPGA-CONFIG-EX ] OK" in line:
            ver = line.split()[6].split(',')[1].split('-')[0].strip()
            role = line.split()[7].split(',')[0].split('role:')[1]
            
    get_fpga_fw_ver = ver+','+role
    sendlog("expfw = {0}, get_fpga_fw_ver = {1}".format(expfw, get_fpga_fw_ver), 0, log_path)
    if expfw != get_fpga_fw_ver:
        return 1
    return 0


def ssh_connect_to_rm(MBSNdict, cmd, rm_ip, log_location):
        sn_log_folder = "{0}/{1}".format(g_log_folder, MBSNdict["mbsn"])
        log_name = "{0}_rm_cmd.log".format(MBSNdict["mbsn"])
        log_path = "{0}/{1}".format(sn_log_folder, log_name)        
        prj_rm_pw = "$pl3nd1D"
        print ("get_rm_ip:{}".format(rm_ip))
        ret = 0
        if os.path.exists(log_path):
            os.system("rm -rf "+ log_path)
        ssh_cmd = "sshpass -p '{0}' ssh -o \"StrictHostKeyChecking no\" -c aes256-cbc root@{1} \"{2}\" > {3}".format(prj_rm_pw, rm_ip, cmd, log_path)
        #print (ssh_cmd)
        sendlog("Execute CMD: {}".format(ssh_cmd), 0, log_location)
        ret = os.system(ssh_cmd)
        if ret != 0:
            sendlog("SSH connect to RM to execute CMD: {} FAIL!".format(ssh_cmd), 0, log_location)
            return 1
        if os.path.exists(log_path):
            os.system("cat {0} >> {1}".format(log_path, log_location))

        res = -1
        with open(log_path, mode="r") as f:
            for line in f.readlines():
                if 'Completion Code:' in line:
                    res = line.find('Success')
                    break
        f.close()
        if res == -1:
            return 1
        return 0

#*****************************************************************************
# Function   : gs_get_rm_mac
# Description: Get RM mac by mapping gate way
# Inputs     : None
# Outputs    : Pass : return 0 ; Fail : return 1
# Notice     : 
#*****************************************************************************  
def gs_get_rm_mac(MBSNdict):
    sn_log_folder = "{0}/{1}".format(g_log_folder, MBSNdict["mbsn"])
    log_name = "{0}_get_rm_mac.log".format(MBSNdict["mbsn"])
    log_path = "{0}/{1}".format(sn_log_folder, log_name)
    RM_location = MBSNdict["TESTLOC"][:3]
    #RM loc mac cat 
    file_path = "/usr/local/bin/rm_mac.txt"
    rm_mac = ""
    with open(file_path, 'r') as file:
        for line in file:
            if  RM_location.upper() in line:
                rm_mac = line.split("=")[1].strip("\"")
                break
    if rm_mac == "":
        sendlog("Get RM {} MAC Fail".format(RM_location), RED, log_path)
        return 1
    else:
        sendlog("Get RM {0} MAC: {1}".format(RM_location, rm_mac), RED, log_path)
        return rm_mac

def gs_get_rm_ip(MBSNdict):
    sn_log_folder = "{0}/{1}".format(g_log_folder, MBSNdict["mbsn"])
    log_name = "{0}_get_rm_ip.log".format(MBSNdict["mbsn"])
    log_path = "{0}/{1}".format(sn_log_folder, log_name)
    mac_addr = gs_get_rm_mac(MBSNdict)
    if mac_addr == 1:
        return 1
    print (mac_addr)
    ip = "" 
    log = "get_rm_ip"
    mac_trans = (mac_addr[:2]+':'+mac_addr[2:4]+':'+mac_addr[4:6]+':'+mac_addr[6:8]+':'+mac_addr[8:10]+':'+mac_addr[10:12])
    mac_trans = mac_trans.lower()
    if build_side == "QTMC" or build_side == "QMF" or build_side == "QCG":
        if "QTMC" in build_side:
            search_ip_cmd = g_cmd_search_ip_QTMC.format(mac_trans)
        elif "QMF" in build_side:
            search_ip_cmd = g_cmd_search_ip_QMF.format(mac_trans)
        elif "QCG" in build_side:
            search_ip_cmd = g_cmd_search_ip_QCG.format(mac_trans)

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
                        sendlog("Get_IP MAC = {0} IP = {1:.<12}".format(mac_trans,line), 0, log_path)
                        return line
                else:
                    break
        sendlog(log, 0, log_path)
        return 1
    else:
        sendlog("Unknown build side", 0, log_path)
        return 1

def map_port(port_id):
    if port_id in ['04', '08', '12']:
        return 1
    elif port_id in ['03', '07', '11']:
        return 2
    elif port_id in ['02', '06', '10']:
        return 3
    elif port_id in ['01', '05', '09']:
        return 4
    else:
        return "Invalid port ID"

def gs_get_rm_port(ip,MBSNdict):
    sn_log_folder = "{0}/{1}".format(g_log_folder, MBSNdict["mbsn"])
    log_name = "{0}_get_rm_port.log".format(MBSNdict["mbsn"])
    log_path = "{0}/{1}".format(sn_log_folder, log_name)
    server_ID       = "NA"
    port_state      = "NA"
    present         = "NA"
    type            = "NA"
    completion_code = "NA"
    # uut_mac = MBSNdict["nic_mac_addr"]
    uut_mac = "{0}:{1}:{2}:{3}:{4}:{5}".format(MBSNdict["nic_mac_addr"][0:2], MBSNdict["nic_mac_addr"][2:4], MBSNdict["nic_mac_addr"][4:6], MBSNdict["nic_mac_addr"][6:8], MBSNdict["nic_mac_addr"][8:10], MBSNdict["nic_mac_addr"][10:12])
    uut_loc =  MBSNdict["TESTLOC"][-2:]
    print ("uut_mac = {0}".format(uut_mac))
    rm_show_manager_info = "show manager info"
    rm_file = "{0}/{1}_show_manager_info.txt".format(sn_log_folder,MBSNdict["mbsn"])
    sysinfo_name = "{0}_show_sys_info.log".format(MBSNdict["mbsn"])
    sysinfo_path = "{0}/{1}".format(sn_log_folder, sysinfo_name)
    # "/RACKLOG/t6j/RM_logs/monitor.log"
    # if os.path.isfile(rm_file) and i_cfg.prj_build_site != "QCI":
    # if os.path.isfile(rm_file):
    #   os.system("rm {}".format(rm_file))
    if not os.path.isfile(rm_file):
        print("creat show manager info list")
        ret = ssh_connect_to_rm(MBSNdict, rm_show_manager_info, ip, rm_file)
        if ret != 0:
            sendlog("RM shows manager info FAIL!", 0, log_path)
            return -1
    
    rm_info = ""
    if os.path.isfile(rm_file):
        fp = open(rm_file, "r")
        rm_info = fp.readlines()
        fp.close()
    else:
        sendlog("Cannot get info file from rm", 0, log_path)
        return -1
    for line in rm_info:
        line = line.strip()
        if uut_mac.upper() in line: # or uut_mac.lower() in line:
            sendlog(f"Identify The Server ID BY MAC ADDRESS-{uut_mac}", 0, log_path)
            uut_info        =   line.strip().split("| ")
            server_ID       =   uut_info[1].strip()
            port_state      =   uut_info[2].strip()
            present         =   uut_info[3].strip()
            type            =   uut_info[4].strip()
            completion_code =   uut_info[7].strip()
            break
        elif "Failure" in line:
            # 2nd checking in case the MAC ADDRESS in rm shows info which is showing failure
            server_loc = map_port(uut_loc)
            sys_show_fru = f"show system fru -i {server_loc}"
            uut_mbsn = MBSNdict['mbsn']
            ret = ssh_connect_to_rm(MBSNdict, sys_show_fru, ip, sysinfo_path)
            sys_fru=""
            if ret != 0:
                sendlog("RM show system info FAIL!", 0, log_path)
                return -1 
            else:
                if os.path.isfile(sysinfo_path):
                    fp = open(sysinfo_path, "r")
                    sys_fru = fp.readlines()
                    fp.close()
                else:
                    sendlog("Can not get info file from system",0,log_path)
                    return -1
            for line in sys_fru:
                sys_mbsn = ""
                if "Board Serial Number" in line:
                    sys_mbsn = line.split(':')[1].strip()
                    break
            if sys_mbsn == uut_mbsn:
                sendlog(f"Identify The Server ID BY MBSN-{uut_mbsn}", 0, log_path)
                server_ID 		= 	server_loc
                port_state 		= 	"ON"
                present			= 	"True"
                type 			= 	"Server"
                completion_code = 	"Success"
                break

    log = "Get server_ID=[{0}], port_state=[{1}], resent=[{2}], type=[{3}], Completion_Code=[{4}] ".format(server_ID,port_state,present,type,completion_code) #don't need to check present
    if server_ID != "" and port_state == "ON" and type == "Server" and completion_code == "Success":
        sendlog(log, 0, log_path)
        return server_ID

    sendlog(log, 0, log_path)
    sendlog("Get RM port information not match !", 0, log_path)
    return -1


#*****************************************************************************
# Function   : send_cmd_to_rm
# Description: send cmd by rm
# Inputs     : MBSNdict: an empty array for storing SN info, cmd, log_location
# Outputs    : 0: PASS
#            : 1: FAIL
# Notice     : NA
#*****************************************************************************
def send_cmd_to_rm(MBSNdict, cmd, log_location):
    rm_ip = gs_get_rm_ip(MBSNdict)
    if rm_ip == 1:
        return 2

    rm_port = gs_get_rm_port(rm_ip,MBSNdict)
    if rm_port == -1:
        return 3

    if cmd == "A/C":
        sendlog(f"Runnning cmd to off the port {rm_port}", 0, log_location)
        set_cmd= f"set manager port off -i {rm_port}"
        ret = ssh_connect_to_rm(MBSNdict, set_cmd, rm_ip, log_location)
        if ret != 0:
           sendlog("Fail to set manager port off!", 0, log_location)
           return 1
        time.sleep(10)
        set_cmd= f"set manager port on -i {rm_port}"
        ret = ssh_connect_to_rm(MBSNdict, set_cmd, rm_ip, log_location)
        if ret != 0:
           sendlog("Fail to set manager port on!", 0, log_location)
           return 1        
    else:
        set_cmd = f"set system cmd -i {rm_port} -c {cmd}"
        ret = ssh_connect_to_rm(MBSNdict, set_cmd, rm_ip, log_location)
        if ret != 0:
            sendlog(f"Can not execute RM cmd: {cmd}!", 0, log_location)
            return 1
    return 0

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
        if  file_name.endswith(".txt"):
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
            "CP_FPGA_FW": "",
            "CP_GOLDEN_IMAGE": "",
            "CP_FACTORY_IMAGE": "",
            "CP_SOC_OS_FW": "",
            "CP_SOC_FIP_FW": "",
            "CP_SOC_NITRO_FW": "",
            "CP_SOC_DRIVER": "",
            "CP_SOC_FIP_PFMID": "",
            "CP_SOC_NITRO_PFMID": "",
            "CP_SN": "" # 20240328 David add CP SN
        }
        bmc_mac_addr = ""
        nic_mac_addr = ""
        model_name = ""
        cp_mac_addr = ""
        real_mbsn = ""
        cp_cerberus_fw = ""
        cp_fpga_fw = ""
        cp_golden_image = ""
        cp_soc_os_fw = ""
        cp_soc_fip_fw = ""
        cp_soc_nitro_fw = ""
        test_loc = "" #Ken Add test loc to find RM
        cp_soc_fip_pfm_id = ""
        cp_soc_nitro_pfm_id = ""
        cp_sn = "" # 20240328 David add CP SN
        for file_name in info:
            if file_name.endswith(".txt") and mbsn in file_name:
                print ("file_name = {0}".format(file_name))
                file_path = "{0}/{1}".format(g_sf_config_folder, file_name)
                f = open(file_path)
                for line in f:
                    line = line.upper()
                    #for link.ini
                    if "BMC,MEMAC" in line:
                        print ("line = {0}".format(line))
                        bmc_mac_addr = line.split('=')[1].strip()
                    if "MAC,MEMAC_100G_0_2" in line:
                        print ("line = {0}".format(line))
                        nic_mac_addr = line.split('=')[1].strip()
                    #for UUTconfig2.ini
                    if "BMCMAC" in line:
                        print ("line = {0}".format(line))
                        bmc_mac_addr = line.split('=')[1].strip()
                    if "ETH0" in line: # 20220829 David fix
                        print ("line = {0}".format(line))
                        nic_mac_addr = line.split('=')[1].split(',')[0].strip()
                    if "MODEL" in line: # 20221007 David add
                        print ("line = {0}".format(line))
                        model_name = line.split('=')[1].strip()

                    if "ETH" in line and "MICROSOFT" in line: # 20221223 David add CP MAC
                        print ("line = {0}".format(line))
                        cp_mac_addr = line.split('=')[1].split(',')[0].strip()
                    if "MBSN" in line: #20221224 David add real MB SN
                        print ("line = {0}".format(line))
                        real_mbsn = line.split('=')[1].strip()
                    if "CP_CERBERUS_FW" in line:
                        print ("line = {0}".format(line.lower()))
                        cp_cerberus_fw = line.lower().split('=')[1].strip()
                    if "CP_FPGA_FW" in line:
                        print ("line = {0}".format(line.lower()))
                        cp_fpga_fw = line.lower().split('=')[1].strip()
                    if "CP_GOLDEN_IMAGE" in line:
                        print ("line = {0}".format(line.lower()))
                        cp_golden_image = line.lower().split('=')[1].strip()
                    if "CP_FACTORY_IMAGE" in line:
                        print ("line = {0}".format(line.lower()))
                        cp_factory_image = line.lower().split('=')[1].strip()
                    if "CP_SOC_OS_FW" in line:
                        print ("line = {0}".format(line.lower()))
                        cp_soc_os_fw = line.lower().split('=')[1].strip()
                    if "CP_SOC_FIP_FW" in line:
                        print ("line = {0}".format(line.lower()))
                        cp_soc_fip_fw = line.lower().split('=')[1].strip()
                    if "CP_SOC_FIP_PFMID" in line: 
                        print ("line = {0}".format(line.lower()))
                        cp_soc_fip_pfm_id = line.lower().split('=')[1].strip()
                    if "CP_SOC_NITRO_FW" in line:
                        print ("line = {0}".format(line.lower()))
                        cp_soc_nitro_fw = line.lower().split('=')[1].strip()
                    if "CP_SOC_NITRO_PFMID" in line: 
                        print ("line = {0}".format(line.lower()))
                        cp_soc_nitro_pfm_id = line.lower().split('=')[1].strip()
                    if "FPGA0" in line or "FPGASN0" in line: # 20240328 David add CP SN
                        print ("line = {0}".format(line.lower()))
                        cp_sn = line.lower().split('=')[1].strip()
                    if "TESTLOC" in line: # 20240328 David add CP SN
                        print ("line = {0}".format(line.lower()))
                        test_loc = line.lower().split('=')[1].strip()

                f.close()
        MBSNdict["mbsn"] = real_mbsn
        MBSNdict["bmc_mac_addr"] = bmc_mac_addr
        MBSNdict["nic_mac_addr"] = nic_mac_addr
        MBSNdict["cp_mac_addr"] = cp_mac_addr
        MBSNdict["CP_CERBERUS_FW"] = cp_cerberus_fw
        MBSNdict["CP_FPGA_FW"] = cp_fpga_fw
        MBSNdict["CP_GOLDEN_IMAGE"] = cp_golden_image
        MBSNdict["CP_FACTORY_IMAGE"] = cp_factory_image
        MBSNdict["CP_SOC_OS_FW"] = cp_soc_os_fw
        MBSNdict["CP_SOC_FIP_FW"] = cp_soc_fip_fw
        MBSNdict["CP_SOC_NITRO_FW"] = cp_soc_nitro_fw
        MBSNdict["CP_SN"] = cp_sn # 20240328 David add CP SN
        MBSNdict["TESTLOC"] = test_loc
        MBSNdict["CP_SOC_FIP_PFMID"] = cp_soc_fip_pfm_id
        MBSNdict["CP_SOC_NITRO_PFMID"] = cp_soc_nitro_pfm_id

        if g_project not in model_name.lower(): # 20221007 David add: Skip other project
            print ("EXP: {}, GET: {}, skip.".format(g_project, model_name.lower()))
            continue
        #get bmc ip from DHCP
        MBSNdict["bmc_ip"] = get_ip(MBSNdict["bmc_mac_addr"])
        # if MBSNdict["bmc_ip"] == "" or MBSNdict["bmc_ip"] == 1:# 20220829 David modify if BMC no resp then skip
        #   continue
        MBSNdict["cp_ip"] = get_ip(MBSNdict["cp_mac_addr"])
        skip_cpip = False# BSL reflow cp card won't have ip
        if MBSNdict["mbsn"] in bsl_return_list.keys():
            skip_cpip = True
        if (MBSNdict["cp_ip"] == "" or MBSNdict["cp_ip"] == 1) and not skip_cpip:
            continue
        MBSNdict["nic_ip"] = get_ip(MBSNdict["nic_mac_addr"])
        # for i in range(3):
        #   #get nic_ip from DHCP
        #   MBSNdict["nic_ip"] = get_ip(MBSNdict["nic_mac_addr"])
        #   if MBSNdict["nic_ip"] == "" or MBSNdict["nic_ip"] == 1:
        #       time.sleep(10)
        #   else:
        #       break
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
        sendlog("make log folder ({0}) success".format(sn_log_folder), GREEN, log_path)
    except OSError as e:
        if e.errno == errno.EEXIST:
            sendlog("log folder ({0}) exist".format(sn_log_folder), GREEN, log_path)
        else:
            sendlog("{0}".format(e), 0, log_path)
            return 1
    ret = getresult("ipmitool -H {0} -U {1} -P {2} -I lanplus power status".format(MBSNdict["bmc_ip"], g_bmc_username, g_bmc_password))
    sendlog(ret, 0, log_path)
    if ret.strip() == "Chassis Power is on":
        msg = "[mbsn:{0} bmc_ip: {1} bmc_mac: {2}] power on".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"])
        sendlog(msg, 0, log_path)
        return 0
    else:
        msg = "[mbsn:{0} bmc_ip: {1} bmc_mac: {2}]] power not on".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"])
        sendlog(msg, 0, log_path)
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
    
    try:
        os.makedirs(sn_log_folder)
        sendlog("make log folder ({0}) success".format(sn_log_folder), GREEN, log_path)
    except OSError as e:
        if e.errno == errno.EEXIST:
            sendlog("log folder ({0}) exist".format(sn_log_folder), GREEN, log_path)
        else:
            sendlog("{0}".format(e), 0, log_path)
            return 1
    
    #login to CP
    try:
        s = pxssh.pxssh()
        msg = "[mbsn:{0} bmc_ip: {1} bmc_mac: {2}] login to CP".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"])
        sendlog(msg, 0, log_path)
        s.login(MBSNdict["bmc_ip"], g_bmc_username, g_bmc_password, port=g_bmc_port_to_CP, auto_prompt_reset=False)
        s.sendline()
    except pxssh.ExceptionPxssh as e:
        sendlog("[mbsn:{0} bmc_ip: {1} bmc_mac: {2}] pxssh failed: login to CP".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"]), RED, log_path)
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
        sendlog("[mbsn:{0} bmc_ip: {1} bmc_mac: {2}] pxssh failed: can not get CP chip id".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"]), RED, log_path)
        sendlog(e, RED, log_path)
        return 1

    info = s.before.split("\n")
    CP_chip_id = ""
    for i in range(len(info)):
        if "Chip ID" in info[i]:
            line_next = info[i+1]
            CP_chip_id = line_next.split("  ")[1].strip()

    if CP_chip_id == "":
        sendlog ("[mbsn:{0} bmc_ip: {1} bmc_mac: {2}]: fail to get CP chip id".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"]), RED, log_path)
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
            sendlog("[mbsn:{0} bmc_ip: {1} bmc_mac: {2}] pxssh failed: can not send cmd- {3}".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"], action), RED, log_path)
            sendlog(e, RED, log_path)
            return 1
    try:
        s.prompt()
        sendlog(s.before, 0, log_path)
    except pxssh.ExceptionPxssh as e:
        sendlog("[mbsn:{0} bmc_ip: {1} bmc_mac: {2}] pxssh failed: record CP message".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"]), RED, log_path)
        sendlog(e, RED, log_path)
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
    
    if golen_image_role_id == golden_image_version == golden_image_build_version == "":
        msg = "[mbsn:{0} bmc_ip: {1} bmc_mac: {2}] record golden image fail".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"])
        sendlog(msg, 0, log_path)
        #s.logout()
        return 1
    msg = "[mbsn:{0} bmc_ip: {1} bmc_mac: {2}] record golden image finish, full porocess please see {3}".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"], log_path)
    sendlog(msg, 0, log_path)
    #s.logout()
    
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

    sendlog ("[mbsn: {0}, bmc_ip: {1}] DBG1===============".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"]), 0, log_path)
    try:
        os.makedirs(sn_log_folder)
        sendlog("make log folder ({0}) success".format(sn_log_folder), GREEN, log_path)
    except OSError as e:
        if e.errno == errno.EEXIST:
            sendlog("log folder ({0}) exist".format(sn_log_folder), GREEN, log_path)
        else:
            sendlog("{0}".format(e), log_path)
            return 1
    
    #login to CP
    sendlog ("[mbsn: {0}, bmc_ip: {1}] DBG2===============".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"]), 0, log_path)
    try:
        #import pdb;pdb.set_trace()
        s = pxssh.pxssh()
        s.force_password = True
        msg = "[mbsn:{0} bmc_ip: {1} bmc_mac: {2}] login to CP".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"])
        sendlog(msg, 0, log_path)
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
        sendlog("[mbsn:{0} bmc_ip: {1} bmc_mac: {2}] pxssh failed: login to CP".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"]), RED, log_path)
        sendlog(e, RED, log_path)
        #s.logout()
        return 1
    
    sendlog ("[mbsn: {0}, bmc_ip: {1}] DBG3===============".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"]), 0, log_path)
    try:
        sendlog ("[mbsn: {0}, bmc_ip: {1}] DBG4===============".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"]), 0 ,log_path)
        s.sendline('modprobe catapult')
        s.prompt()
        s.sendline('fpgadiagnostics -reconfigApp')
        s.prompt()
        sendlog ("[mbsn:{0} bmc_ip: {1} bmc_mac: {2}] do CP reconfig".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"]), 0, log_path)
        sendlog(s.before, 0, log_path)
    except pxssh.ExceptionPxssh as e:
        sendlog("[mbsn:{0} bmc_ip: {1} bmc_mac: {2}]pxssh failed: reconfig Celestial Peak.".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"]), RED, log_path)
        sendlog(e, RED, log_path)
        return 1
    
    #s.logout()
    return 0
    
def is_CP_Golden_mode(MBSNdict):
    sn_log_folder = "{0}/{1}".format(g_log_folder, MBSNdict["mbsn"])
    log_name = "{0}_check_golden_mode.log".format(MBSNdict["mbsn"])
    log_path = "{0}/{1}".format(sn_log_folder, log_name)
    record_log_name = "{0}_do_record_CP_golden_image_version.log".format(MBSNdict["mbsn"])
    record_log_path = "{0}/{1}".format(sn_log_folder, record_log_name)
    ret = -1
    # try:
    #   s = pxssh.pxssh()
    #   s.force_password = True
    #   #print "login... IP = {0}, user = {1}, password = {2}".format(MBSNdict["bmc_ip"], g_bmc_username, g_bmc_password)
    #   s.login(MBSNdict["bmc_ip"], g_bmc_username, g_bmc_password, port=g_bmc_port_to_CP, auto_prompt_reset=False)
    #   print "[mbsn:{0} bmc_ip: {1} bmc_mac: {2}] login".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"])
    #   s.sendline()

    #   #print "install catapult driver"
    #   s.sendline('modprobe catapult')
    #   print "[mbsn:{0} bmc_ip: {1} bmc_mac: {2}] load CP driver".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"])
    #   #print "dumpHealth"
    #   s.sendline('fpgadiagnostics -dumpHealth')
    #   print "[mbsn:{0} bmc_ip: {1} bmc_mac: {2}] dumpHealth".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"])
    #   s.prompt()
    # except pxssh.ExceptionPxssh, e:
    #   print str(e)
    #   sendlog("[mbsn:{0} bmc_ip: {1} bmc_mac: {2}]pxssh failed: is_CP_Golden_mode().".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"]), RED)
    #   sendlog(e, RED)
    #   #s.logout()
    #   return -1
    
    sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] load CP driver".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
    cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/sbin/modprobe catapult\"".format(MBSNdict["cp_ip"])
    # Changed ssh to null user

    result = getresult(cmd)
    sendlog(result, 0, log_path)
    if "Found no catapult devices" in result:
        sendlog("No catapult devices !!! ".format(sn_log_folder), RED, log_path)
        return 6

    sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] dumpHealth".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
    cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/fpgadiagnostics -dumphealth\"".format(MBSNdict["cp_ip"])
    # Changed ssh to null user
    result = getresult(cmd)
    sendlog(result, 0, log_path)
    info = result.split('\n')

    # info = s.before.split('\n')
    for line in info:
        if "[FPGA-CONFIG " in line:
            golden_str = line.split()[3].split(',')[0].strip()
            status = golden_str.split(':')[1]
            if status == "0":
                sendlog("[mbsn:{0} cp_ip: {1} cp_mac: {2}]: App mode".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), GREEN, log_path)
                ret = 1
                return ret
            else:
                sendlog("[mbsn:{0} cp_ip: {1} cp_mac: {2}]: Golden mode".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), GREEN, log_path)
                #ret = 0
    if "[FPGA-CONFIG " not in result:
        return ret
    if not os.path.isfile(record_log_path):
        sendlog ("{0}_do_record_CP_golden_image_version does not exist".format(MBSNdict["mbsn"]), 0, log_path)
        ###do_record_CP_golden_img_ver
        try:
            os.makedirs(sn_log_folder)
            sendlog("make log folder ({0}) success".format(sn_log_folder), GREEN, log_path)
        except OSError as e:
            if e.errno == errno.EEXIST:
                sendlog("log folder ({0}) exist".format(sn_log_folder), GREEN, log_path)
            else:
                sendlog("{0}".format(e), 0, log_path)
                return 3
        
        #get CP chip id
        # try:
        #   s.sendline("modprobe catapult")
        #   s.prompt()
        #   s.sendline("fpgadiagnostics -list")
        #   s.prompt()
        #   sendlog(s.before, 0, record_log_path)
        # except pxssh.ExceptionPxssh, e:
        #   sendlog("[mbsn:{0} bmc_ip: {1} bmc_mac: {2}] pxssh failed: can not get CP chip id".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"]), RED)
        #   sendlog(e, RED)
        #   return 3

        cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/sbin/modprobe catapult\"".format(MBSNdict["cp_ip"])
        # Changed ssh to null user
        result = getresult(cmd)
        sendlog(result, 0, log_path)
        if "Found no catapult devices" in result:
            sendlog("No catapult devices !!! ".format(sn_log_folder), RED, log_path)
            return 6

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
            sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}]: fail to get CP chip id".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), RED, log_path)
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
        #   try:
        #       s.sendline(cmd)
        #   except pxssh.ExceptionPxssh, e:
        #       sendlog("[mbsn:{0} cp_ip: {1} cp_mac: {2}] pxssh failed: can not send cmd- {3}".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"], action), RED)
        #       sendlog(e, RED)
        #       return 3
        # try:
        #   s.prompt()
        #   sendlog(s.before, 0, record_log_path)
        # except pxssh.ExceptionPxssh, e:
        #   sendlog("[mbsn:{0} cp_ip: {1} cp_mac: {2}] pxssh failed: record CP message".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), RED)
        #   sendlog(e, RED)
        #   return 3


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
        
        if golen_image_role_id == golden_image_version == golden_image_build_version == "":
            msg = "[mbsn:{0} cp_ip: {1} cp_mac: {2}] record golden image fail".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"])
            sendlog(msg, 0, log_path)
            #s.logout()
            return 3
        msg = "[mbsn:{0} cp_ip: {1} cp_mac: {2}] record golden image finish, full porocess please see {3}".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"], log_path)
        sendlog(msg, 0, log_path)
        
        chk_count = 0
        for i in range(5):
            if not os.path.isfile(record_log_path):
                sendlog ("{0}_do_record_CP_golden_image_version is not exist".format(MBSNdict["mbsn"]), 0, log_path)
                try:
                    os.makedirs(sn_log_folder)
                    sendlog("make log folder ({0}) success".format(sn_log_folder), GREEN, log_path)
                    result = write_golden_image_log_file(MBSNdict)
                    if result == 2: #No catapult devices
                        return 6
                except OSError as e:
                    if e.errno == errno.EEXIST:
                        sendlog("log folder ({0}) exist".format(sn_log_folder), GREEN, log_path)
                    else:
                        sendlog("{0}".format(e), 0, log_path)
                        return 3
            golden_image_chk_result = chk_golden_image_log_file(MBSNdict)
            if golden_image_chk_result == 0:
                chk_count += 1
                sendlog("{0}_do_record_CP_golden_image_version.log content check PASS!".format(MBSNdict["mbsn"]), 0, log_path)
                break
            else:
                sendlog("{0}_do_record_CP_golden_image_version.log content check FAIL!".format(MBSNdict["mbsn"]), 0, log_path)
                sendlog("Re-write content in {0}_do_record_CP_golden_image_version.log. Retry:{1}/5".format(MBSNdict["mbsn"], i+1), 0, log_path)
                result = write_golden_image_log_file(MBSNdict)
                if result == 2: #No catapult devices
                    return 6
        if golden_image_chk_result == 1:
            sendlog("{0}_do_record_CP_golden_image_version.log content check FAIL!".format(MBSNdict["mbsn"]), 0, log_path)
            return 4 # It means create log file fail.
        
    else:
        chk_count = 0
        for i in range(5):
            if not os.path.isfile(record_log_path):
                sendlog ("{0}_do_record_CP_golden_image_version is not exist".format(MBSNdict["mbsn"]), 0, log_path)
                try:
                    os.makedirs(sn_log_folder)
                    sendlog("make log folder ({0}) success".format(sn_log_folder), GREEN, log_path)
                    result = write_golden_image_log_file(MBSNdict)
                    if result == 2: #No catapult devices
                        return 6
                except OSError as e:
                    if e.errno == errno.EEXIST:
                        sendlog("log folder ({0}) exist".format(sn_log_folder), GREEN, log_path)
                    else:
                        sendlog("{0}".format(e), 0, log_path)
                        return 3
            golden_image_chk_result = chk_golden_image_log_file(MBSNdict)
            if golden_image_chk_result == 0:
                chk_count += 1
                sendlog("{0}_do_record_CP_golden_image_version.log content check PASS!".format(MBSNdict["mbsn"]), 0, log_path)
                break
            else:
                sendlog("{0}_do_record_CP_golden_image_version.log content check FAIL!".format(MBSNdict["mbsn"]), 0, log_path)
                sendlog("Re-write content in {0}_do_record_CP_golden_image_version.log. Retry:{1}/5".format(MBSNdict["mbsn"], i+1), 0, log_path)
                result = write_golden_image_log_file(MBSNdict)
                if result == 2: #No catapult devices
                    return 6
        if golden_image_chk_result == 1:
            sendlog("{0}_do_record_CP_golden_image_version.log content check FAIL!".format(MBSNdict["mbsn"]), 0, log_path)
            return 4 # It means create log file fail.
        sendlog ("{0}_do_record_CP_golden_image_version exist".format(MBSNdict["mbsn"]), 0, log_path)

    # try:
    #   s.sendline('fpgadiagnostics -reconfigApp')
    #   s.prompt()
    #   print "[mbsn:{0} bmc_ip: {1} bmc_mac: {2}] do CP reconfig".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"])
    #   sendlog(s.before, 0, log_path)
    #   return 1
    # except pxssh.ExceptionPxssh, e:
    #   sendlog("[mbsn:{0} bmc_ip: {1} bmc_mac: {2}]pxssh failed: reconfig Celestial Peak.".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"]), RED)
    #   sendlog(e, RED)
    #   return 2
    
    # 2024.04.11, Martin, Implement new reconfig method
    # print ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] do CP reconfig".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]))
    # cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/fpgadiagnostics -reconfigApp\"".format(MBSNdict["cp_ip"])
    # Changed ssh to null user
    # result = getresult(cmd)
    # sendlog(s.before, 0, log_path)
    # sendlog(result, 0, log_path)
    #if create_auto_reconfig_file(MBSNdict) != 0: #20231102 David add auto reconfig
    #   sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}]: create auto reconfig file FAIL".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), RED)
    #   return 2
    #return 1

    #s.logout()
    # Move create_auto_reconfig_file 
    ret = 5
    return ret
#*****************************************************************************
# Function   : chk_golden_image_log_file
# Description: check MBSN_do_record_CP_golden_image_version.log content.
#            : It should not be empty and the key information need to be include in it.
# Inputs     : MBSNdict: dictionary of SN info
# Outputs    : 0: PASS
#            : 1: FAIL
# Notice     : NA
#*****************************************************************************
def chk_golden_image_log_file(MBSNdict):
    sn_log_folder = "{0}/{1}".format(g_log_folder, MBSNdict["mbsn"])
    log_name = "{0}_chk_golden_image.log".format(MBSNdict["mbsn"])
    log_path = "{0}/{1}".format(sn_log_folder, log_name)
    record_log_name = "{0}_do_record_CP_golden_image_version.log".format(MBSNdict["mbsn"])
    record_log_path = "{0}/{1}".format(sn_log_folder, record_log_name)
    get_info = 0
    exp_info = 9
    chk_list = ["Read register 101", "Read register 65", "Read register 59", "[FPGA-CONFIG ", "[FPGA-CONFIG-EX ]", "golen_image_role_id", "golden_image_version", "golden_image_build_version"]

    if not os.path.isfile(record_log_path):
        return 1

    with open(record_log_path, 'r') as file:
        for line in file:
            for i in range(len(chk_list)):
                if chk_list[i] == "Read register 101" and chk_list[i] in line:
                    get_read_register_101 = line.split(" ")[5].strip().strip("(").strip(")")
                    sendlog(f"[Read register 101] get:{get_read_register_101} exp:{MBSNdict['CP_GOLDEN_IMAGE'].split(',')[1]}", 0 ,log_path)
                    if get_read_register_101 == (MBSNdict["CP_GOLDEN_IMAGE"].split(",")[1]):
                        get_info += 1
                    break
                if chk_list[i] == "Read register 65" and chk_list[i] in line:
                    get_read_register_65 = line.split(" ")[5].strip().strip("(").strip(")")
                    sendlog(f"[Read register 65] get:{get_read_register_65} exp:{MBSNdict['CP_FPGA_FW'].split(',')[1]}", 0 ,log_path)
                    if get_read_register_65 == (MBSNdict["CP_FPGA_FW"].split(",")[1]):
                        get_info += 1
                    break
                if chk_list[i] == "[FPGA-CONFIG " and chk_list[i] in line:
                    get_role_id_1 = line.split("role_id:")[1].split(",")[0]
                    sendlog(f"[FPGA-CONFIG    ] get:{get_role_id_1} exp:{MBSNdict['CP_GOLDEN_IMAGE'].split(',')[1]}", 0 ,log_path)
                    if get_role_id_1 == (MBSNdict["CP_GOLDEN_IMAGE"].split(",")[1]):
                        get_info += 1
                    #get_role_ver_1 = line.split("role_ver:")[1].split(",")[0]
                    #get_fpga_fw = str(hex(int(MBSNdict["CP_FPGA_FW"].split(",")[1], 16)))
                    #if get_role_ver_1 == get_fpga_fw:
                    #    get_info += 1
                    break
                if chk_list[i] == "[FPGA-CONFIG-EX ]" and chk_list[i] in line:
                    get_role_id_2 = line.split("role:") [1].split(",")[0]
                    get_golden_version = line.split("shell:")[1].split(",")[1].split("-")[0]
                    sendlog(f"[FPGA-CONFIG-EX ] get:{get_role_id_2} exp:{MBSNdict['CP_GOLDEN_IMAGE'].split(',')[1]}", 0 ,log_path)
                    if get_role_id_2 == (MBSNdict["CP_GOLDEN_IMAGE"].split(",")[1]):
                        get_info += 1
                    sendlog(f"[FPGA-CONFIG-EX ] get:{get_golden_version} exp:{MBSNdict['CP_GOLDEN_IMAGE'].split(',')[0]}", 0 ,log_path)
                    if get_golden_version == (MBSNdict["CP_GOLDEN_IMAGE"].split(",")[0]):
                        get_info += 1
                    break
                if chk_list[i] == "golen_image_role_id" and chk_list[i] in line and 'mbsn' in line:
                    get_role_id_3 = line.split(" ")[9].strip().strip("(").strip(")")
                    sendlog(f"[golen_image_role_id] get:{get_role_id_3} exp:{MBSNdict['CP_GOLDEN_IMAGE'].split(',')[1]}", 0 ,log_path)
                    if get_role_id_3 == (MBSNdict["CP_GOLDEN_IMAGE"].split(",")[1]):
                        get_info += 1
                    break
                if chk_list[i] == "golden_image_version" and chk_list[i] in line and 'mbsn' in line:
                    get_role_ver_2 = line.split(" ")[9].strip().strip("(").strip(")")
                    sendlog(f"[golden_image_version] get:{get_role_ver_2} exp:{MBSNdict['CP_FPGA_FW'].split(',')[1]}", 0 ,log_path)
                    if get_role_ver_2 == MBSNdict["CP_FPGA_FW"].split(",")[1]:
                        get_info += 1
                    break
                if (chk_list[i] in line) or (chk_list[i] == "Read register 59" and chk_list[i] in line) or (chk_list[i] == "golden_image_build_version" and chk_list[i] in line and 'mbsn' in line):
                    sendlog(f"Get {chk_list[i]}", 0 ,log_path)
                    get_info += 1
                    break
    
    if get_info == exp_info:
        sendlog("{} golden image log file content check PASS!".format(MBSNdict["mbsn"]), 0, log_path)
        return 0
    else:
        sendlog(f"Get:{get_info} EXP:{exp_info}", 0, log_path)
        sendlog("{} golden image log file content check FAIL!".format(MBSNdict["mbsn"]), 0, log_path)
        return 1

#*****************************************************************************
# Function   : write_golden_image_log_file
# Description: Record fpgadiagnostics information in MBSN_do_record_CP_golden_image_version.log.
# Inputs     : MBSNdict: dictionary of SN info
# Outputs    : 0: PASS
#            : 1: FAIL
# Notice     : NA
#*****************************************************************************
def write_golden_image_log_file(MBSNdict):
    sn_log_folder = "{0}/{1}".format(g_log_folder, MBSNdict["mbsn"])
    log_name = "{0}_write_golden_image.log".format(MBSNdict["mbsn"])
    log_path = "{0}/{1}".format(sn_log_folder, log_name)
    record_log_name = "{0}_do_record_CP_golden_image_version.log".format(MBSNdict["mbsn"])
    record_log_path = "{0}/{1}".format(sn_log_folder, record_log_name)
    cmd = "rm -f {0}".format(record_log_path)
    getresult(cmd)


    cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/sbin/modprobe catapult\"".format(MBSNdict["cp_ip"])
    result = getresult(cmd)
    sendlog(result, 0, log_path)
    if "Found no catapult devices" in result:
        sendlog("No catapult devices !!!".format(sn_log_folder), RED, log_path)
        return 2

    cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/fpgadiagnostics -list\"".format(MBSNdict["cp_ip"])
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
        sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}]: fail to get CP chip id".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), RED, log_path)
        print (info)
        return 1
    
    actions=[
        # ["set CP to golden image", "fpgadiagnostics -chip {0} -reconfigToFlashSlot 0".format(CP_chip_id)],
        ["get CP golden image role id", "fpgadiagnostics -chip {0} -mgmt -justreadreg 101".format(CP_chip_id)],
        ["get CP golden image version", "fpgadiagnostics -chip {0} -mgmt -justreadreg 65".format(CP_chip_id)],
        ["get CP golden image build version", "fpgadiagnostics -chip {0} -mgmt -justreadreg 59".format(CP_chip_id)],
        ["get CP golden shell package version", "fpgadiagnostics -chip {0} -dumpHealth".format(CP_chip_id)]
    ]
    
    golen_image_role_id = ""
    golden_image_version = ""
    golden_image_build_version = ""

    for action,cmd in actions:
        ccmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{0} \"echo overlake | sudo -S /usr/bin/{1}\"".format(MBSNdict["cp_ip"], cmd)
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
        sendlog(msg, 0, log_path)
    
    if golen_image_role_id == golden_image_version == golden_image_build_version == "":
        msg = "[mbsn:{0} cp_ip: {1} cp_mac: {2}] record golden image fail".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"])
        sendlog(msg, 0, log_path)
        #s.logout()
        return 1
    msg = "[mbsn:{0} cp_ip: {1} cp_mac: {2}] record golden image finish, full porocess please see {3}".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"], record_log_path)
    sendlog(msg, 0, log_path)
    return 0

#*****************************************************************************
# Function   : chk_soc_fw
# Description: Login CP by RM, and get SoC firmware/Nitro firmware version
#            : and check these version are as expected or not
# Inputs     : sn_info_list: SN list information
# Outputs    : 0: PASS
#            : 1: FAIL
#            : 2: it means it need to update SoC firmware version
# Notice     : NA
#*****************************************************************************
def chk_soc_fw(MBSNdict):
    sn_log_folder = "{0}/{1}".format(g_log_folder, MBSNdict["mbsn"])
    log_name = "{0}_chk_soc_fw.log".format(MBSNdict["mbsn"])
    log_path = "{0}/{1}".format(sn_log_folder, log_name)
    
    try:
        os.makedirs(sn_log_folder)
        sendlog("make log folder ({0}) success".format(sn_log_folder), GREEN, log_path)
    except OSError as e:
        if e.errno == errno.EEXIST:
            sendlog("log folder ({0}) exist".format(sn_log_folder), GREEN, log_path)
        else:
            sendlog("{0}".format(e), 0, log_path)
            return 1

    g_cmd_get_soc_os_ver = "cat /etc/os-release | grep 'VERSION_ID'"
    #Get SoC OS version
    try: #20230902 David add try expect to prevent cannot get fw ver
        sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Get SoC OS version".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
        cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"{}\"".format(MBSNdict["cp_ip"], g_cmd_get_soc_os_ver)
        # Changed ssh to null user
        result = getresult(cmd).split('\x00')[0]
        sendlog(result, 0, log_path)
        if result == "":
            sendlog("Can't get SoC OS version !", 0, log_path)
            return 1
        else:
            get_soc_os_ver = result.split('=')[1].replace('"','').strip()
            sendlog("get_soc_os_ver = {0}".format(get_soc_os_ver), 0, log_path)
    except:
        get_soc_os_ver = ""
    
    #Get SoC firmware version
    try: #20230902 David add try expect to prevent cannot get fw ver
        sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Get SoC firmware version".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
        cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"{}\"".format(MBSNdict["cp_ip"], g_cmd_get_soc_firmware_ver)
        # Changed ssh to null user
        result = getresult(cmd).split('\x00')[0]
        sendlog(result, 0, log_path)
        if result == "":
            sendlog("Can't get SoC firmware version !", 0, log_path)
            return 1
        else:
            get_soc_fw_ver = result
            sendlog("get_soc_fw_ver = {0}".format(get_soc_fw_ver), 0, log_path)
    except:
        get_soc_fw_ver = ""

    #Get SoC cerberus firmware version
    try: #20230902 David add try expect to prevent cannot get fw ver
        sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Get SoC cerberus firmware version".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, )
        cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/{} | grep 'Cerberus Version'\"".format(MBSNdict["cp_ip"], g_cmd_get_soc_cerberus_firmware_ver)
        # Changed ssh to null user
        result = getresult(cmd).split('\x00')[0]
        sendlog(result, 0, log_path)
        if result == "":
            sendlog("Can't get SoC cerberus firmware version !", 0, log_path)
            return 1
        else:
            get_soc_cerberus_fw_ver = result.split(':')[1].strip()
            sendlog("get_soc_cerberus_fw_ver = {0}".format(get_soc_cerberus_fw_ver), 0, log_path)
    except:
        get_soc_cerberus_fw_ver = ""
    
    #Get SoC Nitro firmware version
    try: #20230902 David add try expect to prevent cannot get fw ver
        sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Get SoC Nitro firmware version".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
        cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"{}\"".format(MBSNdict["cp_ip"], g_cmd_get_soc_nitro_firmware_ver)
        # Changed ssh to null user
        result = getresult(cmd).split('\x00')[0]
        sendlog(result, 0, log_path)
        if result == "":
            sendlog("Can't get SoC Nitro firmware version !", 0, log_path)
            return 1
        else:
            get_soc_fw_nitro_ver = result
            sendlog("get_soc_fw_nitro_ver = {0}".format(get_soc_fw_nitro_ver), 0, log_path)
    except:
        get_soc_fw_nitro_ver = ""
    
    #Judge SoC firmware/Nitro firmware version are as expected or not
    if MBSNdict["CP_SOC_FIP_FW"] != get_soc_fw_ver:
        sendlog("SoC firmware version check FAIL ! exp:{0}, get:{1}".format(MBSNdict["CP_SOC_FIP_FW"], get_soc_fw_ver), RED, log_path)
        return 2
    else:
        sendlog("SoC firmware version check PASS ! exp:{0}, get:{1}".format(MBSNdict["CP_SOC_FIP_FW"], get_soc_fw_ver), GREEN, log_path)
        if MBSNdict["CP_SOC_NITRO_FW"] != get_soc_fw_nitro_ver:
            sendlog("SoC firmware Nitro version check FAIL ! exp:{0}, get:{1}".format(MBSNdict["CP_SOC_NITRO_FW"], get_soc_fw_nitro_ver), RED, log_path)
            return 2
        else:
            sendlog("SoC firmware Nitro version check PASS ! exp:{0}, get:{1}".format(MBSNdict["CP_SOC_NITRO_FW"], get_soc_fw_nitro_ver), GREEN, log_path)
        if MBSNdict["CP_CERBERUS_FW"] != get_soc_cerberus_fw_ver:
            sendlog("SoC cerberus firmware version check FAIL ! exp:{0}, get:{1}".format(MBSNdict["CP_CERBERUS_FW"], get_soc_cerberus_fw_ver), RED)
            return 2
        else:
            sendlog("SoC cerberus firmware version check PASS ! exp:{0}, get:{1}".format(MBSNdict["CP_CERBERUS_FW"], get_soc_cerberus_fw_ver), GREEN, log_path)
        
        if MBSNdict["CP_SOC_OS_FW"] != get_soc_os_ver:
            sendlog("SoC OS version check FAIL ! exp:{0}, get:{1}".format(MBSNdict["CP_SOC_OS_FW"], get_soc_os_ver), RED, log_path)
            return 2
        else:
            sendlog("SoC OS version check PASS ! exp:{0}, get:{1}".format(MBSNdict["CP_SOC_OS_FW"], get_soc_os_ver), GREEN, log_path)
    return 0

#*****************************************************************************
# Function   : update_soc_fw
# Description: follow updating SoC firmware version SOP to update
# Inputs     : sn_info_list: SN list information
# Outputs    : 0: PASS
#            : 1: FAIL
# Notice     : NA
#*****************************************************************************
def update_soc_fw(MBSNdict):
    g_os_path = "firmware/{0}/stos/{1}_Image_rsa.img".format(g_project, MBSNdict["CP_GOLDEN_IMAGE"].split(',')[0])
    g_os_local = "/tmp/{0}_Image_rsa.img".format(MBSNdict["CP_GOLDEN_IMAGE"].split(',')[0])
    g_cmd_emmcflash = "emmcflash -a {0} -b {0} -s".format(g_os_local)
    sn_log_folder = "{0}/{1}".format(g_log_folder, MBSNdict["mbsn"])
    log_name = "{0}_update_soc_fw.log".format(MBSNdict["mbsn"])
    log_path = "{0}/{1}".format(sn_log_folder, log_name)
    image_path = "/tftpboot/{}".format(g_os_path)

    try:
        os.makedirs(sn_log_folder)
        sendlog("make log folder ({0}) success".format(sn_log_folder), GREEN, log_path)
    except OSError as e:
        if e.errno == errno.EEXIST:
            sendlog("log folder ({0}) exist".format(sn_log_folder), GREEN, log_path)
        else:
            sendlog("{0}".format(e), 0, log_path)
            return 1
    
    if build_side == 'QCI':
        sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Check CP image on TFTP".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
        cmd = "sshpass -p '{0}' ssh -o 'StrictHostKeyChecking no' {1}@{2} 'ls {3}'".format(g_tftp_passwd, g_tftp_user, g_tftp_ip, image_path)
        result = getresult(cmd).split('\n')
        sendlog(result, 0, log_path)
        if image_path not in result:
            sendlog("MBSN:{0} no overlake image,{1} on PXE server~~~~~~~~~".format(MBSNdict["mbsn"],g_os_path), 0, log_path)
            return 1
    else:
        if not os.path.isfile(image_path):
            sendlog("MBSN:{0} no overlake image,{1} on PXE server~~~~~~~~~".format(MBSNdict["mbsn"],g_os_path), 0, log_path)
            return 1

    # label T6G rsa image
    #   kernel firmware/T6G/stos/Image_rsa.img
    
    cp_mac = MBSNdict["cp_mac_addr"].lower()
    if build_side == 'QCI':
        image_mac_file = "/tmp/01-{0}-{1}-{2}-{3}-{4}-{5}".format(cp_mac[0:2], cp_mac[2:4], cp_mac[4:6], cp_mac[6:8], cp_mac[8:10], cp_mac[10:12])
        os.system("echo 'label T6J rsa image' > {}".format(image_mac_file))
        os.system("echo 'kernel {}' >> {}".format(g_os_path, image_mac_file))

        if not os.path.isfile(image_mac_file):
            sendlog("MBSN:{1} no CP grub on PXE server~~~~~~~~~".format(MBSNdict["mbsn"]), 0, log_path)
            return 1
        sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] copy CP grub to TFTP".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
        cmd = "sshpass -p '{0}' scp -o 'StrictHostKeyChecking no' {1} {2}@{3}:{4}/".format(g_tftp_passwd, image_mac_file, g_tftp_user, g_tftp_ip, g_PXE_grub_folder)        
        result = getresult(cmd).split('\n')
        sendlog(result, 0, log_path)
        
        sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Check CP grub on TFTP".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
        cmd = "sshpass -p '{0}' ssh -o 'StrictHostKeyChecking no' {1}@{2} 'ls {3} | grep {4}'".format(g_tftp_passwd, g_tftp_user, g_tftp_ip, g_PXE_grub_folder, image_mac_file.split('/')[-1].strip())
        print(cmd)
        result = getresult(cmd).split('\n')
        sendlog(result, 0, log_path)
        if result == "":
            sendlog("copy CP grub to TFTP fail !", 0, log_path)
            return 1
    else:
        image_mac_file = "{6}/01-{0}-{1}-{2}-{3}-{4}-{5}".format(cp_mac[0:2], cp_mac[2:4], cp_mac[4:6], cp_mac[6:8], cp_mac[8:10], cp_mac[10:12], g_PXE_grub_folder)
        os.system("echo 'label T6J rsa image' > {}".format(image_mac_file))
        os.system("echo 'kernel {}' >> {}".format(g_os_path, image_mac_file))

        if not os.path.isfile(image_mac_file):
            sendlog("MBSN:{1} no CP grub on PXE server~~~~~~~~~".format(MBSNdict["mbsn"]), 0, log_path)
            return 1

    #Set bootmode to 2 (PXE)
    set_cp_boot_mode(MBSNdict, 2, log_path)
    
    #Reboot the SoC
    sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Reboot CP".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
    cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/sbin/{}\"".format(MBSNdict["cp_ip"], g_cmd_reboot)
    result = getresult(cmd).split('\n')
    sendlog(result, 0, log_path)    
    if result == "":
        sendlog("MBSN:{1} soc reboot fail, change mode to emmc".format(MBSNdict["mbsn"]), 0, log_path)
        #Set bootmode to 0 (EMMC)
        set_cp_boot_mode(MBSNdict, 0, log_path)
        return 1
    
    time.sleep(60)
    # print("rm -rf /root/.ssh/known_hosts...")
    # os.system("rm -rf /root/.ssh/known_hosts")

    sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] CP status check".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
    cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"cat /etc/os-release\"".format(MBSNdict["cp_ip"])
    result = getresult(cmd)
    sendlog(result, 0, log_path)
    
    if result !="":
        #print "DBG:{0}".format(res)
        if "ID=\"msft\"" in result.split("\n"):
            sendlog("Reboot SOC success !", 0, log_path) 
        else:
            time.sleep(10)
            sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] CP status check".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
            cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"cat /etc/os-release\"".format(MBSNdict["cp_ip"])
            result = getresult(cmd).split('\n')
            sendlog(result, 0, log_path)
            
            if result !="":
                if len([word for word in result if 'VERSION=' in word]):
                    sendlog("After Wait 60 second! Reboot SOC Success!", 0, log_path)
                else:
                    sendlog("After Wait 60 second! Reboot SOC fail!", 0, log_path)
                    #Set bootmode to 0 (EMMC)
                    set_cp_boot_mode(MBSNdict, 0, log_path)
                    return 1
            else:
                sendlog("Can't get result - After reboot SOC!!", 0, log_path)
                #Set bootmode to 0 (EMMC)
                set_cp_boot_mode(MBSNdict, 0, log_path)
                return 1
    else:
        sendlog("Can't get result - After reboot SOC!!", 0, log_path)
        #Set bootmode to 0 (EMMC)
        set_cp_boot_mode(MBSNdict, 0, log_path)
        return 1

    #Get soc from tftpboot
    sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] tftp_ip: {3}, soc_path: {4}".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"], g_tftp_ip, g_os_path), 0, log_path)
    cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{0} \"echo overlake | sudo -S tftp -g -r {1} -l {2} {3}\"".format(MBSNdict["cp_ip"], g_os_path, g_os_local, g_tftp_ip)
    result = getresult(cmd).split('\n')
    sendlog(result, 0, log_path)

    #Check md5sum for Image_rsa.img
    if MBSNdict["CP_GOLDEN_IMAGE"].split(',')[0] in g_stos_md5sum:
        stos_md5 = g_stos_md5sum[MBSNdict["CP_GOLDEN_IMAGE"].split(',')[0]]
        sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] stos md5sum expect: {3}".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"], stos_md5), 0, log_path)
        cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{0} \"echo overlake | sudo -S md5sum {1}\"".format(MBSNdict["cp_ip"], g_os_local)
        result = getresult(cmd).split(' ')
        sendlog(result, 0, log_path)
        if result != "":
            get_md5 = result[0]
            if get_md5 != stos_md5:
                sendlog("stos md5sum not equal with database!! get: {0}  expect: {1}".format(get_md5, stos_md5), 0, log_path)
                #Set bootmode to 0 (EMMC)
                set_cp_boot_mode(MBSNdict, 0, log_path)
                return 1
            else:
                sendlog("stos md5sum check successfully!! get: {0}  expect: {1}".format(get_md5, stos_md5), 0, log_path)
        else:
            sendlog("Can't get soc md5sum result!!", 0, log_path)
            #Set bootmode to 0 (EMMC)
            set_cp_boot_mode(MBSNdict, 0, log_path)
            return 1
    else:
        sendlog ("Can't find soc md5sum in database!!", 0, log_path)
        #Set bootmode to 0 (EMMC)
        set_cp_boot_mode(MBSNdict, 0, log_path)
        return 1
    
    #Format mmcblk0 before flash
    #sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] diskprep -s".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
    #cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{0} \"echo overlake | sudo -S diskprep -s\"".format(MBSNdict["cp_ip"])
    #result = getresult(cmd).split('\n')
    #sendlog(result, 0, log_path)

    #Execute "emmcflash" command
    sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] emmcflash".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
    cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/sbin/{}\"".format(MBSNdict["cp_ip"], g_cmd_emmcflash)
    result = getresult(cmd).split('\n')
    sendlog(result, 0, log_path)    
    if result == "":
        sendlog("Can't get result - emmcflash", 0, log_path)
        #Set bootmode to 0 (EMMC)
        set_cp_boot_mode(MBSNdict, 0, log_path)
        return 1
    sendlog("Execute emmcflash command success!!!", 0, log_path)
    
    #Create /tmp/usb folder
    sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Create /tmp/usb folder".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
    cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/{}\"".format(MBSNdict["cp_ip"], g_cmd_mkdir_usb_folder)
    # Changed ssh to null user
    result = getresult(cmd).split('\n')
    sendlog(result, 0, log_path)    
    if result == "":
        sendlog("Can't get result - create /tmp/usb folder", 0, log_path)
        #Set bootmode to 0 (EMMC)
        set_cp_boot_mode(MBSNdict, 0, log_path)        
        return 1
    sendlog("Create /tmp/usb folder success!!", 0, log_path)
    if "0002.17.240911-prd" in MBSNdict["CP_SOC_FIP_FW"]:
        upgrade_image = "overlake-{}-prod-stos.img"	
    g_overlake_image_path = ""
    cmd = "find /tftpboot/firmware/Celestial_Peak/ -name {}".format(upgrade_image.format(MBSNdict["CP_SOC_OS_FW"]))
    print("[debug]cmd:{}".format(cmd))
    res = getresult(cmd)
    if res != "":
        g_overlake_image_path = res.split(upgrade_image.format(MBSNdict["CP_SOC_OS_FW"]))[0]
    else:
        sendlog("[SN:{0}] Cannot find CP SOC image path".format(MBSNdict["mbsn"]), 0, log_path)
        return 1

    if build_side == 'QCI':
        sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Get CP overlake image on TFTP".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
        cmd = "sshpass -p '{0}' scp -o 'StrictHostKeyChecking no' {1}@{2}:{3}/{4} /tmp/".format(g_tftp_passwd, g_tftp_user, g_tftp_ip, g_overlake_image_path.format(MBSNdict["CP_SOC_FIP_FW"][3:7],MBSNdict["CP_SOC_OS_FW"]),upgrade_image.format(MBSNdict["CP_SOC_OS_FW"]))        
        result = getresult(cmd).split('\n')
        sendlog(result, 0, log_path)

        cmd = "ls /tmp/"
        result = getresult(cmd)
        sendlog(result, 0, log_path)
        if upgrade_image.format(MBSNdict["CP_SOC_OS_FW"]) not in result:
            sendlog("Can't get overlake_image!!", 0, log_path)
            #Set bootmode to 0 (EMMC)
            set_cp_boot_mode(MBSNdict, 0, log_path)
            return 1
                
        #Copy image from TFTP to CP SoC
        sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Copy image from TFTP to CP SoC".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
        cmd = "sshpass -p overlake scp -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null /tmp/{0} stuser@{1}:/tmp/".format(upgrade_image.format(MBSNdict["CP_SOC_OS_FW"]), MBSNdict["cp_ip"])   
        result = getresult(cmd).split('\n')
        sendlog(result, 0, log_path)
    else:
        #Copy image from TFTP to CP SoC
        sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Copy image from TFTP to CP SoC".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
        cmd = "sshpass -p overlake scp -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null {0}/{1} stuser@{2}:/tmp/".format(g_overlake_image_path.format(MBSNdict["CP_SOC_FIP_FW"][3:7],MBSNdict["CP_SOC_OS_FW"]),upgrade_image.format(MBSNdict["CP_SOC_OS_FW"]), MBSNdict["cp_ip"])
        sendlog(cmd, 0, log_path)
        result = getresult(cmd).split('\n')
        sendlog(result, 0, log_path)


    #Check md5sum for overlake.img
    if upgrade_image.format(MBSNdict["CP_SOC_OS_FW"]) in g_overlake_md5sum:
        overlake_md5 = g_overlake_md5sum[upgrade_image.format(MBSNdict["CP_SOC_OS_FW"])]
        sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] overlake md5sum expect: {3}".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"], overlake_md5), 0, log_path)
        cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{0} \"echo overlake | sudo -S md5sum {1}\"".format(MBSNdict["cp_ip"], "/tmp/{0}".format(upgrade_image.format(MBSNdict["CP_SOC_OS_FW"])))
        result = getresult(cmd).split(' ')
        sendlog(result, 0, log_path)
        if result != "":
            get_md5 = result[0]
            if get_md5 != overlake_md5:
                sendlog("overlake md5sum not equal with database!! get: {0}  expect: {1}".format(get_md5, overlake_md5), 0, log_path)
                #Set bootmode to 0 (EMMC)
                set_cp_boot_mode(MBSNdict, 0, log_path)
                return 1
            else:
                sendlog("overlake md5sum check successfully!! get: {0}  expect: {1}".format(get_md5, overlake_md5), 0, log_path)
        else:
            sendlog("Can't get overlake md5sum result!!", 0, log_path)
            #Set bootmode to 0 (EMMC)
            set_cp_boot_mode(MBSNdict, 0, log_path)
            return 1
    else:
        sendlog ("Can't find overlake md5sum in database!!", 0, log_path)
        #Set bootmode to 0 (EMMC)
        set_cp_boot_mode(MBSNdict, 0, log_path)
        return 1
    
    g_cmd_losetup_image = "losetup -f -P /tmp/{}".format(upgrade_image.format(MBSNdict["CP_SOC_OS_FW"]))
    #Execute "losetup_image" command
    sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] losetup_image".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
    cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/sbin/{}\"".format(MBSNdict["cp_ip"], g_cmd_losetup_image)
    # Changed ssh to null user
    result = getresult(cmd).split('\n')
    sendlog(result, 0, log_path)
    if result == "":
        sendlog("Can't get result - losetup_image", 0, log_path)
        #Set bootmode to 0 (EMMC)
        set_cp_boot_mode(MBSNdict, 0, log_path)
        return 1
    sendlog("Execute losetup command success!!!", 0, log_path)

    g_cmd_check_loop2_exist = "lsblk"
    #Check "loop2" drive losetup
    sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Check loop2 drive losetup".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
    cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/{}\"".format(MBSNdict["cp_ip"], g_cmd_check_loop2_exist)
    # Changed ssh to null user
    result = getresult(cmd)
    sendlog(result, 0, log_path)
    if result != "":
        if "loop2p1" in result:
            sendlog("Check 'loop2p1' drive losetup success !", 0, log_path)
        else:
            sendlog("Check 'loop2p1' drive losetup fail !", 0, log_path)
            #Set bootmode to 0 (EMMC)
            set_cp_boot_mode(MBSNdict, 0, log_path)
            return 1
    else:
        sendlog("Can't get result - check 'loop2' drive losetup", 0, log_path)
        #Set bootmode to 0 (EMMC)
        set_cp_boot_mode(MBSNdict, 0, log_path)
        return 1

    g_cmd_mount_usb_loop2p1_folder = "mount /dev/loop2p1 /tmp/usb/"
    #Mount /tmp/usb to /dev/loop2p1
    sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Mount /tmp/usb to /dev/loop2p1".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
    cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/{}\"".format(MBSNdict["cp_ip"], g_cmd_mount_usb_loop2p1_folder)
    # Changed ssh to null user
    result = getresult(cmd).split('\n')
    sendlog(result, 0, log_path)
    if result == "":
        sendlog("Can't get result - mount /tmp/usb to /dev/loop2p1", 0, log_path)
        #Set bootmode to 0 (EMMC)
        set_cp_boot_mode(MBSNdict, 0, log_path)
        return 1
    sendlog("Mount /tmp/usb to /dev/loop2p1 success!!", 0, log_path)

    #Check bin files exist or not
    sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Check bin files exist or not".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
    cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/{}\"".format(MBSNdict["cp_ip"], g_cmd_check_bin_file_exist)
    # Changed ssh to null user
    result = getresult(cmd)
    sendlog(result, 0, log_path)
    if result != "":
        try:
            fip_fw_file = re.search("fip.*?bin", result).group()
            nitro_fw_file = re.search("nitro.*?img", result).group()
            fip_pfm_file = re.search(r".*FIP\.PFM.*\.bin", result).group().split()[-1]
            nitro_pfm_file = re.search(r".*NITRO\.PFM.*\.bin", result).group().split()[-1]
        except:
            pass
        if fip_fw_file in result and nitro_fw_file in result and fip_pfm_file in result and nitro_pfm_file in result:
            sendlog("Check bin files success !", 0, log_path)
        else:
            sendlog("Check bin files fail !", 0, log_path)
            #Set bootmode to 0 (EMMC)
            set_cp_boot_mode(MBSNdict, 0, log_path)
            return 1
    else:
        sendlog("Can't get result - check bin files", 0, log_path)
        #Set bootmode to 0 (EMMC)
        set_cp_boot_mode(MBSNdict, 0, log_path)
        return 1
    
    g_cmd_update_sop = ["cerberus_utility pfmupdate 0 /tmp/usb/{} 0".format(fip_pfm_file), #T6G not PFM activate
                    "cerberus_utility socfwupdate 0 /tmp/usb/{} 1".format(fip_fw_file),
                    "cerberus_utility pfmupdate 1 /tmp/usb/{} 0".format(nitro_pfm_file), #T6G not PFM activate
                    "cerberus_utility socfwupdate 1 /tmp/usb/{}".format(nitro_fw_file)]
    #Phuc adding check pfm id before updating pfm
    for id in range(2):
        cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/{}\"".format(MBSNdict["cp_ip"],g_cmd_cerberus_pfm_chk.format(id))
        # Changed ssh to null user
        result = getresult(cmd)
        sendlog(result, 0, log_path)
        if result == "":
            sendlog("Can't get cmd result: {0}".format(cmd), 0, log_path)
        else:
            match = re.search(r'Cerberus PFM ID:\s*(0x[0-9a-fA-F]+)', result)
            if match:
                info = match.group(1).strip()  # Extract the PFM ID
                if id == 0:
                    fip_pfm_id = info  # Store the FIP PFM ID
                    sendlog(f"FIP ID is {fip_pfm_id}", 0, log_path)
                    if fip_pfm_id >= MBSNdict["CP_SOC_FIP_PFMID"]:
                        g_cmd_update_sop.remove("cerberus_utility pfmupdate 0 /tmp/usb/{} 0".format(fip_pfm_file))
                else:
                    nitro_pfm_id = info  # Store the Nitro PFM ID
                    sendlog(f"NITRO ID is {nitro_pfm_id}", 0, log_path)
                    if nitro_pfm_id >= MBSNdict["CP_SOC_NITRO_PFMID"]:
                        g_cmd_update_sop.remove("cerberus_utility pfmupdate 1 /tmp/usb/{} 0".format(nitro_pfm_file))                        
            else:
                sendlog("PFM ID not found in the command output.")
    print(g_cmd_update_sop)
    #do update FW
    for cmd in g_cmd_update_sop:
        sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] CP SoC FW update: {3}".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"], cmd), 0, log_path)
        cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/{}\"".format(MBSNdict["cp_ip"], cmd)
        # Changed ssh to null user
        success = False
        for attempt in range(1,3 + 1):
            result = getresult(cmd)
            sendlog(result, 0, log_path)
            if result == "":
                sendlog("Can't get cmd result: {0}".format(cmd), 0, log_path)
            elif "Cerberus command completed successfully" in result:
                sendlog("Use update command success.", 0, log_path)
                success = True
                break
            else:
                sendlog("Use update command fail: {0}".format(cmd), 0, log_path)
            sendlog(f"Attempt {attempt} of 3 failed. Retrying", 0 , log_path)
            time.sleep(10)
        if not success:
            try:
                os.system(f"python3 /usr/local/bin/L10_Status_Update.py send2sf {MBSNdict['mbsn']} 'Cerberus Update Command Error' '' '{MBSNdict['STATION']}'")
            except:
                sendlog(f"Send log to SF failed", 0 , log_path)
            #Set bootmode to 0 (EMMC)
            set_cp_boot_mode(MBSNdict, 0, log_path)
            return 1
    
    # 20240328 David modify use SF info
    g_cp_Cerberus_fw="cerberus_v{}.bin".format(MBSNdict["CP_CERBERUS_FW"])
    g_cp_Cerberus_fw_loc="/project/firmware/{}/cp/{}".format(g_project,g_cp_Cerberus_fw)
    if build_side == "QCI":
        os.system("mkdir -p /project/firmware/{}/cp/".format(g_project))
        sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Copy cp Cerberus FW file to server".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
        cmd = "cp -rf /mnt/smbfs/firmware/{}/cp/{} {}".format(g_project, g_cp_Cerberus_fw, g_cp_Cerberus_fw_loc)
        result = getresult(cmd)
        sendlog(result, 0, log_path)
        info = result.split('\n')
    #Copy Cerberus FW from TFTP to CP SoC
    sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Copy Cerberus FW from TFTP to CP SoC".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
    cmd = "sshpass -p overlake scp -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null {0} stuser@{1}:/tmp/".format(g_cp_Cerberus_fw_loc, MBSNdict["cp_ip"])  
    result = getresult(cmd).split('\n')
    sendlog(result, 0, log_path)
    
    #do Cerberus FW update
    sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Update CP Cerberus FW".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
    cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/cerberus_utility fwupdate /tmp/{}\"".format(MBSNdict["cp_ip"], g_cp_Cerberus_fw)
    # Changed ssh to null user
    result = getresult(cmd)
    sendlog(result.split('\n'), 0, log_path)
    if result == "":
        sendlog("Can't get cmd result: {0}".format(cmd), 0, log_path)
        #Set bootmode to 0 (EMMC)
        set_cp_boot_mode(MBSNdict, 0, log_path)
        return 1
    elif "Cerberus command completed successfully" in result:
        sendlog("Use update command success.", 0, log_path)
    else:
        sendlog("Use update command fail: {0}".format(cmd), 0, log_path)
        #Set bootmode to 0 (EMMC)
        set_cp_boot_mode(MBSNdict, 0, log_path)
        return 1

    #Set bootmode to 0 (EMMC)
    set_cp_boot_mode(MBSNdict, 0, log_path)

    global g_reboot_flag
    g_reboot_flag = True
        
    #Reset SoC
    sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Reset SoC".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
    cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/{}\" &".format(MBSNdict["cp_ip"], g_cmd_reset_soc)
    # Changed ssh to null user
    # result = getresult(cmd).split('\n')
    # sendlog(result, 0, log_path)
    os.system(cmd)

    time.sleep(10)  
    sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Kill socreset process".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
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
# Function   : chk_fpga_fw
# Description: Login CP by RM, and get CP FPGA firmware version
#            : and check these version are as expected or not
# Inputs     : sn_info_list: SN list information
# Outputs    : 0: PASS
#            : 1: FAIL
#            : 2: it means it need to update SoC firmware version
# Notice     : NA
#*****************************************************************************
def chk_fpga_fw(MBSNdict):
    factory_image = True
    golden_image = True
    sn_log_folder = "{0}/{1}".format(g_log_folder, MBSNdict["mbsn"])
    log_name = "{0}_chk_fpga_fw.log".format(MBSNdict["mbsn"])
    log_path = "{0}/{1}".format(sn_log_folder, log_name)
    ver = ""
    role = ""
    
    try:
        os.makedirs(sn_log_folder)
        sendlog("make log folder ({0}) success".format(sn_log_folder), GREEN, log_path)
    except OSError as e:
        if e.errno == errno.EEXIST:
            sendlog("log folder ({0}) exist".format(sn_log_folder), GREEN, log_path)
        else:
            sendlog("{0}".format(e), 0, log_path)
            return 1
    
    sendlog("[mbsn:{0} cp_ip: {1} cp_mac: {2}] load CP driver".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
    cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/sbin/modprobe catapult\"".format(MBSNdict["cp_ip"])
    # Changed ssh to null user
    result = getresult(cmd)
    sendlog(result, 0, log_path)
    if "Found no catapult devices" in result:
        sendlog("No catapult devices !!! ".format(sn_log_folder), RED, log_path)
        return 3

    # print ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Change FPGA slot to Golden".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]))
    # cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/fpgadiagnostics -reconfiggolden\"".format(MBSNdict["cp_ip"])
    #   # Changed ssh to null user
    # result = getresult(cmd)
    # sendlog(result, 0, log_path)
    # info = result.split('\n')
        
    time.sleep(30)

    sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Change FPGA slot to Golden".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
    cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/fpgadiagnostics -reconfiggolden\"".format(MBSNdict["cp_ip"])
    result = getresult(cmd)

    sendlog(result, 0, log_path)

    sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] dumpHealth".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
    cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/fpgadiagnostics -dumphealth\"".format(MBSNdict["cp_ip"])
    # Changed ssh to null user
    result = getresult(cmd)
    sendlog(result, 0, log_path)
    info = result.split('\n')

    for line in info:
        if "[FPGA-CONFIG-EX ] OK" in line:
            ver = line.split()[6].split(',')[1].split('-')[0].strip()
            role = line.split()[7].split(',')[0].split('role:')[1]

    global g_reboot_flag
    g_reboot_flag = True

    #Check FPGA version
    if ver == "" or role == "":
        sendlog("Can't get FPGA firmware version !", 0, log_path)
        return 1
    else:
        get_fpga_fw_ver = ver+','+role
        sendlog("get_fpga_fw_ver = {0} CP_GOLDEN_IMAGE = {1}".format(get_fpga_fw_ver, MBSNdict["CP_GOLDEN_IMAGE"]), 0, log_path)
        if MBSNdict["CP_GOLDEN_IMAGE"] != get_fpga_fw_ver:
            golden_image = False

    sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] ".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
    cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/fpgadiagnostics -reconfigApp\"".format(MBSNdict["cp_ip"])
    result = getresult(cmd)
    sendlog(result, 0, log_path)
    sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] dumpHealth".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
    cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/fpgadiagnostics -dumphealth\"".format(MBSNdict["cp_ip"])
    # Changed ssh to null user
    result = getresult(cmd)
    sendlog(result, 0, log_path)
    info = result.split('\n')

    for line in info:
        if "[FPGA-CONFIG-EX ] OK" in line:
            ver = line.split()[6].split(',')[1].split('-')[0].strip()
            role = line.split()[7].split(',')[0].split('role:')[1]
            
    # switch back to golden image
    sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Change FPGA slot to Golden".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
    cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/fpgadiagnostics -reconfiggolden\"".format(MBSNdict["cp_ip"])
    result = getresult(cmd)
    sendlog(result, 0, log_path)


    #Check FPGA version
    if ver == "" or role == "":
        sendlog("Can't get FPGA firmware version !", 0, log_path)
        return 1
    else:
        get_fpga_fw_ver = ver+','+role
        sendlog("cp_factory_image = {0}, get_fpga_fw_ver = {1}".format(MBSNdict["CP_FACTORY_IMAGE"], get_fpga_fw_ver), 0, log_path)
        if MBSNdict["CP_FACTORY_IMAGE"] != get_fpga_fw_ver:
            factory_image = False
    if factory_image == False or golden_image == False:
        return 2
    
    return 0

#*****************************************************************************
# Function   : update_fpga_fw
# Description: follow updating FPGA firmware version SOP to update
# Inputs     : sn_info_list: SN list information
# Outputs    : 0: PASS
#            : 1: FAIL
# Notice     : NA
#*****************************************************************************
def update_fpga_fw(MBSNdict):     
    sn_log_folder = "{0}/{1}".format(g_log_folder, MBSNdict["mbsn"])
    log_name = "{0}_update_fpga_fw.log".format(MBSNdict["mbsn"])
    log_path = "{0}/{1}".format(sn_log_folder, log_name)
    CP_IP=""
    
    try:
        os.makedirs(sn_log_folder)
        sendlog("make log folder ({0}) success".format(sn_log_folder), GREEN, log_path)
    except OSError as e:
        if e.errno == errno.EEXIST:
            sendlog("log folder ({0}) exist".format(sn_log_folder), GREEN, log_path)
        else:
            sendlog("{0}".format(e), 0, log_path)
            return 1
    
    g_cp_FPGA_firmware=""
    g_cp_FPGA_firmware_loc=""
    cmd = "find /project/firmware/{0}/ -name *{1}*.rpd".format(g_project.lower(),MBSNdict["CP_GOLDEN_IMAGE"].split(',')[0])
    res = getresult(cmd)
    if res != "":
        g_cp_FPGA_firmware = res.split('/')[-1].strip()
        g_cp_FPGA_firmware_loc=res.strip()
    else:
        sendlog("[SN:{}] Cannot find cp FPGA firmware file name".format(MBSNdict["mbsn"]), 0, log_path)
        return 1
        
    #Find CP SOC IP
    sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] dumpHealth".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0 ,log_path)
    cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/fpgadiagnostics -dumphealth\"".format(MBSNdict["cp_ip"])
    # Changed ssh to null user
    result = getresult(cmd)
    sendlog(result, 0, log_path)
    info = result.split('\n')
    
    g_cp_FPGA_firmware=""
    g_cp_FPGA_firmware_loc=""
    cmd = "find /project/firmware/{0}/ -name *{1}*.rpd".format(g_project.lower(),MBSNdict["CP_GOLDEN_IMAGE"].split(',')[0])
    res = getresult(cmd)
    if res != "":
        g_cp_FPGA_firmware = res.split('/')[-1]
        g_cp_FPGA_firmware_loc= res.strip()
        sendlog("g_cp_FPGA_firmware_loc = {0}".format(g_cp_FPGA_firmware_loc), 0, log_path)
        sendlog("g_cp_FPGA_firmware = {0}".format(g_cp_FPGA_firmware), 0, log_path)
    else:
        sendlog("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Cannot find cp FPGA firmware file name".format(format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 2), 0, log_path)
        return 1
    
    #Copy image to CP SOC
    if build_side == "QCI":
        os.system("mkdir -p /project/firmware/{}/cp/".format(g_project))
        sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Copy cp image file to server".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
        cmd = "cp -rf /mnt/smbfs/firmware/{}/cp/{} {}".format(g_project, g_cp_FPGA_firmware, g_cp_FPGA_firmware_loc)
        result = getresult(cmd)
        sendlog(result, 0, log_path)
        info = result.split('\n')
    
    for i in range(1, 3 + 1):
        ret = update_cp_fpga_fw(MBSNdict,log_path)
        if ret == 0:
            if check_cp_fpga_fw(MBSNdict,"app",log_path) or check_cp_fpga_fw(MBSNdict,"golden",log_path):
                pass #do update_cp_fpga_fw() again
            else:
                break
        if i == 3:
            try:
                os.system(f"python3 /usr/local/bin/L10_Status_Update.py send2sf {MBSNdict['mbsn']} 'Update fpga fw fail. Retry: {i} times.' '' '{MBSNdict['STATION']}'")
            except:
                sendlog(f"Send log to SF failed", 0 , log_path)
            return 1
    
    global g_reboot_flag
    g_reboot_flag = True

    return 0

def power_cycle_uut(MBSNdict):
    failure_code = {1:"Command was not sent successfully", 2: "Rm Ip Is Failed", 3: "Rm Port Failure"}
    log_header = f"[mbsn: {MBSNdict['mbsn']} bmc_ip: {MBSNdict['bmc_ip']} bmc_mac: {MBSNdict['bmc_mac_addr']}]"
    sn_log_folder = "{0}/{1}".format(g_log_folder, MBSNdict["mbsn"])
    log_name = "{0}_reboot.log".format(MBSNdict["mbsn"])
    log_path = "{0}/{1}".format(sn_log_folder, log_name)

    isFailure = False
    sendlog(f"{log_header} Starting A/C cycle UUT", 0, log_path)
    ret = send_cmd_to_rm(MBSNdict, "A/C", log_path)

    if ret != 0:
        sendlog(f"{log_header} A/C is not success due to {failure_code[ret]}, try to do D/C cycle", 0, log_path)
        count = 3
        while count > 0:
            sendlog(f"{log_header} Starting power cycle UUT", 0, log_path)
            # KH add power cycle
            ret_dc = send_cmd_to_rm(MBSNdict, "power cycle", log_path)
            # Add ipmitool power cycle for unit not on RM
            if ret_dc != 0:
                sendlog(f"{log_header} D/C is failed due to {failure_code[ret]}, try power cycle thourgh BMC IP", 0, log_path)
                ret = getresult(f"ipmitool -H {MBSNdict['bmc_ip']} -U {g_bmc_username} -P {g_bmc_password} -I lanplus power cycle", log_path)
                sendlog(f"{log_header} {ret_dc}", 0, log_path)
                if "Chassis Power Control: Cycle" in ret:
                    sendlog(f"{log_header} Power cycle via BMC success", 0, log_path)
                    break
                else:
                    isFailure = True
            else:
                sendlog(f"{log_header} Power cycle via RM success", 0, log_path)
                break
            time.sleep(10)
            count = count - 1
    else:
        sendlog(f"{log_header} A/C cycle via RM success", 0, log_path)
        time.sleep(10)

    if isFailure:
        return 1
    else:
        time.sleep(130) #wait 130 secs for system reboot
        return 0

def is_CP_update(MBSNdict):
    sn_log_folder = "{0}/{1}".format(g_log_folder, MBSNdict["mbsn"])
    update_flag = "{0}_already_update.log".format(MBSNdict["CP_SN"]) # 20240328 David modify to CP SN to avoid change CP card no update
    update_flag_path = "{0}/{1}".format(sn_log_folder, update_flag)
    log_name = "{0}_check_cp_update.log".format(MBSNdict["mbsn"])
    log_path = "{0}/{1}".format(sn_log_folder, log_name)
    record_log_name = "{0}_do_record_CP_golden_image_version.log".format(MBSNdict["mbsn"])
    record_log_path = "{0}/{1}".format(sn_log_folder, record_log_name)
    if not os.path.isfile(update_flag_path):
        sendlog ("{0}_do_CP_FW_version check".format(MBSNdict["mbsn"]), 0, log_path)

        sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] remove auto-reconfig".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
        cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S rm -rf {}\"".format(MBSNdict["cp_ip"],auto_reconfig_soc_loc)
        getresult(cmd)

        # 20240328 David modify to remove record to avoid change CP card no update record
        sendlog("[MBSN:{0}]Remove CP record file".format(MBSNdict["mbsn"]), 0, log_path)
        if os.path.isfile(record_log_path):
            os.system("rm -rf {0}".format(record_log_path))
        
        sendlog ("start to do_cp_soc_fw_check~~", 0, log_path)
        ret = chk_soc_fw(MBSNdict)
        if ret != 0:
            if ret == 2:
                sendlog("SoC firmware is error and need to update", 0, log_path)
                ret = update_soc_fw(MBSNdict)
                if ret != 0:
                    sendlog("[MBSN:{0}] update SoC firmware FAIL".format(MBSNdict["mbsn"]), RED, log_path)
                    return 1
                else:
                    sendlog("[MBSN:{0}] update SoC firmware PASS".format(MBSNdict["mbsn"]), GREEN, log_path)
            else:
                sendlog("[MBSN:{0}] check SoC firmware FAIL. it can not update".format(MBSNdict["mbsn"]), RED, log_path)
                return 1

        sendlog ("start to do_cp_fpga_fw_check~~", 0, log_path)
        ret=chk_fpga_fw(MBSNdict)
        if ret != 0:
            if ret == 2:
                sendlog("FPGA firmware is error and need to update", 0, log_path)
                ret = update_fpga_fw(MBSNdict)
                if ret != 0:
                    sendlog("[MBSN:{0}] update FPGA firmware FAIL".format(MBSNdict["mbsn"]), RED, log_path)
                    return 1
                else:
                    sendlog("[MBSN:{0}] update FPGA firmware PASS".format(MBSNdict["mbsn"]), GREEN, log_path)
            elif ret == 3:
                sendlog("SoC firmware is error and need to update", 0, log_path)
                ret = update_soc_fw(MBSNdict)
                if ret != 0:
                    sendlog("[MBSN:{0}] update SoC firmware FAIL".format(MBSNdict["mbsn"]), RED, log_path)
                else:
                    sendlog("[MBSN:{0}] update SoC firmware PASS".format(MBSNdict["mbsn"]), GREEN, log_path)
                return 1
            else:
                sendlog("[MBSN:{0}] check FPGA firmware FAIL. it can not update".format(MBSNdict["mbsn"]), RED, log_path)
                return 1
        else:
            sendlog("[MBSN:{0}] check FPGA firmware PASS. no need to update".format(MBSNdict["mbsn"]), GREEN, log_path)
            
        os.system("touch {0}".format(update_flag_path))
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
    sn_log_folder = "{0}/{1}".format(g_log_folder, MBSNdict["mbsn"])
    log_name = "{0}_record_cp_and_reconfig.log".format(MBSNdict["mbsn"])
    log_path = "{0}/{1}".format(sn_log_folder, log_name)
    updating_log_name = "{0}_updating.log".format(MBSNdict["mbsn"])
    updating_flag = "{0}/{1}".format(sn_log_folder, updating_log_name)
    is_False = False
    try:
        os.makedirs(sn_log_folder)
        sendlog("make log folder ({0}) success".format(sn_log_folder), GREEN, log_path)
    except OSError as e:
        if e.errno == errno.EEXIST:
            sendlog("log folder ({0}) exist".format(sn_log_folder), GREEN, log_path)
        else:
            sendlog("{0}".format(e), 0, log_path)
            return 1

    #step 1 : check uut power status
    # ret = chk_uut_power_state(MBSNdict)
    # if ret != 0:
    #   msg = "[mbsn: {0}, bmc_ip: {1}] chk_uut_power_state FAIL".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"])
    #   sendlog(msg, RED)
    #   return 1
    if not os.path.isfile(updating_flag):
        os.system("touch {0}".format(updating_flag))
        try:
            ret = is_CP_update(MBSNdict)
            if ret == 0:
                sendlog ("[mbsn: {0}, cp_ip: {1}] CP FW check/update Success".format(MBSNdict["mbsn"], MBSNdict["cp_ip"]), GREEN, log_path)
            else:
                sendlog ("[mbsn: {0}, cp_ip: {1}] CP FW check/update Fail".format(MBSNdict["mbsn"], MBSNdict["cp_ip"]), RED, log_path)
                is_False = True
        except:
            sendlog ("[mbsn: {0}, cp_ip: {1}] CP FW check/update Fail".format(MBSNdict["mbsn"], MBSNdict["cp_ip"]), RED, log_path)
            sendlog (sys.exc_info(), 0, log_path)
            is_False = True

        if g_reboot_flag == True:
            power_res = power_cycle_uut(MBSNdict)
            if power_res != 0:
                sendlog("Power cycle UUT FAIL", RED, log_path)
                clear_flag(MBSNdict)
                return 1
        
        if is_False == True:
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
            sendlog ("[mbsn: {0}, cp_ip: {1}] reconfig CP Success".format(MBSNdict["mbsn"], MBSNdict["cp_ip"]), GREEN, log_path)
        elif ret == 1:
            # print "====== [mbsn: {0}, bmc_ip: {1}] already APP mode".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"])
            # msg = "[mbsn: {0}, bmc_ip: {1}] already APP mode".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"])
            print ("====== [mbsn: {0}, cp_ip: {1}] already APP mode".format(MBSNdict["mbsn"], MBSNdict["cp_ip"]))
            msg = "[mbsn: {0}, cp_ip: {1}] already APP mode".format(MBSNdict["mbsn"], MBSNdict["cp_ip"])
            sendlog(msg, GREEN, log_path)
        elif ret == 2: #golden mode
            # print "====== [mbsn: {0}, bmc_ip: {1}] reconfig CP to APP mode fail".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"])
            # msg = "[mbsn: {0}, bmc_ip: {1}] reconfig CP to APP mode fail".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"])
            print ("====== [mbsn: {0}, cp_ip: {1}] reconfig CP to APP mode fail".format(MBSNdict["mbsn"], MBSNdict["cp_ip"]))
            msg = "[mbsn: {0}, cp_ip: {1}] reconfig CP to APP mode fail".format(MBSNdict["mbsn"], MBSNdict["cp_ip"])
            sendlog(msg, RED, log_path)
            clear_flag(MBSNdict)
            return 1
        elif ret == 3:
            # msg = "[mbsn: {0}, bmc_ip: {1}]reconfig CP FAIL".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"])
            msg = "[mbsn: {0}, cp_ip: {1}]reconfig CP FAIL".format(MBSNdict["mbsn"], MBSNdict["cp_ip"])
            sendlog(msg, RED, log_path)
            clear_flag(MBSNdict)
            return 1
        elif ret == 4:
            # msg = "[mbsn: {0}, bmc_ip: {1}]log file create fail".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"])
            msg = "[mbsn: {0}, cp_ip: {1}]log file create fail".format(MBSNdict["mbsn"], MBSNdict["cp_ip"])
            sendlog(msg, RED, log_path)
            clear_flag(MBSNdict)
            return 1
        elif ret == 5:
            if create_auto_reconfig_file(MBSNdict) != 0: #20231102 David add auto reconfig
                # print "====== [mbsn: {0}, bmc_ip: {1}] reconfig CP to APP mode fail".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"])
                # msg = "[mbsn: {0}, bmc_ip: {1}] reconfig CP to APP mode fail".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"])
                print ("====== [mbsn: {0}, cp_ip: {1}] reconfig CP to APP mode fail".format(MBSNdict["mbsn"], MBSNdict["cp_ip"]))
                msg = "[mbsn: {0}, cp_ip: {1}] reconfig CP to APP mode fail".format(MBSNdict["mbsn"], MBSNdict["cp_ip"])
                sendlog(msg, RED, log_path)
                clear_flag(MBSNdict)
                return 1
            cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' stuser@{0} \"echo overlake | sudo -S {1}\"".format(MBSNdict["cp_ip"], g_cmd_find_auto_python)
            result = getresult(cmd)
            if auto_reconfig_python_soc_loc in result:
                print ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Golden mode and fpga.py exist in cp card, Reboot CP".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), GREEN)
                cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' stuser@{} \"echo overlake | sudo -S /usr/sbin/{}\"".format(MBSNdict["cp_ip"], g_cmd_reboot)
                result = getresult(cmd).split('\n')
                sendlog(result, 0, log_path)
        elif ret == 6: #cannot modprobe catapult
                sendlog("SoC firmware is error and need to update", 0, log_path)
                ret = update_soc_fw(MBSNdict)
                if ret != 0:
                    sendlog("[MBSN:{0}] update SoC firmware FAIL".format(MBSNdict["mbsn"]), RED, log_path)
                else:
                    sendlog("[MBSN:{0}] update SoC firmware PASS".format(MBSNdict["mbsn"]), GREEN, log_path)
                clear_flag(MBSNdict)
                return 1

        else:
            # msg = "[mbsn: {0}, bmc_ip: {1}] Get CP current mode fail".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"])
            msg = "[mbsn: {0}, cp_ip: {1}] Get CP current mode fail".format(MBSNdict["mbsn"], MBSNdict["cp_ip"])
            sendlog(msg, RED, log_path)
            # print "====== [mbsn: {0}, bmc_ip: {1}] Get CP current mode fail".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"])
            print ("====== [mbsn: {0}, cp_ip: {1}] Get CP current mode fail".format(MBSNdict["mbsn"], MBSNdict["cp_ip"]))
            clear_flag(MBSNdict)
            return 1
       
        sendlog("Finish Do_record_cp_and_reconfig~~~~", 0, log_path)
        os.system("rm -rf {0}".format(updating_flag))
    else:
        check_flag(MBSNdict)
        sendlog("[mbsn:{0}, cp_ip: {1}]doing update~~~".format(MBSNdict["mbsn"], MBSNdict["cp_ip"]), GREEN, log_path)

    return 0

#*****************************************************************************
# Function   : create_auto_reconfig_file()
# Description: create auto reconfig file
# Inputs     : 
# Outputs    : 
# Notice     : 20231102 David add
#*****************************************************************************
def create_auto_reconfig_file(MBSNdict):
    sn_log_folder = "{0}/{1}".format(g_log_folder, MBSNdict["mbsn"])
    log_name = "{0}_cp_auto_reconfig.log".format(MBSNdict["mbsn"])
    log_path = "{0}/{1}".format(sn_log_folder, log_name)
    CP_IP=""

    if not os.path.isfile(auto_reconfig_service_server_loc):
        sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] File {3} not exist, please check it!!".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"], auto_reconfig_service_server_loc), 0, log_path)
        return 1
    
    if not os.path.isfile(auto_reconfig_python_server_loc):
        sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] File {3} not exist, please check it!!".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"], auto_reconfig_python_server_loc), 0, log_path)
        return 1
    
    #check auto reconfig exist
    sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] check auto reconfig exist".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
    cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' stuser@{0} \"echo overlake | sudo -S {1}\"".format(MBSNdict["cp_ip"], g_cmd_find_auto_service)
    result = getresult(cmd)
    sendlog(result, 0, log_path)
    
    if auto_reconfig_service_soc_loc in result:
        sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] File {3} exist at soc.".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"], auto_reconfig_service_soc_loc), 0, log_path)
        cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' stuser@{0} \"echo overlake | sudo -S {1}\"".format(MBSNdict["cp_ip"], g_cmd_find_auto_python)
        result = getresult(cmd)
        sendlog(result, 0, log_path)
        if auto_reconfig_python_soc_loc in result:
            sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] File {3} exist at soc.".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"], auto_reconfig_python_soc_loc), 0, log_path)
            if is_CP_Golden_mode(MBSNdict) != 1: #Not APP mode
                try:
                    if not MBSNdict["is_reconfig"]:
                        sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Do reconfig Celestial Peak.".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
                        sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Need reconfig Celestial Peak.".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)

                        sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] load CP driver".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
                        cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' stuser@{} \"echo overlake | sudo -S /usr/sbin/modprobe catapult\"".format(MBSNdict["cp_ip"])
                        result = getresult(cmd)
                        sendlog(result, 0, log_path)

                        if "Found no catapult devices" in result:
                            sendlog("No catapult devices !!! SoC firmware is error and need to update", 0, log_path)
                            ret = update_soc_fw(MBSNdict)
                            if ret != 0:
                                sendlog("[MBSN:{0}] update SoC firmware FAIL".format(MBSNdict["mbsn"]), RED, log_path)
                            else:
                                sendlog("[MBSN:{0}] update SoC firmware PASS".format(MBSNdict["mbsn"]), GREEN, log_path)
                            return 1

                        sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] do CP reconfig".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
                        cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' stuser@{} \"echo overlake | sudo -S /usr/bin/fpgadiagnostics -reconfigApp\"".format(MBSNdict["cp_ip"])
                        result = getresult(cmd)
                        sendlog(result, 0, log_path)
                        return 0

                    else:
                        return 0
                except pxssh.ExceptionPxssh as e:
                    sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Pxssh failed: reconfig Celestial Peak.".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
                    sendlog(e, RED, log_path)
                    return 1
            else:
                sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Auto reconfig PASS!!".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
                return 0
            
    sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Create auto reconfig Celestial Peak.".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
    
    #Find CP SOC IP
    sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Find CP SOC IP".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
    cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' stuser@{} \"echo overlake | sudo -S /sbin/ifconfig\"".format(MBSNdict["cp_ip"])
    result = getresult(cmd)
    sendlog(result, 0, log_path)

    info = result.split("\n")
    retry = 0
    if info != "":
        while CP_IP == "" and retry < 3:
            for line in info:
                # if "inet addr:" in line and "127.0.0.1" not in line:
                if "inet" in line and "inet6" not in line: #20230927 david change query message, os change
                    if "127.0.0.1" in line:
                        continue
                    if "addr:" in line:
                        CP_IP = line.split()[1].split(":")[1]
                    else:
                        CP_IP = line.split()[1]
                    
                    ret = os.system("ping -c 3 {0}".format(CP_IP))
                    if ret == 0:
                        sendlog("Get_CP_IP IP = {0}".format(CP_IP), PASS, log_path)
                        break

            retry += 1
    ###send auto_reconfig_service to console
    send_file_to_console(CP_IP,auto_reconfig_service_server_loc,"/tmp/",MBSNdict)
    ###send auto_reconfig_python to console
    send_file_to_console(CP_IP,auto_reconfig_python_server_loc,"/tmp/",MBSNdict)

    sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Create {3} folder".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"], g_cmd_mkdir_service_loc_path), 0, log_path)
    cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' stuser@{} \"echo overlake | sudo -S /usr/bin/{}\"".format(MBSNdict["cp_ip"], g_cmd_mkdir_service_loc_path)
    result = getresult(cmd).split('\n')
    sendlog(result, 0, log_path)
    if result == "":
        sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Create service path fail!DBG:{3}".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"], result), 0, log_path)
        return 1
    else:
        sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Create service path PASS!DBG:{3}".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"], result), 0, log_path)

    sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Create {3} folder".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"], g_cmd_mkdir_service_loc_path), 0, log_path)
    cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' stuser@{} \"echo overlake | sudo -S /usr/bin/{}\"".format(MBSNdict["cp_ip"], g_cmd_mkdir_service_loc_path)
    result = getresult(cmd).split('\n')
    sendlog(result, 0, log_path)
    if result == "":
        sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Create service path fail!DBG:{3}".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"], result), 0, log_path)
        return 1
    else:
        sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Create service path PASS!DBG:{3}".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"], result), 0, log_path)


    sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] copy  SoCFPGATestSvc.service file to CP console".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
    cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' stuser@{0} \"echo overlake | sudo -S {1}\"".format(MBSNdict["cp_ip"], g_cmd_copy_auto_service_to_loc_path)
    result = getresult(cmd).split('\n')
    sendlog(result, 0, log_path)

    sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] copy  SoCFPGATestSvc.service file to CP console".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
    cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' stuser@{0} \"echo overlake | sudo -S {1}\"".format(MBSNdict["cp_ip"], g_cmd_copy_auto_python_to_loc_path)
    result = getresult(cmd).split('\n')
    sendlog(result, 0, log_path)

    #Reboot the SoC
    sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Reboot CP".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
    cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' stuser@{} \"echo overlake | sudo -S /usr/sbin/{}\"".format(MBSNdict["cp_ip"], g_cmd_reboot)
    result = getresult(cmd).split('\n')
    sendlog(result, 0, log_path)
    if result == "":
        return 1
    
    time.sleep(60)
    print("rm -rf /root/.ssh/known_hosts...")
    os.system("rm -rf /root/.ssh/known_hosts")

    sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] CP status check".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
    cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' stuser@{} \"cat /etc/os-release\"".format(MBSNdict["cp_ip"])
    result = getresult(cmd)
    sendlog(result, 0, log_path)
    
    if result !="":
        #print "DBG:{0}".format(res)j
        if "msft" in result:
            sendlog("Reboot SOC success !", 0, log_path) 
        else:
            time.sleep(10)
            sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] CP status check".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
            cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' stuser@{} \"cat /etc/os-release\"".format(MBSNdict["cp_ip"])
            result = getresult(cmd)
            sendlog(result, 0, log_path)
            
            if result !="":
                if "VERSION=" in result:
                    sendlog("After Wait 10 second! Reboot SOC success !", 0 ,log_path)
                else:
                    sendlog("After Wait 10 second! Reboot SOC fail!", 0, log_path)
                    return 1
            else:
                sendlog("Can't get result - After reboot SOC!!", 0, log_path)
                return 1
    else:
        sendlog("Can't get result - After reboot SOC!!", 0, log_path)
        return 1

    time.sleep(15)
    if is_CP_Golden_mode(MBSNdict) != 1:
        sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Auto reconfig FAIL!!".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
        return 1
    else:
        sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Auto reconfig PASS!!".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
        return 0

#_*****************************************************************************
#_ Function   : send_file_to_console
#_ Description: 
#_ Inputs     : cmd: the command tobe execute
#_ Outputs    : return value from the result of input command
#_ Notice     : 
#_*****************************************************************************
def send_file_to_console(ip, from_file,to_file, MBSNdict):
    # os.system("rm -rf /root/.ssh/known_hosts")
    result_str="Another instance of"
    while "Another instance of" in  result_str:
        cmdstr = "sshpass -p 'overlake' scp -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null {0} stuser@{1}:{2}".format(from_file, ip, to_file)
        sendlog("[mbsn:{0} bmc_ip: {1} bmc_mac: {2}] cmdstr:{3}".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"], cmdstr))
        # (status,result) = commands.getstatusoutput(cmdstr)
        p = subprocess.Popen(cmdstr, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        stdout,stderr = p.communicate()
        output=stdout.strip() 
        ret=p.returncode
        status = ret
        result = output
        sendlog("[mbsn:{0} bmc_ip: {1} bmc_mac: {2}] status:{3}".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"], status))
        sendlog("[mbsn:{0} bmc_ip: {1} bmc_mac: {2}] result:{3}".format(MBSNdict["mbsn"], MBSNdict["bmc_ip"], MBSNdict["bmc_mac_addr"], result))
        result_str = str(result)
        print(result_str)
        time.sleep(1)
    return result

#*****************************************************************************
# Function   : check_flag
# Description: Check UUT flag
# Inputs     : NA
# Outputs    : NA
# Notice     : 
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
    if diff/60 > 300:
        os.system("rm -rf {0}".format(updating_flag))
        sendlog("[mbsn:{0}, cp_ip: {1}]update process to long! Remove the flag and do update again!".format(sn_info_list["mbsn"], sn_info_list["cp_ip"]), RED)
    
    
#*****************************************************************************
# Function   : clear_flag
# Description: Clear UUT flag
# Inputs     : NA
# Outputs    : NA
# Notice     : 
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


#*****************************************************************************
# Function   : set_cp_boot_mode
# Description: Set CP Boot Mode
# Inputs     : MBSNdict, mode, log_path
# Outputs    : 0:SUCCESS 1:FAIL
# Notice     : 
#*****************************************************************************
def set_cp_boot_mode(MBSNdict, mode, log_path):
    if mode == 0:
        #Set bootmode to 0
        sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Set bootmode to 0".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
        cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/{}\"".format(MBSNdict["cp_ip"], g_cmd_set_bootmode_to_zero)
        result = getresult(cmd).split('\n')
        sendlog(result, 0, log_path)
        time.sleep(10)
        if result != "":
            if "boot mode is set to 0x00 through cerberus" in result:
                sendlog("Set boot mode to 0 success !", 0, log_path)
            else:
                sendlog("Set boot mode to 0 fail !", 0, log_path)
                return 1
        else:
            sendlog("Can't get result - set boot mode to 0", 0, log_path)
            return 1
    elif mode == 2:
        #Set bootmode to 2
        sendlog ("[mbsn:{0} cp_ip: {1} cp_mac: {2}] Set bootmode to 2".format(MBSNdict["mbsn"], MBSNdict["cp_ip"], MBSNdict["cp_mac_addr"]), 0, log_path)
        cmd = "sshpass -p overlake ssh -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null stuser@{} \"echo overlake | sudo -S /usr/bin/{}\"".format(MBSNdict["cp_ip"], g_cmd_set_bootmode_to_two)
        result = getresult(cmd).split('\n')
        sendlog(result, 0, log_path)
        time.sleep(10)
        if result != "":
            if "boot mode is set to 0x02 through cerberus" in result:
                sendlog("Set boot mode to 2 success !", 0, log_path)
            else:
                sendlog("Set boot mode to 2 fail !", 0, log_path)
                return 1
        else:
            sendlog("Can't get result - set boot mode to 2", 0, log_path)
            return 1
    else:
        sendlog(f"Set boot mode {mode} no support !", 0, log_path)
        return 1
    return 0

### L11 cp config portion

def get_bsl_return_folder_list():
    # get bsl return folder list
    #g_bsl_return_folder = "/mnt/test_log/{}/BSL_return".format(g_project)
    global g_bsl_return_folder
    if os.path.exists(g_bsl_return_folder) == False:
        os.makedirs(g_bsl_return_folder)
    bsl_return_folder_list = {}
    files = os.listdir(g_bsl_return_folder)

    for file in files:
        infos = getresult("cat {}/{}".format(g_bsl_return_folder, file)).replace('\n', '').strip()
        sn = file.split('.')[0].replace('\n', '').strip()
        rmip = infos.split(',')[0].replace('\n', '').strip()
        rmport = infos.split(',')[1].replace('\n', '').strip()
        
        bsl_return_folder_list[sn] = [rmip,rmport]
    print("bsl_return_folder_list: ")
    print(bsl_return_folder_list)
    return bsl_return_folder_list


class bsl_soc_flash:
    def __init__(self):
        self.g_rm_username        = "root"
        self.g_rm_password        = "$pl3nd1D"
        self.g_cmd_connect_cp =    "start serial session -i {0} -b 1"
        self.g_cmd_disconnect_cp = "stop serial session -i {0} -b 1"
        self.g_cmd_show_system_info = "show system info -i {0}"
        self.g_cmd_cat_cp_logfile = "cat /tmp/cp_cmd.log"
        self.g_cmd_show_tftp = "show manager tftp list"
        self.tftp_ip=""
        self.replace_image_name = {"0002.17.240911-prd":["dropcp-2.17FW-stos2008.6.23101601","dropcp-2.17.1FW-stos2008.6.23101601"]}
        self.g_cmd_set_bootmode_to_one = "bootmode set 1"

        self.sn_log_folder = None
        self.log_name = None
        self.log_path = None
        self.upload_img_flag = None
        self.flag_name =  None
        self.flag_path =  None
        self.CP_IP=None
        self.fip_pfm_file  =  None
        self.fip_fw_file =  None
        self.nitro_pfm_file =  None
        self.nitro_fw_file = None
        self.g_cp_Cerberus_fw= None

    
    def login_rm(self,sn_info_list):
        try:
            ssh_object = pxssh.pxssh(maxread=3000, timeout=5)
            sendlog("[rm_ip:{0:>12} mbsn:{1}] RM login1".format(sn_info_list["rm_ip"],sn_info_list["mbsn"]))
            print(f" host: {sn_info_list['rm_ip']} user: {self.g_rm_username} password: {self.g_rm_password}")
            ssh_object.SSH_OPTS = "-oCiphers=aes256-cbc"
            ssh_object.login(sn_info_list["rm_ip"], self.g_rm_username, self.g_rm_password, sync_multiplier=10, auto_prompt_reset=False)
            return ssh_object
        except pxssh.ExceptionPxssh as e:
            print(e)
            sendlog("[rm_ip:{0:>12} mbsn:{1}] login failed, delay 10s and retry".format(sn_info_list["rm_ip"],sn_info_list["mbsn"]))
            time.sleep(10)
            try:
                ssh_object = pxssh.pxssh(maxread=3000, timeout=5)
                sendlog("[rm_ip:{0:>12} mbsn:{1}] RM login2".format(sn_info_list["rm_ip"],sn_info_list["mbsn"]))
                ssh_object.login(sn_info_list["rm_ip"], self.g_rm_username, self.g_rm_password, sync_multiplier=10, auto_prompt_reset=False)
                return ssh_object
            except pxssh.ExceptionPxssh as e:
                sendlog("[rm_ip:{0:>12} mbsn:{1}] pxssh failed: login to RM.\n sterr:{2}".format(sn_info_list["rm_ip"],sn_info_list["mbsn"], e), RED)
                return None
            # sendlog("[rm_ip:{0:>12} rm_mac: {1}] pxssh failed: login to RM.".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"]), RED)
            # sendlog(e, RED)
            # return None

    def send_cmd_to_rm(self,ssh_object, sn_info_list, cmd, sleep_time, log_path = "",device = "RM"):
        try:
            ####check the link is connect or not, if not connect to rm again
            ssh_object.buffer = b"" #20230724 david
            # ssh_object.expect(r'.+')
            ssh_object.sendline(" ")
            ssh_object.prompt()
            
            if device == "CP":
                # print("return: "+ssh_object.before.decode ('utf-8').splitlines()[-1])
                if ssh_object.before.decode ('utf-8') == "" or "@localhost:" not in ssh_object.before.decode ('utf-8').splitlines()[-1]:

                    #disconnect to CP
                    ssh_object.sendline(self.g_cmd_disconnect_cp.format(sn_info_list["uut_to_rm_port"]))
                    time.sleep(1)
                    #connect to CP
                    ssh_object.sendline(self.g_cmd_connect_cp.format(sn_info_list["uut_to_rm_port"]))
                    ssh_object.sendline(" ")
                    ssh_object.prompt()
                    if ssh_object.before.decode ('utf-8') == "" or "@localhost:" not in ssh_object.before.decode ('utf-8').splitlines()[-1]:
                        sendlog("[rm_ip:{0:>12} mbsn:{1}] connect to CP fail".format(sn_info_list["rm_ip"] ,sn_info_list["mbsn"]), RED)
                        return 1, None
            elif device == "RM":
                if ssh_object.before.decode ('utf-8') == "" or "WcsCli#" not in ssh_object.before.decode ('utf-8').splitlines()[-1]:
                    #Login to RM switch
                    ssh_object = self.login_rm(sn_info_list)
                    if ssh_object == None:
                        return 1, None

            ssh_object.buffer = b"" #20230724 david
            sendlog("[rm_ip:{0:>12} mbsn:{1} {2}] cmd:{3}".format(sn_info_list["rm_ip"],sn_info_list["mbsn"], device, cmd))
            # ssh_object.expect(r'.+')
            if device == "CP" and not (g_cmd_reset_soc in cmd or g_cmd_reboot in cmd or cmd.startswith(" ")):
                cmd = cmd + " | tee /tmp/cp_cmd.log"
            print(f"[Send CMD]:{cmd}")
            ssh_object.sendline(cmd)
            time.sleep(sleep_time)
            ssh_object.prompt()
            if device == "CP":
                # print("return: "+ssh_object.before.decode ('utf-8').splitlines()[-1])
                if ssh_object.before.decode ('utf-8') == "" or "@localhost:" not in ssh_object.before.decode ('utf-8').splitlines()[-1]:
                    ssh_object.sendline(self.g_cmd_disconnect_cp.format(sn_info_list["uut_to_rm_port"]))
                    time.sleep(1)
                    #connect to CP
                    ssh_object.sendline(self.g_cmd_connect_cp.format(sn_info_list["uut_to_rm_port"]))
                    ssh_object.sendline(" ")
                    ssh_object.prompt()
                    if ssh_object.before.decode ('utf-8') == "" or "@localhost:" not in ssh_object.before.decode ('utf-8').splitlines()[-1]:
                        sendlog("[rm_ip:{0:>12} mbsn:{1}] connect to CP fail".format(sn_info_list["rm_ip"],sn_info_list["mbsn"]), RED)
                        return 1, None
                if not (g_cmd_reset_soc in cmd or g_cmd_reboot in cmd or cmd.startswith(" ")):
                    ssh_object.buffer = b""
                    if "writeFlashjic" in cmd: #FPGA FW update command.
                        ssh_object.sendline(self.g_cmd_cat_cp_logfile+" | tail -10") #The full output about FPGA 4.4.4 update is too long to get cp prompt, only print the last 10 lines.
                    else:
                        ssh_object.sendline(self.g_cmd_cat_cp_logfile)
                    ssh_object.prompt()
                    if ssh_object.before.decode ('utf-8') == "" or "@localhost:" not in ssh_object.before.decode ('utf-8').splitlines()[-1]:
                        sendlog("[rm_ip:{0:>12}  mbsn:{1}] connect to CP fail".format(sn_info_list["rm_ip"],sn_info_list["mbsn"]), RED)
                        return 1, None
            elif device == "RM":
                if ssh_object.before.decode ('utf-8') == "" or "WcsCli#" not in ssh_object.before.decode ('utf-8').splitlines()[-1]:
                    #Login to RM switch
                    ssh_object = self.login_rm(sn_info_list)
                    if ssh_object == None:
                        return 1, None
            sendlog(ssh_object.before.decode ('utf-8').replace("'",''), 0, log_path) #20231101
            return 0, ssh_object.before.decode ('utf-8')
        except pxssh.ExceptionPxssh as e:
            sendlog("[rm_ip:{0:>12} mbsn:{1} {2}] pxssh failed: can not execute cmd:{5}".format(sn_info_list["rm_ip"],sn_info_list["mbsn"], device, cmd), RED)
            sendlog(e, RED)
            return 1, None

    def disconnect_cp_by_rm(self,ssh_object, sn_info_list):
        try:
            locallogin = False
            if ssh_object == None:
                ssh_object = pxssh.pxssh(timeout=5)
                ssh_object.login(sn_info_list["rm_ip"], self.g_rm_username, self.g_rm_password, sync_multiplier=10, auto_prompt_reset=False)
                locallogin = True
            ssh_object.buffer = b"" #20230724 david
            # ssh_object.expect(r'.+')
            ssh_object.sendline(self.g_cmd_disconnect_cp.format(sn_info_list["uut_to_rm_port"]))
            ssh_object.prompt()
            sendlog(ssh_object.before.decode ('utf-8'))
            if locallogin:
                ssh_object.logout()
            return 0
        except pxssh.ExceptionPxssh as e:
            sendlog("[rm_ip:{0:>12} mbsn:{1}] pxssh failed: can not disconnect other device".format(sn_info_list["rm_ip"],sn_info_list["mbsn"]), RED)
            sendlog(e, RED)
            return 1

    def is_success(self,res):
        completion = False
        for line in res.split("\n"):
            if "Completion Code:" in line:
                if "Success" in line:
                    completion = True
                else:
                    completion = False
        return completion    

    def connect_cp_by_rm(self,ssh_object, sn_info_list):
        try:
            ssh_object.buffer = b"" #20230724 david
            # ssh_object.expect(r'.+')
            ssh_object.sendline(self.g_cmd_connect_cp.format(sn_info_list["uut_to_rm_port"]))
            ssh_object.sendline(" ")
            ssh_object.prompt()
            sendlog(ssh_object.before.decode ('utf-8'))
            if ssh_object.before.decode ('utf-8') == "" or "@localhost:" not in ssh_object.before.decode ('utf-8').splitlines()[-1]:
                #disconnect to CP
                ssh_object.sendline(self.g_cmd_disconnect_cp.format(sn_info_list["uut_to_rm_port"]))
                time.sleep(1)
                #connect to CP
                ssh_object.sendline(self.g_cmd_connect_cp.format(sn_info_list["uut_to_rm_port"]))
                ssh_object.sendline(" ")
                ssh_object.prompt()
                #sendlog(ssh_object.before.decode ('utf-8'))
                if ssh_object.before.decode ('utf-8') == "" or "@localhost:" not in ssh_object.before.decode ('utf-8').splitlines()[-1]:
                    sendlog("[rm_ip:{0:>12} mbsn:{1}] connect to CP fail".format(sn_info_list["rm_ip"],sn_info_list["mbsn"]), RED)
                    return 1
            return 0
        except pxssh.ExceptionPxssh as e:
            sendlog("[rm_ip:{0:>12} mbsn:{1}] pxssh failed: can not login to CP by port".format(sn_info_list["rm_ip"],sn_info_list["mbsn"]), RED)
            sendlog(e, RED)
            return 1
        
    def send_cmd_to_cp(self,ssh_object, sn_info_list, cmd, sleep_time, log_path = ""):
        return self.send_cmd_to_rm(ssh_object, sn_info_list, cmd, sleep_time, log_path,device="CP")
    
    def update_soc_fw_bsl(self,sn_info_list, rmip):
        sn_info_list["rm_ip"] = rmip
        self.sn_log_folder = "{0}/{1}".format(g_log_folder, sn_info_list["mbsn"])
        self.log_name = "{0}_update_soc_fw.log".format(sn_info_list["mbsn"])
        self.log_path = "{0}/{1}".format(self.sn_log_folder, self.log_name)
        self.upload_img_flag = "{0}/{1}_overlakeimg_flag.log".format(g_log_folder,sn_info_list["mbsn"])
        self.flag_name = "{0}_first_update_soc_fw.log".format(sn_info_list["mbsn"])
        self.flag_path = "{0}/{1}".format(self.sn_log_folder, self.flag_name)
        self.CP_IP=""
        self.fip_pfm_file  = "A2040.FIP.PFM.{}.bin".format(int(sn_info_list["CP_SOC_FIP_PFMID"],16))
        self.fip_fw_file = "fip.bin"
        self.nitro_pfm_file = "A2040.NITRO.PFM.{}.bin".format(int(sn_info_list["CP_SOC_NITRO_PFMID"],16))
        self.nitro_fw_file = "nitro.img"
        self.g_cp_Cerberus_fw="cerberus_v{0}.bin".format(sn_info_list["CP_CERBERUS_FW"])
        cmd = "find /tftpboot/firmware/Celestial_Peak/ -name {}".format(upgrade_image.format(sn_info_list["CP_SOC_OS_FW"]))
        res = getresult(cmd)
        self.g_cp_Cerberus_fw_loc="/project/firmware/{0}/cp/{1}".format(g_project.lower(),self.g_cp_Cerberus_fw)
        image_path = res.split(upgrade_image.format(sn_info_list["CP_SOC_OS_FW"]))[0].replace("/tftpboot/","")
        #20250421 WayneXu 0002.17.240911-prd use the same image name compare to previous version
        print(sn_info_list["CP_SOC_FIP_FW"])
        print(sn_info_list["CP_SOC_NITRO_FW"])
        print(self.replace_image_name)
        if sn_info_list["CP_SOC_FIP_FW"] in self.replace_image_name and sn_info_list["CP_SOC_NITRO_FW"] in self.replace_image_name:
            image_path = image_path.replace(self.replace_image_name[sn_info_list["CP_SOC_FIP_FW"]][0],self.replace_image_name[sn_info_list["CP_SOC_FIP_FW"]][1])
        # login RM
        try:
            os.makedirs(self.sn_log_folder)
            sendlog("[mbsn:{0}]make log folder ({1}) success".format(sn_info_list["mbsn"], self.sn_log_folder), GREEN)
        except OSError as e:
            if e.errno == errno.EEXIST:
                sendlog("[mbsn:{0}]log folder ({1}) exist".format(sn_info_list["mbsn"], self.sn_log_folder), GREEN)
            else:
                sendlog("[mbsn:{0}]{1}".format(sn_info_list["mbsn"], e))
                return 1
            

        ssh_object = self.login_rm(sn_info_list)
        if ssh_object == None:
            return 1
        
        #Disconnect other device
        if self.disconnect_cp_by_rm(ssh_object, sn_info_list) == 1:
            return 1
        
        #check tftp list from RM
        ret, res = self.send_cmd_to_rm(ssh_object, sn_info_list, self.g_cmd_show_tftp, 100, self.log_path)
        if ret != 0:
            return 1
        else:
            if res != "":
                if upgrade_image.format(sn_info_list["CP_SOC_OS_FW"]) in res:
                    sendlog("[mbsn:{0}] {1} image from TFTP to RM success !".format(sn_info_list["mbsn"], upgrade_image.format(sn_info_list["CP_SOC_OS_FW"])))
                else:
                    #Copy image from TFTP to RM
                    ret, res =  self.send_cmd_to_rm(ssh_object, sn_info_list, g_cmd_copy_image_to_rm.format(self.tftp_ip, image_path, upgrade_image.format(sn_info_list["CP_SOC_OS_FW"])), 200, self.log_path)
                    if ret != 0:
                        return 1
                    else:
                        if res != "":
                            if self.is_success(res):
                                os.system("touch {0}".format(self.upload_img_flag))
                                sendlog("[mbsn:{0}] Copy image from TFTP to RM success !".format(sn_info_list["mbsn"]))
                            else:
                                sendlog("[mbsn:{0}] Copy image from TFTP to RM fail !".format(sn_info_list["mbsn"]))
                                return 1
                        else:
                            sendlog("[mbsn:{0}] Can not get result - copy image from TFTP to RM".format(sn_info_list["mbsn"]))
                            return 1
            else:
                sendlog("[mbsn:{0}] Can not get result - check image on SoC".format(sn_info_list["mbsn"]))
                return 1
        
        #Mount image on SoC
        ret, res =  self.send_cmd_to_rm(ssh_object, sn_info_list, g_cmd_mount_image_on_soc.format(sn_info_list["uut_to_rm_port"], upgrade_image.format(sn_info_list["CP_SOC_OS_FW"])), 20, self.log_path)
        if ret != 0:
            return 1
        else:
            if res != "":
                if self.is_success(res):
                    sendlog("[mbsn:{0}] Mount image on SoC success !".format(sn_info_list["mbsn"]))
                else:
                    sendlog("[mbsn:{0}] Mount image on SoC fail !".format(sn_info_list["mbsn"]))
                    self.send_cmd_to_rm(ssh_object, sn_info_list, "set system boot -t eMMC -i {0} -b 1".format(sn_info_list["uut_to_rm_port"]), 5, self.log_path)
                    self.send_cmd_to_rm(ssh_object, sn_info_list, "set system reset -i {0} -b 1".format(sn_info_list["uut_to_rm_port"]), 5, self.log_path)
                    self.send_cmd_to_rm(ssh_object, sn_info_list, "set system remotedrive unmount -i {0} -b 1".format(sn_info_list["uut_to_rm_port"]), 5, self.log_path)
                    self.send_cmd_to_rm(ssh_object, sn_info_list, "set system cmd -i {0} -c mc reset cold".format(sn_info_list["uut_to_rm_port"]), 5, self.log_path)
                    time.sleep(200) #for BMC reset
                    return 1
            else:
                sendlog("[mbsn:{0}] Can not get result - mount image on SoC".format(sn_info_list["mbsn"]))
                return 1

        #Login to CP by port
        if self.connect_cp_by_rm(ssh_object, sn_info_list) == 1:
            return 1

        #Check "sda" drive mounted
        ret, res = self.send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_check_sda_exist, 0, self.log_path)
        if ret != 0:
            return 1
        else:
            if res != "":
                if "sda1" in res:
                    sendlog("[mbsn:{0}] Check sda drive mounted success !".format(sn_info_list["mbsn"]))
                else:
                    sendlog("[mbsn:{0}] Check sda drive mounted fail !".format(sn_info_list["mbsn"]))
                    return 1
            else:
                sendlog("[mbsn:{0}] Can not get result - check sda drive mounted".format(sn_info_list["mbsn"]))
                return 1

        #Set bootmode to 1
        ret, res = self.send_cmd_to_cp(ssh_object, sn_info_list, self.g_cmd_set_bootmode_to_one, 0, self.log_path)
        if ret != 0:
            return 1
        else:
            if res != "":
                if "boot mode is set to 0x01" in res:
                    sendlog("[mbsn:{0}] Set boot mode to 1 success !".format(sn_info_list["mbsn"]))
                else:
                    sendlog("[mbsn:{0}] Set boot mode to 1 fail !".format(sn_info_list["mbsn"]))
                    return 1
            else:
                sendlog("[mbsn:0{0}] Can not get result - set boot mode to 1".format(sn_info_list["mbsn"]))
                return 1
        
        #Reboot the SoC
        ret, res = self.send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_reboot, 150, self.log_path)
        if ret != 0:
            ret, res = self.send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, self.log_path)
            return 1

        ret, res = self.send_cmd_to_cp(ssh_object, sn_info_list, " ", 10, self.log_path)
        if ret != 0:
                ret, res = self.send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, self.log_path)
                return 1
        else:
            if res !="":
                #print "DBG:{0}".format(res)
                if "@localhost:" in res.split("\n")[-1]:
                    sendlog("[mbsn:{0}] Reboot SOC success !".format(sn_info_list["mbsn"])) 
                else:
                    time.sleep(10)
                    ret, res = self.send_cmd_to_cp(ssh_object, sn_info_list, " ", 3, self.log_path)
                    if ret != 0:
                        ret, res = self.send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, self.log_path)
                        return 1
                    else:
                        if res !="":
                            if "@localhost:" in res.split("\n")[-1]:
                                sendlog("[mbsn:{0}] Reboot SOC success !".format(sn_info_list["mbsn"]))
                            else:
                                sendlog("[mbsn:{0}] Reboot SOC fail!".format(sn_info_list["mbsn"]))
                                ret, res = self.send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, self.log_path)
                                return 1
                        else:
                            sendlog("[mbsn:{0}] Can not get result - After reboot SOC!!".format(sn_info_list["mbsn"]))
                            ret, res = self.send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, self.log_path)
                            return 1
            else:
                sendlog("[mbsn:{0}] Can not get result - After reboot SOC!!".format(sn_info_list["mbsn"]))
                return 1

        #Execute "socflash" command
        ret, res = self.send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_socflash, 300, self.log_path)
        if ret != 0:
            ret, res = self.send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, self.log_path)
            return 1

        # remove flag
        flagpath=g_bsl_return_folder + "/{0}".format(sn_info_list["mbsn"])
        if os.path.isfile(flagpath):
            print("Remove flag {}".format(flagpath))
            os.system("rm {}".format(flagpath))
        sendlog("[mbsn:{0}] Execute socflash command success!!!".format(sn_info_list["mbsn"]))

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
    except Exception as err:
        sendlog("{0}".format(err))
        sys.exit(1)
            
    #20231102 David add
    if not os.path.isfile(auto_reconfig_service_server_loc):
        sendlog("File {} not exist, please check it!!".format(auto_reconfig_service_server_loc))
        sys.exit(1)
    
    if not os.path.isfile(auto_reconfig_python_server_loc):
        sendlog("File {} not exist, please check it!!".format(auto_reconfig_python_server_loc))
        sys.exit(1)
        
    show_info()
    
    #initial
    print("rm -rf /root/.ssh/known_hosts...")
    os.system("rm -rf /root/.ssh/known_hosts")

    p = ""
    mbsn_info_list = []
    bsl_return_list=get_bsl_return_folder_list()
    ret = get_mbsn_info_from_sf_folder(mbsn_info_list)
    if ret != 0:
        log = "get_mbsn_info_from_sf_folder Fail"
        sendlog(log, FAIL)
    else:
        #print "-------------"
        #print mbsn_info_list
        #print "-------------"
        for i in range(len(mbsn_info_list)):
            print ("-" * 100)
            print (mbsn_info_list[i])
            print ("-" * 100)
            sn_log_folder = "{0}/{1}".format(g_log_folder, mbsn_info_list[i]["mbsn"])
            record_log_name = "{0}_do_record_CP_golden_image_version.log".format(mbsn_info_list[i]["mbsn"])
            record_log_path = "{0}/{1}".format(sn_log_folder, record_log_name)
            # check whether the cp card is bsl return
            for sn, (rmip, rmport) in bsl_return_list.items():
                print("sn: {0}, rmip: {1}, rmport: {2}".format(sn, rmip,rmport))
                print("mbsn_info_list[i]['mbsn']: {0}".format(mbsn_info_list[i]['mbsn']))
                if sn == mbsn_info_list[i]['mbsn']:
                    sendlog("mbsn:{0} is bsl return cp card, need upgrade soc by RM".format(mbsn_info_list[i]['mbsn']), GREEN)
                    mbsn_info_list[i]["uut_to_rm_port"]=rmport
                    manager = bsl_soc_flash()
                    manager.update_soc_fw_bsl(mbsn_info_list[i], rmip)
                    mbsn_info_list[i]["cp_ip"] = get_ip(mbsn_info_list[i]["cp_mac_addr"])
                    if mbsn_info_list[i]["cp_ip"] != 1:# if cp card is able to connect. 
                        flagpath=g_bsl_return_folder + "/{0}".format(sn)
                        if os.path.isfile(flagpath):
                            print("Remove flag {}".format(flagpath))
                            os.system("rm {}".format(flagpath))

            if not mbsn_info_list[i]["is_reconfig"]:
                p = Process(target=do_record_CP_and_reconifg, args=(mbsn_info_list[i],))
                if p != "":
                    p.start()
                if i != 0 and i%11 == 0: #20230829 David add prevent server busy
                    time.sleep(10)
            else:
                if os.path.isfile(record_log_path):
                    golden_image_chk_result = chk_golden_image_log_file(mbsn_info_list[i])
                    print(f"============{golden_image_chk_result}=============")
                    if golden_image_chk_result == 0:
                        sendlog("{0}_do_record_CP_golden_image_version.log content check PASS!".format(mbsn_info_list[i]["mbsn"]))
                        msg =  "[mbsn:{0}, cp_ip:{1}, cp_mac:{2}]reconfig already done".format(mbsn_info_list[i]["mbsn"], mbsn_info_list[i]["cp_ip"], mbsn_info_list[i]["cp_mac_addr"])
                        sendlog(msg)
                    else:
                        cmd = f"rm -rf {sn_log_folder}"
                        getresult(cmd)
                        sendlog("{0}_do_record_CP_golden_image_version.log content check FAIL!".format(mbsn_info_list[i]["mbsn"]))

                        p = Process(target=do_record_CP_and_reconifg, args=(mbsn_info_list[i],))
                        if p != "":
                            p.start()
                        if i != 0 and i%11 == 0: #20230829 David add prevent server busy
                            time.sleep(10)
                else:
                    p = Process(target=do_record_CP_and_reconifg, args=(mbsn_info_list[i],))
                    if p != "":
                        p.start()
                    if i != 0 and i%11 == 0: #20230829 David add prevent server busy
                        time.sleep(10)
    # if p != "":
    #   p.join()
    if build_side != "QMF" and build_side != "QCG": # 20230707 David modify QMF use crontab to run
        print ("wait 180 sec")
        time.sleep(180)
    sys.exit(0)