from threading import Thread, Lock
from pexpect import pxssh
import sys
import os
import time
import subprocess
from datetime import datetime
import pexpect
import base64
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio
import asyncssh

lock = Lock()

ESC_GREEN = "\033[32m"
ESC_RED = "\033[31m"
ESC_YELLOW_F = "\033[33;1m"
ESC_YELLOW = "\033[33m"
ESC_PINK = "\033[35m"
ESC_LBLUE = "\033[36m"
ESC_OFF = "\033[0m"

GREEN = 1
RED = 2
YELLOW = 3
PINK = 4
ORANGE = 5
BLUE = 6

PASS = "PASS"
FAIL = "FAIL"
VERSION = "2.0.3"
EDITOR = "Edward"
RELEASE_DATE = "2024/03/12"

# Added new skus for 8.1 LM/HH in here
current_8_point_1_lm = ("M1288874-001", "M1289494-001", "M1289493-001", "M1271465-001")
current_8_point_1_hh = ("M1271540-001", "M1271469-001", "M1288874-001")

current_date = datetime.now()
g_model = "MODEL"
g_racklog_t6ub = "t6ub"
g_WIN_T6UB = "T6UB"
g_log_folder = "/RACKLOG/{0}/RM_logs".format(g_racklog_t6ub)
g_mainlog_file = "{0}/monitor.log".format(g_log_folder)
g_win_config_folder = "/WIN/{0}/response/config".format(g_WIN_T6UB)

g_switch_config_files = ["sonic-aboot-broadcom-20201231.76.swi", "SW_Config.sh"]
SW_CONFIG_SH_8_1_LM = "SW_Config_8.1_LM.sh"
SW_CONFIG_SH_8_1_HH = "SW_Config_8.1_HH.sh"
SW_CONFIG_SH_8_1_LM_NO_UPLINK = "SW_Config_8.1_NO_UPLINK_LM.sh"
SW_CONFIG_SH_8_1_HH_NO_UPLINK = "SW_Config_8.1_NO_UPLINK_HH.sh"
g_ycable_files = ["AEC_VERMONT_MV_1.0_20220907.bin", "mux_update_T6J_A.py"]
g_script_folder = "/project/edward/L15/"

g_tftpboot_firmware_switch_folder = "/tftpboot/firmware/t6ub/switch_automation/"

g_switch_update_folder = "/host/FW_Update/"
g_switch_firmware_folder = "/usr/share/sonic/firmware/"

g_cmd_search_ip_QMF = "grep -B8 -A1 {0} /var/lib/dhcpd/dhcpd.leases | grep lease"
g_cmd_ping = "ping -c 3 {0}"

g_switch_passwords = ["password", "Temp123!"]
ycables_lm = [
    "Ethernet0",
    "Ethernet4",
    "Ethernet8",
    "Ethernet12",
    "Ethernet16",
    "Ethernet20",
    "Ethernet24",
    "Ethernet28",
    "Ethernet32",
    "Ethernet36",
    "Ethernet40",
    "Ethernet44",
    "Ethernet80",
    "Ethernet84",
    "Ethernet88",
    "Ethernet92",
    "Ethernet96",
    "Ethernet100",
    "Ethernet104",
    "Ethernet108",
    "Ethernet112",
    "Ethernet116",
    "Ethernet120",
    "Ethernet124",
    "Ethernet128",
    "Ethernet132",
    "Ethernet136",
    "Ethernet140",
    "Ethernet144",
    "Ethernet148",
    "Ethernet152",
    "Ethernet156",
    "Ethernet160",
    "Ethernet164",
    "Ethernet168",
    "Ethernet172",
    "Ethernet176",
    "Ethernet180",
    "Ethernet184",
    "Ethernet188",
    "Ethernet192",
    "Ethernet196",
    "Ethernet200",
    "Ethernet204",
    "Ethernet208",
    "Ethernet212",
    "Ethernet216",
    "Ethernet220",
    "Ethernet224",
    "Ethernet228",
    "Ethernet232",
    "Ethernet236",
    "Ethernet240",
    "Ethernet244",
    "Ethernet248",
    "Ethernet252",
]

ycable_hh = [
    "Ethernet0",
    "Ethernet4",
    "Ethernet8",
    "Ethernet12",
    "Ethernet16",
    "Ethernet20",
    "Ethernet40",
    "Ethernet44",
    "Ethernet48",
    "Ethernet52",
    "Ethernet56",
    "Ethernet60",
    "Ethernet64",
    "Ethernet68",
    "Ethernet72",
    "Ethernet76",
    "Ethernet80",
    "Ethernet84",
    "Ethernet104",
    "Ethernet108",
    "Ethernet112",
    "Ethernet116",
    "Ethernet120",
    "Ethernet124",
]


