import os
import subprocess

class RM_REDFISH():
    
    def __init__(self,rack_id, rack_ip):
        request_type = "GET"
        self.rack_id = rack_id
        self.rack_ip = rack_ip
        self.number = "unknow"
        self.cmd_root = "curl -k -u 'root':'$pl3nd1D' -X {0} ".format(request_type)
        self.url = "https://{0}".format(self.rack_ip)
        self.url_uut_id ="/{0}".format(self.rack_id) 
        self.rack_endpoint = { "manager_info" : "/redfish/v1/Managers/RackManager",
                 "manager_ethernet": "/redfish/v1/Managers/RackManager/EthernetInterfaces/eth{0}".format(self.number),
                 "manager_tftp": "/redfish/v1/Managers/RackManager/Tftp",
                 "manager_inventory": "/Redfish/v1/Chassis/Rack/Inventory",
                 "manager_cpld" : "/redfish/v1/Chassis/RackManager/CPLD"}
        self.uut_endpoint = {"system_info" : "/redfish/v1/System",
                             "system_bios_code" : "/redfish/v1/System/BiosCode",
                             "system_cerberus" : "/redfish/v1/System/Cerberus/1"}

    
    def getresult(self,arg1):
        p = subprocess.Popen(arg1, stdout=subprocess.PIPE, shell=True, text=True)
        (text, err) = p.communicate()
        return text 
        
    def rm_menu():
        actions = [
        "RackManager Info",
        "RackManager Tftp List",
        "RackManager Inventory",
        "RackManager CPLD",
        "RackManager_CLI_Input",
        "System Info",
        "System Bios Code",
        "System Cerberus",
        "System Fru"
        ]
        #Set the midpoint at 9 since there's only 17 actions, if mid//2 = 8
        mid = 5
        left_column = actions[:mid]  # First 9 actions
        right_column = actions[mid:]  # Actions 10-17
        max_index_left = len(str(mid))
        max_index_right = len(str(len(actions)))
        for i in range(mid):
            left_item = f"{i+1:>{max_index_left}}. {left_column[i]:<45}"
            right_item = f"{i+1+mid:>{max_index_right}}. {right_column[i]}" if i < len(right_column) else ""
            print(f"{left_item} {right_item}")
    def rm_query(self,endpoint,type_request):
        cmd = self.cmd_root.format(type_request) + self.url + self.rack_endpoint[endpoint]
        print(cmd)
        result = self.getresult(cmd)
        print(result)
    def rm_sys_query(self,endpoint):
        cmd = self.cmd_root + self.url + self.url_uut_id + self.uut_endpoint[endpoint]
        print(cmd)
        result = self.getresult(cmd)
        print(result)
    def rm_cli_cmd(self,user_cmd):
        cmd = f"sshpass -f /etc/rtp/rm_passwd ssh -o StrictHostKeyChecking=no root@{self.rack_ip}"
        rmcmd = "{ "
        rmcmd += f'echo "{user_cmd} -i {self.rack_id}";'
        rmcmd += " }"
        final_cmd = rmcmd + '|' + cmd
        print(f"Executing:{final_cmd}")
        os.system(final_cmd)
        
