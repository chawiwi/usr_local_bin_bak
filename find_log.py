#!/usr/bin/env python3

import os
import subprocess
from datetime import datetime
from colorama import Fore 

LOG_PATH="/RACKLOG/quanta/"
OOB_PATH="/RACKLOG/OOB/"

class log_search():
    def show_logs(dirs,time):
        data=list(zip(dirs,time))
        data_sorted=sorted(data, key=lambda x: x[1])
        max_len = max([len(d) for d, t in data])
        print("-------------------RESULT------------------------------")
        for d, t in data_sorted:
            print(Fore.YELLOW + f"{d.ljust(max_len)}  {t}"+ Fore.WHITE)
    def find_sn(lists_sn):
        for each in lists_sn:
            list_time,list_dir=[],[]
            pattern =f"*{each[-10:]}*"
            result=subprocess.Popen(['find',LOG_PATH,OOB_PATH,'-type','f','-iname',pattern],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            output=result.communicate()
            string = output[0].decode('utf-8')
            list_str=string.split('\n')
            if len(list_str) > 1:
                for j in list_str:
                    if j :
                        time = os.path.getmtime(j)
                        mod_time=datetime.fromtimestamp(time)
                        formatted_timestamp = mod_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-7]
                        list_dir.append(j)
                        list_time.append(formatted_timestamp)
                log_search.show_logs(list_dir,list_time)
            else:
                print("-------------------Warning------------------------------")
                print(f"No Logs Found For '{each}'")
                print("--------------------------------------------------------")
                continue
if __name__ == '__main__':
        	
        inputs = []
        sn = input("Please enter sn that you want to search log:\n").strip().lower()
        while len(sn) != 0:
            inputs.append(sn)
            sn=input().strip().lower()
        log_search.find_sn(inputs)
    

  	