def sendlog(message="", color=0, logfile=""):
    if color == 1:
        ESC_color = ESC_GREEN
    elif color == 2:
        ESC_color = ESC_RED
    elif color == 3:
        ESC_color = ESC_YELLOW
    elif color == 4:
        ESC_color = ESC_PINK
    elif color == 5:
        ESC_color = ESC_YELLOW_F
    elif color == 6:
        ESC_color = ESC_LBLUE
    else:
        ESC_color = ESC_OFF

    if color == PASS or color == FAIL:
        if color == PASS:
            ESC_color = ESC_GREEN
        else:
            ESC_color = ESC_RED
        print(
            str(message)
            + "........................."
            + ESC_color
            + "["
            + color
            + "]"
            + ESC_OFF
        )
        message = str(message) + "........................." + "[" + color + "]"
    else:
        print(ESC_color + str(message) + ESC_OFF)

    # message = message.replace("'",'') #20230928 David add

    if logfile != "":
        cmd = "echo '{0} ====>> {1}' >>{2}".format(
            time.strftime("%m-%d-%y-%H:%M:%S"), message, logfile
        )
        os.system(cmd)

    cmd = "echo '{0} ====>> {1}' >>{2}".format(
        time.strftime("%m-%d-%y-%H:%M:%S"), message, g_mainlog_file
    )
    os.system(cmd)


def send_data_sf(start_time, message, log_type, sf_sn, location, station, log_file):

    st_file = "/home/Monitor_reconfig_CP/{0}.ST".format(sf_sn)

    head_location = "/WIN/" + g_WIN_T6UB + "/"
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
        # shutil.copyfile(st_file, win_st_file)
        os.system("cp -rf {0} {1}".format(st_file, win_st_file))
        count += 1
    os.system("cp -rf {0} {1}request/mac/{2}.ST".format(st_file, head_location, sf_sn))


def get_switch_configs():
    """
    Find *txt files in the last 30 mins, , files are accepted if these conditions are matched
    LOCATION=F29
    STATION=PRETEST
    RACKSN duplicates will be filtered out by the cmd below
    MSFPN belongs to predefined MSFPN 8.1LM/HH
    """
    switch_config = []
    cmd = "find /WIN/T6UB/response/config -type f -name '*.txt' -mmin -30 -exec grep -H 'RACKSN' {} \; | cut -d: -f1 | xargs -I {} grep -l 'LOCATION=F29' {}"
    # cmd = "find /WIN/T6UB/response/config -type f -name 'P812642870140065.txt' -mmin -500"
    success, result = getresult(cmd)
    print(f"Success code: {success}, result: {result}")
    if not success and not result:
        print("No .txt found in the last 15 mins!")
        sys.exit(3)
    for path in result.splitlines():
        path = path.replace("./", "")  # remove './' prefix
        print(path)
        print("Try open config file {0}".format(path))
        try:
            with open(path, "r") as file:
                contents = file.read()
                if "MLB0=T6UB,C2190" in contents and "STATION=PRETEST" in contents:
                    print("Found switch config file {0}".format(path))
                    msf_pn_match = False
                    for line in contents.splitlines():
                        if line.startswith("MSFPN="):
                            msf_pn_value = line.split("=")[1].strip()
                            print(msf_pn_value)
                            if (
                                msf_pn_value in current_8_point_1_hh
                                or msf_pn_value in current_8_point_1_lm
                            ):
                                msf_pn_match = True
                                break
                    if msf_pn_match:
                        SNdict = {}
                        SNdict["sn"] = path.split(".")[0].strip().split("/")[-1].strip()
                        for line in contents.splitlines():
                            if line.startswith("RACKSN="):
                                SNdict["RACKSN"] = line.split("=")[1].strip()
                            elif line.startswith("SWITCHSMLC1="):
                                SNdict["switch_a_mac"] = line.split(",")[1].strip()
                            elif line.startswith("SWITCHSMLC3="):
                                SNdict["switch_b_mac"] = line.split(",")[1].strip()
                            elif line.startswith("STATION="):
                                SNdict["STATION"] = line.split("=")[1].strip()
                            elif line.startswith("LOCATION="):
                                SNdict["LOCATION"] = line.split("=")[1].strip()
                            elif line.startswith("RACK_MOUNT_MAC1="):
                                SNdict["RM"] = line.split("=")[1].strip()
                            elif line.startswith("MSFPN="):
                                SNdict["MSFPN"] = line.split("=")[1].strip()
                        if not SNdict:
                            print("SNDict does not have any values")
                        switch_config.append(SNdict)
        except FileNotFoundError:
            print("File:{0} not found.".format(path))
        except Exception as e:
            print("EXCEPTION, " + e)
    return switch_config


def read_sn_info_from_config(file_name):
    if ".txt" in file_name:
        SNdict = {
            "sn": "NA",
            "RACKSN": "NA",
            "switch_a_mac": "NA",
            "switch_b_mac": "NA",
            "STATION": "NA",
            "LOCATION": "NA",
            "RM": "NA",
        }
        file_path = "{0}/{1}".format(g_win_config_folder, file_name)
        if os.path.isfile(file_path):
            SNdict["sn"] = file_path.split(".")[0].strip().split("/")[-1].strip()
            f = open(file_path)
            for line in f:
                if "RACKSN" in line:
                    SNdict["RACKSN"] = line.split("=")[1].strip()

                if "SWITCHSMLC0" in line:
                    SNdict["switch_a_mac"] = line.split(",")[1].strip()

                if "SWITCHSMLC1" in line:
                    SNdict["switch_b_mac"] = line.split(",")[1].strip()
                if "STATION" in line:
                    SNdict["STATION"] = line.split("=")[1].strip()
                if "LOCATION" in line:
                    SNdict["LOCATION"] = line.split("=")[1].strip()
                if "RACK_MOUNT_MAC1" in line:
                    SNdict["RM"] = line.split("=")[1].strip()
            f.close()
        return SNdict


