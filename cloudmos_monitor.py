import os
import subprocess
import yaml

FLAG_DIR="/RACKLOG/CLOUDMOS"
PXE_IP="10.0.3.254"
SSH_FLAG_DIR="/RACKLOG/SSH"

if not os.path.isdir(SSH_FLAG_DIR):
    os.mkdir(SSH_FLAG_DIR)

for i in os.listdir(SSH_FLAG_DIR):
    with open(f"{SSH_FLAG_DIR}/{i}", 'r') as f:
        data = yaml.safe_load(f)
    if data:
        print(data)
        cmd = f"sshpass -p '{data['pwd']}' ssh -o 'StrictHostKeyChecking no' -o 'UserKnownHostsFile /dev/null' {data['usr']}@{data['ip']} '{data['cmd']}'"
        print("cmd="+cmd)
        os.system(cmd)
        os.remove(f"{SSH_FLAG_DIR}/{i}")

if not os.path.isdir(FLAG_DIR):
    os.mkdir(FLAG_DIR)

for i in os.listdir(FLAG_DIR):
    print("MAC=")
    print(i)
    uut_ip=""
    mac=i.replace("-","")
    try:
        uut_ip=subprocess.Popen( f"/usr/local/bin/find_ip {mac}", stdout = subprocess.PIPE, shell=True, encoding='utf-8').communicate()[0].strip()
    except Exception as e:
        print(e)
    print("uut_ip=")
    print(uut_ip)
    cmd = f"sshpass -p 'msft' ssh -o 'StrictHostKeyChecking no' -o 'UserKnownHostsFile /dev/null' root@{uut_ip} 'echo {PXE_IP} > X:\\Windows\\PXE_IP'"
    print("cmd=")
    print(cmd)
    os.system(cmd)
    model = subprocess.Popen( f"cat {i}", stdout = subprocess.PIPE, shell=True, encoding='utf-8').communicate()[0].strip()

    with open(f"{FLAG_DIR}/{i}", 'r') as f:
        data = yaml.safe_load(f)
    if data:
        for key, value in data.items():
            cmd = f"sshpass -p 'msft' ssh -o 'StrictHostKeyChecking no' -o 'UserKnownHostsFile /dev/null' root@{uut_ip} 'echo {value} > X:\\Windows\\{key}'"
            print("cmd="+cmd)
            os.system(cmd)
        
