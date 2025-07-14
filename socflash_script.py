from multiprocessing import Process
from pexpect import pxssh
from colorama import Fore,Style
import sys
import os
import time 
import subprocess
import errno
import re
import base64
from zeep import Client
import json

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
VERSION			= "2.0.6"
EDITOR			= "Eric"
RELEASE_DATE	= "2024/12/18"
#Sai modify location for QMF 
g_model = "MODEL"
g_project = "T6H"
g_api_sf = True
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
api_url = 'http://192.168.66.20/AMA_L11/AMAService.svc?singleWsdl'
PXE_map = { "192.168.202.24": "Q1","192.168.202.52" : "Q2","192.168.202.53" : "Q3","192.168.202.20": "Q5","192.168.202.26": "Q9", "192.168.202.47": "Q8", "192.168.202.46": "Q7","192.168.202.21": "Q6"}
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
g_cmd_RM_API_FPGA_info = "curl -k -u 'root':'$pl3nd1D' -X GET https://{0}:8080/{1}/redfish/v1/System/FPGA/1"
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


def getresult(arg1):

    p = subprocess.Popen(arg1, stdout=subprocess.PIPE, shell=True,encoding="utf-8")
    (text, err) = p.communicate()
    res = text
    
    return res

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
                    #print(log,"PASS")
                    #log = "Check RM Connection IP ={0}".format(line)
                    if os.system(g_cmd_ping.format(line)) == 0:
                        print("Get_IP MAC = {0} IP = {1:.<12}".format(mac_trans,line),"PASS")
                        return line
                else:
                    break
        print(log,"FAIL")
        return 1
    else:
        print("Unknown build side","FAIL")
        return 1

def is_success(res):
    completion = False
    for line in res.split("\n"):
        if "Completion Code:" in line:
            if "Success" in line:
                completion = True
            else:
                completion = False
    return completion
	