def check_ping(ip_address):
    # Construct the ping command
    command = ["ping", "-c", "3", ip_address]

    # Execute the ping command
    try:
        output = subprocess.check_output(
            command, timeout=8, stderr=subprocess.STDOUT, universal_newlines=True
        )
        print(output)
        return True
    except subprocess.CalledProcessError:
        return False
    except subprocess.TimeoutExpired:
        return False


def getresult(arg1):
    try:
        # Start the subprocess
        p = subprocess.Popen(
            arg1,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            encoding="utf-8",
        )
        # Capture stdout and stderr
        (text, err) = p.communicate()
        # Check the return code
        if p.returncode == 0:
            # Command was successful
            return (True, text)
        elif p.returncode == 1 and text == "":
            # No matches found, but command executed successfully
            return (True, "")
        else:
            print("p.returncode = {0}".format(p.returncode))
            print("text = {0}".format(text))
            print("stderr = {0}".format(err))  # Print stderr for debugging
            return (True, text)
    except Exception as e:
        return (False, str(e))


def get_ip(mac_addr):
    ip = ""
    mac_trans = (
        mac_addr[:2]
        + ":"
        + mac_addr[2:4]
        + ":"
        + mac_addr[4:6]
        + ":"
        + mac_addr[6:8]
        + ":"
        + mac_addr[8:10]
        + ":"
        + mac_addr[10:12]
    )
    mac_trans = mac_trans.lower()
    search_ip_cmd = g_cmd_search_ip_QMF.format(mac_trans)
    success, ip = getresult(search_ip_cmd)

    if not success:
        log = "Failed to get IP for MAC = {0}, Error = {1}".format(mac_trans, ip)
        sendlog(log, color=RED)
        return 1  # Indicating failure

    if len(ip) >= 1:
        if "{" in ip:
            ip = ip.strip().split("{")

        for line in ip:
            if line != "":
                if " " in line:
                    line = line.split(" ")[1]
                log = "Get_ip MAC = {0} IP = {1}".format(mac_trans, line)
                sendlog(log, color=GREEN)
                if os.system(g_cmd_ping.format(line)) == 0:
                    return line
            else:
                break
    return 1  # Indicating failure


def is_config(sn_info):
    flag_path = g_log_folder + "/{0}/{0}.txt".format(sn_info["RACKSN"])
    flag_dir = g_log_folder + "/{0}/".format(sn_info["RACKSN"])
    updating_flag = g_log_folder + "/{0}/{1}.txt".format(sn_info["RACKSN"], "Updating")

    with lock:  # Ensure exclusive access while checking flags and directories
        if os.path.exists(flag_path):
            print("{0} already configured".format(sn_info["RACKSN"]))
            return True
        elif os.path.exists(updating_flag):
            print("{0} already configuring...".format(sn_info["RACKSN"]))
            return True
        elif os.path.exists(flag_dir):
            return False
        else:
            os.makedirs(flag_dir, exist_ok=True)
            return False


def switch_password():
    global g_switch_passwords
    g_switch_passwords = g_switch_passwords[::-1]


def login_to_RM(ip, at_step=None, username="root", password="$pl3nd1D"):
    if at_step != None:
        print(at_step)
    try:
        ssh_object = pxssh.pxssh()
        ssh_object.login(ip, username, password, auto_prompt_reset=False)
        return ssh_object
    except pxssh.ExceptionPxssh as e:
        print("Failed to login to RM")
        print(e)
    return None


def login_to_switch(ip, at_step=None, credentials=None):
    if at_step != None:
        print(at_step)
    for password in g_switch_passwords:
        try:
            ssh_object = pxssh.pxssh()
            ssh_object.login(ip, "admin", password, auto_prompt_reset=False)
            if password == g_switch_passwords[1]:
                switch_password()
                print("Password switched to: {0}".format(g_switch_passwords[0]))
            return ssh_object
        except pxssh.ExceptionPxssh as e:
            print("Failed to login to Switch")
            print(e)

    return None


def send_file_to_switch(ip, log):
    cmdstr = "sudo scp -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null root@10.0.3.254:{0}* /host/FW_Update/".format(
        g_tftpboot_firmware_switch_folder
    )
    ssh_object = login_to_switch(ip, "sending file to switch")
    if ssh_object == None:
        return None
    try:
        ssh_object.buffer = b""
        ssh_object.sendline(cmdstr)
        time.sleep(1)
        ssh_object.prompt()
        ssh_object.sendline("M1cr0$0ft")
        ssh_object.prompt()
        ssh_object.prompt(timeout=60)
        output = ssh_object.before.decode("utf-8")
        print(output)
        with open(log, "a") as file:
            # Write output to the file
            file.write(output + "\n")
        return 0
    except pxssh.ExceptionPxssh as e:
        print("Failed to run command")
        print(e)
        return None


def send_mux_firmware_to_switch(ip, log):
    cmdstr = "sudo scp -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null root@10.0.3.254:/tftpboot/firmware/t6ub/switch_automation/AEC_WYOMING_MW_1.4_20220907.bin /usr/share/sonic/firmware/"
    ssh_object = login_to_switch(ip, "send mux fw to switch !")
    if ssh_object == None:
        return None
    try:
        ssh_object.buffer = b""
        ssh_object.sendline(cmdstr)
        ssh_object.prompt()
        ssh_object.sendline("M1cr0$0ft")
        ssh_object.prompt()
        output = ssh_object.before.decode("utf-8")
        print(output)
        with open(log, "a") as file:
            # Write output to the file
            file.write(output + "\n")
        return 0
    except pxssh.ExceptionPxssh as e:
        print("Failed to run command")
        print(e)
        return None


def check_switch_os_version(ip, log):
    ssh_object = login_to_switch(ip, "checking switch os version")
    if ssh_object == None:
        return None
    try:
        ssh_object.buffer = b""
        ssh_object.sendline("show version")
        time.sleep(1)
        ssh_object.prompt()
        output = ssh_object.before.decode("utf-8")
        print(output)
        with open(log, "a") as file:
            # Write output to the file
            file.write(output + "\n")
        print(output)
        if "SONiC Software Version: SONiC.20201231.76" not in output:
            print("Os need update")
            ssh_object.buffer = b""
            ssh_object.sendline("sudo mkdir /host/FW_Update")
            time.sleep(1)
            ssh_object.prompt()
            output = ssh_object.before.decode("utf-8")
            print(output)
            with open(log, "a") as file:
                # Write output to the file
                file.write(output + "\n")
            return 1
        print("Os already updated")
        return 0
    except pxssh.ExceptionPxssh as e:
        print("Failed to run command")
        print(e)
        return None


def update_switch_os(ip, log):
    ssh_object = login_to_switch(ip, "Start updating switch OS!")
    if ssh_object == None:
        return None
    try:
        ssh_object.buffer = b""
        ssh_object.sendline(
            "sudo sonic-installer install /host/FW_Update/sonic-aboot-broadcom-20201231.76.swi -y"
        )
        ssh_object.prompt(timeout=60)
        ssh_object.prompt()
        output = ssh_object.before.decode("utf-8")
        if "Image SONiC-OS-20201231.76 is already installed":
            print("Image SONiC-OS-20201231.76 is already installed. Perform reboot !")
            ssh_object.buffer = b""
            ssh_object.sendline("sudo reboot")
            ssh_object.prompt(timeout=60)
            ssh_object.prompt()
            output += ssh_object.before.decode("utf-8")
        print(output)
        with open(log, "a") as file:
            # Write output to the file
            file.write(output + "\n")
        ssh_object.buffer = b""
        ssh_object.sendline("sudo reboot")
        output = ssh_object.before.decode("utf-8")
        print(output)
        with open(log, "a") as file:
            # Write output to the file
            file.write(output + "\n")
        return 0

    except pxssh.ExceptionPxssh as e:
        print("Failed to run command")
        print(e)
        return None


def send_cmd_to_switch(ip, log, cmd=""):
    ssh_object = login_to_switch(ip, "Sending [" + cmd + "] to switch: " + ip)
    if ssh_object == None:
        return None
    try:
        ssh_object.buffer = b""
        ssh_object.sendline(cmd)
        ssh_object.prompt(timeout=120)
        output = ssh_object.before.decode("utf-8")
        print(output)
        with open(log, "a") as file:
            # Write output to the file
            file.write(output + "\n")
        return 0
    except pxssh.ExceptionPxssh as e:
        print("Failed to run command")
        print(e)
        return None


async def update_psu_1717_to_1818(RM_IP):
    rm_ip = str(RM_IP)
    username = "root"
    password = "$pl3nd1D"

    # Increase concurrency limit
    semaphore = asyncio.Semaphore(10)

    encryption_algorithms = ["aes256-cbc", "aes192-cbc", "aes128-cbc", "3des-cbc"]

    async with asyncssh.connect(
        rm_ip,
        username=username,
        password=password,
        encryption_algs=encryption_algorithms,
        known_hosts=None,  # Automatically accept unknown host keys
    ) as ssh_session:
        print("Starting PSU update process for 1717 PSUs to 1818.")

        # Fetch the PSU firmware file
        print("Fetching PSU firmware file from TFTP server...")
        result = await ssh_session.run(
            "set manager tftp get -s 10.0.3.254 -f firmware/t6ub/psu/1818.2000.hex"
        )
        output = result.stdout
        print(f"PSU firmware file fetch output: {output}")
        if "Completion Code: Failure" in output:
            print("Failed to fetch PSU firmware file. Exiting the update process.")
            return None

        # Define the slots to check
        slots_to_check = [i for i in range(3, 43) if i not in range(17, 26)]
        print(f"Checking PSU versions for slots: {slots_to_check}")

        async def update_psu_with_limit(slot, ssh_session, semaphore):
            async with semaphore:
                await asyncio.sleep(0.1)  # Adding a small delay
                await update_psu(ssh_session, slot)

        async def check_psu_with_limit(slot):
            async with semaphore:
                await asyncio.sleep(0.1)  # Adding a small delay
                return await check_psu_version(ssh_session, slot)

        # Check PSU versions in parallel with limited concurrency
        tasks = [check_psu_with_limit(slot) for slot in slots_to_check]

        # Process each PSU version check as it completes
        slots_to_update = []
        for task in asyncio.as_completed(tasks):
            result = await task
            if result is not None:
                slots_to_update.append(result)
                # Immediately run the PSU update for the slot that requires it
                await update_psu_with_limit(result, ssh_session, semaphore)

        print(f"Slots updated: {slots_to_update}")

        if slots_to_update:
            print("Waiting 420 seconds for PSU updates to complete (for debugging)...")
            start_time = time.time()
            await asyncio.sleep(420)
            elapsed_time = time.time() - start_time
            print(f"{int(elapsed_time)} seconds have passed.")

        async def reset_psu_with_limit(slot, ssh_session, semaphore):
            async with semaphore:
                await asyncio.sleep(0.1)  # Adding a small delay
                await reset_psu(ssh_session, slot)

        # Reset PSUs in parallel with limited concurrency
        reset_tasks = [
            reset_psu_with_limit(slot, ssh_session, semaphore)
            for slot in slots_to_update
        ]
        await asyncio.gather(*reset_tasks)

        print("PSU update process completed.")