def connect_cp_by_rm(ssh_object, sn_info_list):
    try:
        ssh_object.buffer = b"" #20230724 david
        # ssh_object.expect(r'.+')
        ssh_object.sendline(g_cmd_connect_cp.format(sn_info_list["uut_to_rm_port"]))
        ssh_object.sendline(" ")
        ssh_object.prompt()
        print(ssh_object.before.decode ('utf-8'))
        if ssh_object.before.decode ('utf-8') == "" or "@localhost:" not in ssh_object.before.decode ('utf-8').splitlines()[-1]:
            #disconnect to CP
            ssh_object.sendline(g_cmd_disconnect_cp.format(sn_info_list["uut_to_rm_port"]))
            time.sleep(2)
            #connect to CP
            ssh_object.sendline(g_cmd_connect_cp.format(sn_info_list["uut_to_rm_port"]))
            ssh_object.sendline(" ")
            ssh_object.prompt()
            #print(ssh_object.before.decode ('utf-8'))
            if ssh_object.before.decode ('utf-8') == "" or "@localhost:" not in ssh_object.before.decode ('utf-8').splitlines()[-1]:
                print("[rm_ip:{0:>12} rm_mac: {1} RACKSN:{2} SN:{3}] connect to CP fail".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"],sn_info_list["RACKSN"],sn_info_list["sn"]), RED)
                clear_flag(sn_info_list)
                ssh_object.send('\003')
                return 1
        return 0
    except pxssh.ExceptionPxssh as e:
        print("[rm_ip:{0:>12} rm_mac: {1} RACKSN:{2} SN:{3}] pxssh failed: can not login to CP by port".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"],sn_info_list["RACKSN"],sn_info_list["sn"]), RED)
        print(e, RED)
        return 1



def send_cmd_to_cp(ssh_object, sn_info_list, cmd, sleep_time):
    return send_cmd_to_rm(ssh_object, sn_info_list, cmd, sleep_time,device="CP")

def send_cmd_to_rm(ssh_object, sn_info_list, cmd, sleep_time,device = "RM"):
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
                time.sleep(2)
                #connect to CP
                ssh_object.sendline(g_cmd_connect_cp.format(sn_info_list["uut_to_rm_port"]))
                ssh_object.sendline(" ")
                ssh_object.prompt()
                if ssh_object.before.decode ('utf-8') == "" or "@localhost:" not in ssh_object.before.decode ('utf-8').splitlines()[-1]:
                    print("[rm_ip:{0:>12} rm_mac: {1} RACKSN:{2} SN:{3}] connect to CP fail".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"],sn_info_list["RACKSN"],sn_info_list["sn"]), RED)
                    clear_flag(sn_info_list)
                    ssh_object.send('\003')
                    send_cmd_to_rm(ssh_object, sn_info_list, "set system boot -t eMMC -i {0} -b 1".format(sn_info_list["uut_to_rm_port"]), 5, )
                    send_cmd_to_rm(ssh_object, sn_info_list, "set system remotedrive unmount -i {0} -b 1".format(sn_info_list["uut_to_rm_port"]), 5, )
                    send_cmd_to_rm(ssh_object, sn_info_list, "set system reset -i {0}".format(sn_info_list["uut_to_rm_port"]), 5, )
                    time.sleep(180) #for CP reset
                    return 1, None
        elif device == "RM":
            if ssh_object.before.decode ('utf-8') == "" or "WcsCli#" not in ssh_object.before.decode ('utf-8').splitlines()[-1]:
                #Login to RM switch
                ssh_object = login_rm(sn_info_list)
                if ssh_object == None:
                    return 1, None
            
        ssh_object.buffer = b"" #20230724 david
        print("[rm_ip:{0:>12} rm_mac: {1} RACKSN:{2} SN:{3} {4}] cmd:{5}".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"], sn_info_list["RACKSN"],sn_info_list["sn"], device, cmd))
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
                time.sleep(2)
                #connect to CP
                ssh_object.sendline(g_cmd_connect_cp.format(sn_info_list["uut_to_rm_port"]))
                ssh_object.sendline(" ")
                ssh_object.prompt()
                if ssh_object.before.decode ('utf-8') == "" or "@localhost:" not in ssh_object.before.decode ('utf-8').splitlines()[-1]:
                    print("[rm_ip:{0:>12} rm_mac: {1} RACKSN:{2} SN:{3}] connect to CP fail".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"],sn_info_list["RACKSN"],sn_info_list["sn"]), RED)
                    clear_flag(sn_info_list)
                    ssh_object.send('\003')
                    send_cmd_to_rm(ssh_object, sn_info_list, "set system boot -t eMMC -i {0} -b 1".format(sn_info_list["uut_to_rm_port"]), 5, )
                    send_cmd_to_rm(ssh_object, sn_info_list, "set system remotedrive unmount -i {0} -b 1".format(sn_info_list["uut_to_rm_port"]), 5, )
                    send_cmd_to_rm(ssh_object, sn_info_list, "set system reset -i {0}".format(sn_info_list["uut_to_rm_port"]), 5, )
                    time.sleep(180) #for CP reset
                    return 1, None
            if not (g_cmd_reset_soc in cmd or g_cmd_reboot in cmd or cmd.startswith(" ")):
                ssh_object.buffer = b""
                if "writeFlashjic" in cmd: #FPGA FW update command.
                    ssh_object.sendline(g_cmd_cat_cp_logfile+" | tail -10") #The full output about FPGA 4.4.4 update is too long to get cp prompt, only print the last 10 lines.
                else:
                    ssh_object.sendline(g_cmd_cat_cp_logfile)
                ssh_object.prompt()
                if ssh_object.before.decode ('utf-8') == "" or "@localhost:" not in ssh_object.before.decode ('utf-8').splitlines()[-1]:
                    print("[rm_ip:{0:>12} rm_mac: {1} RACKSN:{2} SN:{3}] connect to CP fail".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"],sn_info_list["RACKSN"],sn_info_list["sn"]), RED)
                    clear_flag(sn_info_list)
                    ssh_object.send('\003')
                    send_cmd_to_rm(ssh_object, sn_info_list, "set system boot -t eMMC -i {0} -b 1".format(sn_info_list["uut_to_rm_port"]), 5, )
                    send_cmd_to_rm(ssh_object, sn_info_list, "set system remotedrive unmount -i {0} -b 1".format(sn_info_list["uut_to_rm_port"]), 5, )
                    send_cmd_to_rm(ssh_object, sn_info_list, "set system reset -i {0}".format(sn_info_list["uut_to_rm_port"]), 5, )
                    return 1, None
        elif device == "RM":
            if ssh_object.before.decode ('utf-8') == "" or "WcsCli#" not in ssh_object.before.decode ('utf-8').splitlines()[-1]:
                #Login to RM switch
                ssh_object = login_rm(sn_info_list)
                if ssh_object == None:
                    return 1, None
        print(ssh_object.before.decode ('utf-8').replace("'",''), 0, ) #20231101
        return 0, ssh_object.before.decode ('utf-8')
    except pxssh.ExceptionPxssh as e:
        print("[rm_ip:{0:>12} rm_mac: {1} RACKSN:{2} SN:{3} {4}] pxssh failed: can not execute cmd:{5}".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"], sn_info_list["RACKSN"],sn_info_list["sn"], device, cmd), RED)
        print(e, RED)
        return 1, None


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
            "is_need_cerberus_update": False,
            "is_reconfig": True,
            "is_GP":False
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
                
                #Get CP_SN from SN.txt. T6H is FPGASN. Jenny 20240913
                if "FPGASN" in line:
                    SNdict["CP_SN"] = line.split('=')[1].strip()
                
                # Arbitrary GP line to have script skip C229D. KA 20250630
                if "GP_CERBERUS_FW" in line:
                    SNdict["is_GP"] = True
            f.close()
            
            if SNdict["is_GP"]:
                sendlog("GP card recognized, skip for {0}".format(SNdict["sn"]))
                return 1

            #Check rackpn
            if rackpn == "":
                print("rackpn get fail ({0}.txt).".format(SNdict["sn"]),"FAIL")
                print(SNdict,"FAIL")
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
                print("sku_name get fail ({0}.txt).".format(SNdict["sn"]),"FAIL")
                print(SNdict,"FAIL")
                return 1

            #Get uut rm port number from rm table
            rm_table_file_path = "{0}/rm_table_{1}.txt".format(g_win_ccr_folder, sku_name)
            print(rm_table_file_path)
            f = open(rm_table_file_path)
            for line in f:
                if SNdict["LOCATION"] in line:
                    SNdict["uut_to_rm_port"] = line.split('-')[1].strip()
            f.close()

            print("SN={0}".format(SNdict["sn"]))
            
            #Get rm ip from DHCP
            print("get rm ip")
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
                print("rm ip get fail ({0}.txt).".format(SNdict["sn"]),"FAIL")
                print(SNdict,"FAIL")
                return 1
            
            #Get C2080 nic mac address by rm port, this is for build from L10.
            # SNdict["uut_mac_addr"] = get_mac_address_by_rm_port(SNdict)
            # if SNdict["uut_mac_addr"] == 1:
                # print("mac adddress by rm port get fail ({0}.txt).".format(SNdict["sn"]),"FAIL")
                # print(SNdict,"FAIL")
                # continue
            
            #Get uut ip from DHCP
            print("get uut ip: [{0}]{1} mac:{2}".format(SNdict["LOCATION"],SNdict["sn"], SNdict["uut_mac_addr"]))
            SNdict["uut_ip"] = get_ip(SNdict["uut_mac_addr"])

            #Get CP ip from DHCP
            print("get CP ip: [{0}]{1} mac:{2}".format(SNdict["LOCATION"],SNdict["sn"], SNdict["cp_mac_addr"]))
            SNdict["cp_ip"] = get_ip(SNdict["cp_mac_addr"])
            #Check reconfig flag
            if SNdict["uut_ip"] == 1 or SNdict["uut_ip"] == "":
                print("get uut ip: [{0}]{1} set is_reconfig to False".format(SNdict["LOCATION"],SNdict["sn"]))
                SNdict["is_reconfig"] = False
            else:
                print("[{0}]{1} is_reconfig is: {2}".format(SNdict["LOCATION"],SNdict["sn"], SNdict["is_reconfig"]))

            #Check dict info correct
            if SNdict["sn"] == SNdict["rm_mac_addr"] == SNdict["rm_mac_addr"] == SNdict["uut_to_rm_port"] == "":
                SNdict["is_dict_info_correct"] = False
            if SNdict["rm_ip"] == 1:
                SNdict["is_dict_info_correct"] = False

            if SNdict["is_dict_info_correct"]:
                return SNdict
            else:
                print("SN.txt ({0}.txt) config error.".format(SNdict["sn"]),"FAIL")
                print(SNdict,"FAIL")
                return 1
        else:
            print ("{0} is not file".format(file_name))
    
    return 1

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
        
        # For sanity, ensure image path is correct using hardcoded data for certain firmware versions
        # 20250421 WayneXu 0002.17.240911-prd use the same image name compare to previous version
        if sn_info_list["CP_SOC_FIP_FW"] in replace_image_name and sn_info_list["CP_SOC_NITRO_FW"] in replace_image_name:
            image_path = image_path.replace(replace_image_name[sn_info_list["CP_SOC_FIP_FW"]][0],replace_image_name[sn_info_list["CP_SOC_FIP_FW"]][1])
        return image_path
    else:
        sendlog("[RACKSN:{0} SN:{1}] Cannot find CP SOC image path".format(sn_info_list["RACKSN"], sn_info_list["sn"]), RED)
        return None

def update_soc_fw(sn_info_list):	  
    CP_IP=""
    sn_log_folder = "{0}/{1}".format(g_log_folder, sn_info_list["sn"])
    log_name = "{0}_update_rm_fw.log".format(sn_info_list["sn"])
    log_path = "{0}/{1}".format(sn_log_folder, log_name)
    upload_img_flag = "{0}/{1}_overlakeimg_flag_{2}.log".format(g_log_folder,sn_info_list["RACKSN"], sn_info_list["master_rm_port"])
    image_path = get_image_directory(sn_info_list)
    if image_path is None:
        return 1

    #Login to RM switch
    ssh_object = login_rm(sn_info_list)
    if ssh_object == None:
        return 1
    
    #Disconnect other device
    if disconnect_cp_by_rm(ssh_object, sn_info_list) == 1:
        return 1
    
    #check tftp list from RM
    ret, res = send_cmd_to_rm(ssh_object, sn_info_list, g_cmd_show_tftp, 100, )
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

    #Mount image on SoC
    ret, res = send_cmd_to_rm(ssh_object, sn_info_list, g_cmd_mount_image_on_soc.format(sn_info_list["uut_to_rm_port"], upgrade_image.format(sn_info_list["CP_SOC_OS_FW"])), 20, )
    if ret != 0:
        return 1
    else:
        if res != "":
            if is_success(res):
                print("[RACKSN:{0} SN:{1}] Mount image on SoC success !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
            else:
                print("[RACKSN:{0} SN:{1}] Mount image on SoC fail !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                send_cmd_to_rm(ssh_object, sn_info_list, "set system boot -t eMMC -i {0} -b 1".format(sn_info_list["uut_to_rm_port"]), 5, )
                send_cmd_to_rm(ssh_object, sn_info_list, "set system remotedrive unmount -i {0} -b 1".format(sn_info_list["uut_to_rm_port"]), 5, )
                send_cmd_to_rm(ssh_object, sn_info_list, "set manager port off -i {0}".format(sn_info_list["uut_to_rm_port"]), 5, )
                time.sleep(30) #for AC OFF
                send_cmd_to_rm(ssh_object, sn_info_list, "set manager port on -i {0}".format(sn_info_list["uut_to_rm_port"]), 5, )
                time.sleep(300) #for AC ON
                return 1
        else:
            print("[RACKSN:{0} SN:{1}] Can not get result - mount image on SoC".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
            return 1

    #Login to CP by port
    if connect_cp_by_rm(ssh_object, sn_info_list) == 1:
        return 1

    #Check "sda" drive mounted
    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_check_sda_exist, 0, )
    if ret != 0:
        return 1
    else:
        if res != "":
            if "sda1" in res:
                print("[RACKSN:{0} SN:{1}] Check sda drive mounted success !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
            else:
                print("[RACKSN:{0} SN:{1}] Check sda drive mounted fail !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                return 1
        else:
            print("[RACKSN:{0} SN:{1}] Can not get result - check sda drive mounted".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
            return 1

    #Set bootmode to 1
    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_one, 0, )
    if ret != 0:
        return 1
    else:
        if res != "":
            if "boot mode is set to 0x01" in res:
                print("[RACKSN:{0} SN:{1}] Set boot mode to 1 success !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
            else:
                print("[RACKSN:{0} SN:{1}] Set boot mode to 1 fail !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                return 1
        else:
            print("[RACKSN:{0} SN:{1}] Can not get result - set boot mode to 1".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
            return 1
    
    #Reboot the SoC
    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_reboot, 150, )
    if ret != 0:
        ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, )
        return 1

    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, " ", 10, )
    if ret != 0:
            ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, )
            return 1
    else:
        if res !="":
            #print "DBG:{0}".format(res)
            if "@localhost:" in res.split("\n")[-1]:
                print("[RACKSN:{0} SN:{1}] Reboot SOC success !".format(sn_info_list["RACKSN"],sn_info_list["sn"])) 
            else:
                time.sleep(10)
                ret, res = send_cmd_to_cp(ssh_object, sn_info_list, " ", 3, )
                if ret != 0:
                    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, )
                    return 1
                else:
                    if res !="":
                        if "@localhost:" in res.split("\n")[-1]:
                            print("[RACKSN:{0} SN:{1}] Reboot SOC success !".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                        else:
                            print("[RACKSN:{0} SN:{1}] Reboot SOC fail!".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                            ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, )
                            return 1
                    else:
                        print("[RACKSN:{0} SN:{1}] Can not get result - After reboot SOC!!".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
                        ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0, )
                        return 1
        else:
            print("[RACKSN:{0} SN:{1}] Can not get result - After reboot SOC!!".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
            return 1

    #Execute "socflash" command
    #For SOC firmware : 4.4.4 socflash need more sleep time for update. Jenny 20240919
    print("Waiting Socflash for 10mins")
    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_socflash, 10*60)
    if ret != 0:
        ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0)
        return 1
    print("[RACKSN:{0} SN:{1}] Execute socflash command success!!!".format(sn_info_list["RACKSN"],sn_info_list["sn"]))
    
    #set bootmode to 0
    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_set_bootmode_to_zero, 0)
    if ret != 0:
        return 1
    #reboot the server
    ret, res = send_cmd_to_cp(ssh_object, sn_info_list, g_cmd_reboot, 150)
    
 
def login_rm(sn_info_list):
    try:
        ssh_object = pxssh.pxssh(maxread=3000, timeout=5)
        print("[rm_ip:{0:>12} rm_mac: {1} RACKSN:{2} SN:{3}] RM login1".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"],sn_info_list["RACKSN"],sn_info_list["sn"]))
        ssh_object.login(sn_info_list["rm_ip"], g_rm_username, g_rm_password, sync_multiplier=10, auto_prompt_reset=False)
        return ssh_object
    except pxssh.ExceptionPxssh as e:
        print("[rm_ip:{0:>12} rm_mac: {1} RACKSN:{2} SN:{3}] login failed, delay 10s and retry".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"],sn_info_list["RACKSN"],sn_info_list["sn"]))
        time.sleep(10)
        try:
            ssh_object = pxssh.pxssh(maxread=3000, timeout=5)
            print("[rm_ip:{0:>12} rm_mac: {1} RACKSN:{2} SN:{3}] RM login2".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"],sn_info_list["RACKSN"],sn_info_list["sn"]))
            ssh_object.login(sn_info_list["rm_ip"], g_rm_username, g_rm_password, sync_multiplier=10, auto_prompt_reset=False)
            return ssh_object
        except pxssh.ExceptionPxssh as e:
            print("[rm_ip:{0:>12} rm_mac: {1} RACKSN:{2} SN:{3}] pxssh failed: login to RM.\n sterr:{4}".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"],sn_info_list["RACKSN"],sn_info_list["sn"], e), RED)
            return None
        # print("[rm_ip:{0:>12} rm_mac: {1}] pxssh failed: login to RM.".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"]), RED)
        # print(e, RED)
        # return None
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
        print(ssh_object.before.decode ('utf-8'))
        if locallogin:
            ssh_object.logout()
        return 0
    except pxssh.ExceptionPxssh as e:
        print("[rm_ip:{0:>12} rm_mac: {1} RACKSN:{2} SN:{3}] pxssh failed: can not disconnect other device".format(sn_info_list["rm_ip"], sn_info_list["rm_mac_addr"],sn_info_list["RACKSN"],sn_info_list["sn"]), RED)
        print(e, RED)
        return 1


def do_socflash(sf_file_list):
    sn_info_list = read_sn_info_from_config(sf_file_list)
    if sn_info_list != 1:
        ret = update_soc_fw(sn_info_list)
        if ret != 0:
            print("[RACKSN:{0} SN:{1}] SoC flash firmware FAIL".format(sn_info_list["RACKSN"],sn_info_list["sn"]), RED)
            return 1
        else:
            print("[RACKSN:{0} SN:{1}] SoC flash firmware PASS".format(sn_info_list["RACKSN"],sn_info_list["sn"]), GREEN)
            return 0
    else:
        print("[RACKSN:{0} SN:{1}] check SoC firmware FAIL. it can not update".format(sn_info_list["RACKSN"],sn_info_list["sn"]), RED)
        return 1

if __name__ == "__main__":
    sf_file_list = []
    bmc_ip_list  = []
    eth_ip_list = []
    sn = input(Fore.MAGENTA + "Please enter serial number of the servers:\n" + Style.RESET_ALL).strip().upper()  
    while len(sn) != 0:
        if 'p' in sn or 'P' in sn:
            sn_cleaned= re.sub(r'\x1B\[200~|\x1B\[201~', '', sn)
            sf_file_list.append(sn_cleaned +".txt")
            sn = input().strip().upper()
        else:
            print("The information is not a serial number of servers")
            sn = input().strip().lower()
            
    if not os.path.isdir(g_win_config_folder):
        print("{0} not found.".format(g_win_config_folder), RED)
        sys.exit(1)
            
    info = os.listdir(g_win_config_folder)
    print(sf_file_list)
    for i in range(len(sf_file_list)):
        p = Process(target=do_socflash, args=(sf_file_list[i],))
        if p != "":
            p.start()
        if i != 0 and i%11 == 0:
            time.sleep(10)
    
    os.system("cp -f /var/lib/dhcpd/dhcpd.leases /project/ ")
    sys.exit(0)