async def check_psu_version(ssh_session, slot):
    print(f"Checking PSU version for slot {slot}...")
    try:
        result = await ssh_session.run(f"show system psu version -i {slot}")
        response = result.stdout
        print(f"Response for slot {slot}: {response}")
        if "17171800" in response:
            print(f"Slot {slot} requires update.")
            return slot
        else:
            print(f"Slot {slot} does not require update or is not present.")
            return None
    except asyncssh.Error as e:
        print(f"Failed to check PSU version for slot {slot}: {str(e)}")
        return None


async def update_psu(ssh_session, slot):
    print(f"Updating PSU for slot {slot}...")
    try:
        await ssh_session.run(
            f"set system psu update -f 1818.2000.hex -t 1 -r -i {slot}"
        )
        print(f"Update command sent for slot {slot}")
    except asyncssh.Error as e:
        print(f"Failed to update PSU for slot {slot}: {str(e)}")


async def reset_psu(ssh_session, slot):
    print(f"Resetting PSU for slot {slot}...")
    try:
        await ssh_session.run(f"set system reset -i {slot}")
        print(f"Reset command sent for slot {slot}")
    except asyncssh.Error as e:
        print(f"Failed to reset PSU for slot {slot}: {str(e)}")


def run_SW_Config(ip, log, model, uplink):
    ssh_object = login_to_switch(ip, "running SW config")
    if ssh_object is None:
        return None
    try:
        ssh_object.buffer = b""
        print("Start configuring switch", ip, model, uplink)
        if model == "8.1lm":
            if not uplink:
                command = (
                    "sudo bash -c 'bash /host/FW_Update/"
                    + SW_CONFIG_SH_8_1_LM_NO_UPLINK
                    + " | tee -a /host/FW_Update/switch_config_results.log'"
                )
            else:
                command = (
                    "sudo bash -c 'bash /host/FW_Update/"
                    + SW_CONFIG_SH_8_1_LM
                    + " | tee -a /host/FW_Update/switch_config_results.log'"
                )
        elif model == "8.1hh":
            if not uplink:
                command = (
                    "sudo bash -c 'bash /host/FW_Update/"
                    + SW_CONFIG_SH_8_1_HH_NO_UPLINK
                    + " | tee -a /host/FW_Update/switch_config_results.log'"
                )
            else:
                command = (
                    "sudo bash -c 'bash /host/FW_Update/"
                    + SW_CONFIG_SH_8_1_HH
                    + " | tee -a /host/FW_Update/switch_config_results.log'"
                )
        else:
            print("Unknown model:", model)
            return None

        ssh_object.sendline(command)
        print("SLEEP FOR 5S")
        time.sleep(5)
        ssh_object.prompt()
        output = ssh_object.before.decode("utf-8")
        print(output)
        with open(log, "a") as file:
            # Write output to the file
            file.write(output + "\n")
        return 0
    except pxssh.ExceptionPxssh as e:
        print("Failed to run command")
        print(e)
        return None


def checkInterfaceStatus(ip, log):
    ssh_object = login_to_switch(ip, "Show interface status")
    if ssh_object == None:
        return None
    try:
        time.sleep(5)
        ssh_object.buffer = b""
        ssh_object.sendline("show interface status")
        time.sleep(20)
        ssh_object.prompt()
        output = ssh_object.before.decode("utf-8")
        print(output)
        with open(log, "a") as file:
            # Write output to the file
            file.write(output + "\n")
        if "Ethernet24" not in output:
            print("Switch interface not found, FAILED to CONFIG")
            return False
        return True
    except pxssh.ExceptionPxssh as e:
        print("Failed to run command")
        print(e)
        return None


def check_mux_firmware(ip, log, model):
    ssh_object = login_to_switch(ip, "Checking mux firmware version.")
    if ssh_object == None:
        return None
    try:
        selected_ports = None
        if model == "8.1lm":
            selected_ports = ycables_lm
        elif model == "8.1hh":
            selected_ports = ycable_hh
        else:
            print("msfpn not recognized")
            return None

        for eth in selected_ports:
            ssh_object.buffer = b""
            ssh_object.sendline("show mux firmware version {0}".format(eth))
            time.sleep(20)
            ssh_object.prompt()
            output = ssh_object.before.decode("utf-8")
            print(output)

            with open(log, "a") as file:
                # Write output to the file
                file.write(output + "\n")
            if 'version_nic_active": "N/A' in output:
                return 2
            if (
                '"version_nic_active": "1.4MW",' not in output
                or '"version_peer_active": "1.4MW",' not in output
            ):
                return 1
        return 0
    except pxssh.ExceptionPxssh as e:
        print("Failed to run command")
        print(e)
        return None


def check_fpga_firmware(ip, log):
    ssh_object = login_to_switch(ip, "Checking FPGA firmware version")
    if ssh_object == None:
        return None
    try:
        # for eth in g_mux_cable_7260_CX3:
        ssh_object.buffer = b""
        ssh_object.sendline("cat /proc/scd")
        time.sleep(5)
        ssh_object.prompt()
        output = ssh_object.before.decode("utf-8")

        with open(log, "a") as file:
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


def downgrade_fpga_firmware(ip, log):
    # WIP
    ssh_object = login_to_switch(ip, "downgrade fpga firmware")
    if ssh_object == None:
        return None
    try:
        ssh_object.buffer = b""
        ssh_object.sendline("cd /host")
        time.sleep(5)
        ssh_object.prompt()
        ssh_object.sendline(
            "sudo scp -o 'StrictHostKeyChecking no' -o UserKnownHostsFile=/dev/null root@10.0.3.254:/project/edward/*.deb ."
        )
        time.sleep(10)
        ssh_object.prompt()

        ssh_object.sendline("M1cr0$0ft")
        time.sleep(20)
        ssh_object.prompt()

        ssh_object.sendline("sudo dpkg -i libcrypt1_4.4.18-4_amd64.deb")
        time.sleep(25)
        ssh_object.prompt()

        ssh_object.sendline(
            "echo 'deb [arch=amd64] http://ftp.us.debian.org/debian sid main' | sudo tee -a /etc/apt/sources.list"
        )
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

        output = ssh_object.before.decode("utf-8")
        print(output)
        with open(log, "a") as file:
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


def post_downgrade_clean(ip, log):
    ssh_object = login_to_switch(ip, "Post downgrade cleaning")
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
        output = ssh_object.before.decode("utf-8")
        print(output)
        with open(log, "a") as file:
            # Write output to the file
            file.write(output + "\n")
        return 0
    except pxssh.ExceptionPxssh as e:
        print("Failed to run command")
        print(e)
        return None


async def run_y_cable_update(ip, log, model):
    # Establish SSH connection using asyncssh
    try:
        async with asyncssh.connect(
            ip, username="admin", password="Temp123!", known_hosts=None
        ) as ssh_session:
            print(f"Connected to {ip} for y-cable update")

            # Determine the correct command based on the msfpn
            if model == "8.1hh":
                command = "sudo bash -c 'python3 -u /host/FW_Update/mux_update_purple.py 8.1HH | tee -a /host/FW_Update/mux_update_purple.log'"
            elif model == "8.1lm":
                command = "sudo bash -c 'python3 -u /host/FW_Update/mux_update_purple.py 8.1LH | tee -a /host/FW_Update/mux_update_purple.log'"
            else:
                print("Unknown model")
                return None

            print(f"Running command: {command}")

            # Execute the command and handle long-running execution
            process = await ssh_session.create_process(command)
            output = ""

            # Stream the output in real-time as the command runs
            async for line in process.stdout:
                output += line
                print(line, end="")  # Print the output line by line
                with open(log, "a") as file:
                    file.write(line)  # Log the output

            # Wait for the command to complete
            await process.wait()

            # Check exit status
            if process.exit_status == 0:
                print(f"Y-cable update done successfully on {ip}")
                return 0
            else:
                print(f"Y-cable update failed on {ip}")
                return 1

    except asyncssh.Error as e:
        print(f"SSH connection failed: {e}")
        return None


def config_switch(sn_info, switch):
    log = "/RACKLOG/t6ub/RM_logs/{0}/TOR_{1}.log".format(
        sn_info["RACKSN"], "A" if switch == 0 else "B"
    )

    def log_exception(message, log_type="ERROR"):
        with open(log, "a") as file:
            file.write(f"{datetime.now()} - {log_type}: {message}\n")
        sendlog(message, color=RED, logfile=log)
        send_data_sf(
            time.strftime("%Y%m%d%H%M%S"),
            message,
            log_type,
            sn_info["sn"],
            sn_info["LOCATION"],
            sn_info["STATION"],
            log,
        )

    try:
        if switch == 0:
            print("Start switch config for TOR A!")
            ip = get_ip(sn_info["switch_a_mac"])
            tor = "A"
            mac = sn_info["switch_a_mac"]
        elif switch == 1:
            print("Start switch config for TOR B!")
            ip = get_ip(sn_info["switch_b_mac"])
            tor = "B"
            mac = sn_info["switch_b_mac"]

        if sn_info["MSFPN"] in current_8_point_1_hh:
            model = "8.1hh"
        elif sn_info["MSFPN"] in current_8_point_1_lm:
            model = "8.1lm"
        else:
            raise ValueError(f"Unknown SKU: {sn_info['MSFPN']}")

        if ip == 1:
            raise ConnectionError(f"Could not get switch {switch} IP")

        print(getresult("ssh-keygen -f '/root/.ssh/known_hosts' -R '{0}'".format(ip)))

        # Check if the switch has been configured
        has_been_config = check_switch_os_version(ip, log)
        if has_been_config is None:
            raise RuntimeError(f"Failed to check switch OS version for {ip}")

        print("Transferring tftp /switch_automation to /host/FW_Update/")
        if send_cmd_to_switch(ip, log, "sudo mkdir -p /host/FW_Update") is None:
            raise RuntimeError("Failed to create /host/FW_Update dir")

        if send_file_to_switch(ip, log) is None:
            raise RuntimeError("Failed to get switch update files")

        if has_been_config == 1:
            if update_switch_os(ip, log) is None:
                raise RuntimeError("Failed to update switch OS")
            print(
                getresult("ssh-keygen -f '/root/.ssh/known_hosts' -R '{0}'".format(ip))
            )
            has_been_config = check_switch_os_version(ip, log)
            if has_been_config != 0:
                raise RuntimeError("OS upgrade failed!")

        # Checking if switch FPGA is in correct version, downgrade if it not
        # if checkInterfaceStatus(ip,log) == False:
        # if check_fpga_firmware(ip,log) == 1:
        #     if downgrade_fpga_firmware(ip,log) == 1:
        #         print("Failed to downgrade switch fpga FW")
        #         log_type="WARNING"
        #         message = "TOR-SWITCH-{0}-FPGA-FW-DOWNGRADE-UNSUCCESSFUL".format(tor)
        #         start_time=time.strftime("%Y%m%d%H%M%S")
        #         log_file =""
        #         send_data_sf(start_time,message, log_type, sn_info["sn"], sn_info["LOCATION"], sn_info["STATION"], log_file)
        #         return 1
        #     time.sleep(120)
        #     if check_fpga_firmware(ip,log) == 1:
        #         print("Failed to downgrade switch fpga FW")
        #         log_type="WARNING"
        #         message = "TOR-SWITCH-{0}-FPGA-FW-DOWNGRADE-UNSUCCESSFUL".format(tor)
        #         start_time=time.strftime("%Y%m%d%H%M%S")
        #         log_file =""
        #         send_data_sf(start_time,message, log_type, sn_info["sn"], sn_info["LOCATION"], sn_info["STATION"], log_file)
        #         return 1
        #     time.sleep(5)
        #     if post_downgrade_clean(ip,log) == 1:
        #         print("Failed to clean switch after downgrade")
        #         log_type="WARNING"
        #         message = "TOR-SWITCH-{0}-POST-DOWNGRADE-UNSUCCESSFUL".format(tor)
        #         start_time=time.strftime("%Y%m%d%H%M%S")
        #         log_file =""
        #         send_data_sf(start_time,message, log_type, sn_info["sn"], sn_info["LOCATION"], sn_info["STATION"], log_file)
        #         return 1

        # Configure the switch but not bringing uplink ports online for ycable updates
        if run_SW_Config(ip, log, model, False) is None:
            raise RuntimeError("Failed to configure the switch - no uplink")

        print("DONE CONFIGURING THE SWITCH:", switch)
        print("Copy Mux FW to /usr/share/sonic/firmware")

        if (
            send_cmd_to_switch(
                ip,
                log,
                "sudo cp /host/FW_Update/AEC_WYOMING_MW_1.4_20220907.bin /usr/share/sonic/firmware/",
            )
            is None
        ):
            raise RuntimeError(
                "Failed to copy AEC firmware file to /usr/share/sonic/firmware/"
            )

        if send_mux_firmware_to_switch(ip, log) is None:
            raise RuntimeError(
                "Failed to transfer AEC firmware to /usr/share/sonic/firmware/"
            )

        # Start y-cable update - do it once
        if switch == 1:
            print("Start to do y-cable updates!")
            if asyncio.run(run_y_cable_update(ip, log, model)) is None:
                raise RuntimeError("Y-cable update failed!")

            time.sleep(1)

            # BRINGING UPLINK
            print("Start to bring uplink up for TOR A")
            if (
                run_SW_Config(
                    get_ip(sn_info["switch_a_mac"]),
                    "/RACKLOG/t6ub/RM_logs/{0}/TOR_{1}.log".format(
                        sn_info["RACKSN"], tor
                    ),
                    model,
                    True,
                )
                is None
            ):
                raise RuntimeError(
                    "Failed to configure the switch with uplinks enabled."
                )

            print("Start to bring uplink up for TOR B")
            if run_SW_Config(ip, log, model, True) is None:
                raise RuntimeError(
                    "Failed to configure the switch with uplinks enabled."
                )

        print(f"Switch config for {mac}:{ip} complete")
        with open(log, "a") as file:
            file.write(f"Switch config for {mac}:{ip} complete\n")

        if os.path.isfile("/host/FW_Update/Y-CABLE-UPDATE-ERROR-PORT.finished"):
            with open(
                "/host/FW_Update/Y-CABLE-UPDATE-ERROR-PORT.finished", "r"
            ) as error_file:
                send_data_sf(
                    time.strftime("%Y%m%d%H%M%S"),
                    "Please check these error ports: " + error_file.read(),
                    "WARNING",
                    sn_info["sn"],
                    sn_info["LOCATION"],
                    sn_info["STATION"],
                    "",
                )
        return 0

    except Exception as e:
        error_message = f"Exception in config_switch for TOR {tor}: {str(e)}"
        log_exception(error_message)
        return 1


def check_error_port_file(file_path):
    """
    Opens the specified error-port file and checks if it is not empty.

    Parameters:
    - file_path (str): The path to the error-port file.

    Returns:
    - bool: True if the file is not empty, False otherwise.
    """
    try:
        with open(file_path, "r") as file:
            contents = file.read().strip()
            return contents
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return True
    except Exception as e:
        print(f"An error occurred while checking the file: {e}")
        return False


def create_flag(sn_info):
    with lock:
        # Create the updating flag
        updating_flag_path = g_log_folder + "/{0}/{1}.txt".format(
            sn_info["RACKSN"], "Updating"
        )
        with open(updating_flag_path, "w") as file:
            file.write("updating...")

        # Ensure the log directory exists
        log_dir = "/RACKLOG/{0}/RM_logs/{1}/".format(g_racklog_t6ub, sn_info["sn"])
        os.makedirs(log_dir, exist_ok=True)

        # Create the log file for the update
        with open("{0}/{1}_updating.log".format(log_dir, sn_info["sn"]), "w") as file:
            file.write("updating...")


def auto_config_switches(sn_info):
    if get_ip(sn_info["RM"]) == 1:
        print("Rack Not on Line")
        return 1
    else:
        # create updating flag
        create_flag(sn_info)
        # perform PSU update for rack
        asyncio.run(update_psu_1717_to_1818(get_ip(sn_info["RM"])))
        print("done updating 1717 to 1818 PSU FW")

    updating_flag_path = g_log_folder + "/{0}/{1}.txt".format(
        sn_info["RACKSN"], "Updating"
    )

    # Update switch A
    log_type = "START"
    message = "START-SWITCH-A-UPDATE-AND-CONFIG"
    start_time = time.strftime("%Y%m%d%H%M%S")
    log_file = ""
    send_data_sf(
        start_time,
        message,
        log_type,
        sn_info["sn"],
        sn_info["LOCATION"],
        sn_info["STATION"],
        log_file,
    )

    resultA = config_switch(sn_info, 0)

    if resultA == 1:
        print("Switch A configuration not success!. Sleep 60s.")
        time.sleep(60)

    log_type = "START"
    message = "START-SWITCH-B-UPDATE-AND-CONFIG"
    start_time = time.strftime("%Y%m%d%H%M%S")
    log_file = ""
    send_data_sf(
        start_time,
        message,
        log_type,
        sn_info["sn"],
        sn_info["LOCATION"],
        sn_info["STATION"],
        log_file,
    )

    resultB = config_switch(sn_info, 1)

    print("Switch A result:{0}".format(resultA))
    print("Switch B result:{0}".format(resultB))

    # Lock the critical section for file updates
    with lock:
        if resultA == 1 or resultB == 1:
            print("Switch Auto Config failed for {0}!".format(sn_info["RACKSN"]))
            print("Deleting updating flag...")
            if os.path.exists(updating_flag_path):
                os.remove(updating_flag_path)
            return 1

        # Remove the updating flag
        if os.path.exists(updating_flag_path):
            os.remove(updating_flag_path)

        print("Creating switch update complete flag")
        finish_flag = g_log_folder + "/{0}/{0}.txt".format(sn_info["RACKSN"])
        with open(finish_flag, "w") as file:
            file.write("done")

        log_type = "FINISH"
        message = "SWITCH-UPDATE-AND-CONFIG-FINISHED"
        start_time = time.strftime("%Y%m%d%H%M%S")
        log_file = ""
        send_data_sf(
            start_time,
            message,
            log_type,
            sn_info["sn"],
            sn_info["LOCATION"],
            sn_info["STATION"],
            log_file,
        )

        # Remove the temporary updating log if it exists
        updating_log_path = "/RACKLOG/t6ub/RM_logs/{0}/{0}_updating.log".format(
            sn_info["sn"]
        )
        if os.path.exists(updating_log_path):
            os.remove(updating_log_path)

    return 0


def main():
    print(current_date.date())
    switch_configs = get_switch_configs()
    threads = []

    if not switch_configs:
        sys.exit(4)

    for conf in switch_configs:
        print(conf)
        if not is_config(conf):
            print("Not config")
            t = Thread(target=auto_config_switches, args=(conf,))
            t.start()
            threads.append(t)
            time.sleep(5)  # Slight delay between starting threads
        else:
            print("Is config")

    # Wait for all threads to complete
    for t in threads:
        t.join()
        print("Thread finished")

    print("All tasks completed")


if __name__ == "__main__":
    main()
    print("Done")
