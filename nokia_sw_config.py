import os
import subprocess
import time


g_cmd_ping = "ping -c 3 {0}"

g_switch_passwords = ["password","Temp123!"]

def sendlog(message = "",logfile=""):
    if logfile != "":
        cmd = ("echo '{0} ====>> {1}' >>{2}".format(time.strftime("%m-%d-%y-%H:%M:%S"), message, logfile))
        os.system(cmd)

def getresult(arg1):
    p = subprocess.Popen(arg1, stdout=subprocess.PIPE, shell=True,encoding="utf-8")
    (text, err) = p.communicate()
    res = text
    return res

def send_data_sf(message):
    st_file = "/host/FW_Update/status.txt"
    cmd = "echo '{0}' > {1}".format(message, st_file)
    os.system(cmd)

def connect_to_switch(serial_port, baudrate=9600, timeout=1):
    """
    Connect to the network switch via a serial connection.
    
    :param serial_port: The serial port to connect to (e.g., 'COM3' or '/dev/ttyUSB0').
    :param baudrate: The baud rate for the connection (default: 9600).
    :param timeout: Read timeout in seconds (default: 1).
    :return: Serial connection object.
    """
    try:
        ser = serial.Serial(port=serial_port, baudrate=baudrate, timeout=timeout)
        if ser.is_open:
           print(f"Connected to {serial_port} at {baudrate} baud.")
        username = "admin"
        password = "password"
        # Wait for login prompt
        time.sleep(10)

        ser.write(("\n").encode())

        time.sleep(35)  # You might need to adjust the sleep time to match your device's prompt timing

        # Send the username (assuming it is requested first)
        ser.write((username + '\n').encode())  # Send username and a newline

        # Wait for password prompt
        time.sleep(5)  # Adjust based on your device's prompt time

        # Send the password (assuming it is requested after username)
        ser.write((password + '\n').encode())  # Send password and a newline

        # Wait for successful login or command prompt
        time.sleep(15)
        response = ser.read_all().decode('utf-8', errors='ignore')
        print(response)

        # Send the command after logging in
        return ser
    except Exception as e:
        print(f"Failed to connect to {serial_port}: {e}")
        return None

def send_command(ser, command, sleep=10):
    """
    Send a command to the switch and read the response.
    
    :param ser: Serial connection object.
    :param command: Command to send (string).
    :return: Response from the switch (string).
    """
    try:
        # Send the command followed by a newline or carriage return
        ser.write(f"{command} \n".encode())
        time.sleep(sleep)  # Allow time for the response
        response = ser.read_all().decode('utf-8', errors='ignore')  # Read all available data
        return response
    except Exception as e:
        print(f"Error sending command: {e}")
        return None

def check_version(ser,log):
    command = "show version"
    print(f"Sending command: {command}")
        
    response = send_command(ser, command, sleep=60)
    sendlog(f"Sending command: {command}",log)
    sendlog(response,log)
    print(response)

    if "SONiC.20220531.34" not in response:
        return False
    else:
        return True

def check_config(ser,log):
    print("Checking switch config")
    command = g_cmd_ping.format("172.16.0.1")
    response = send_command(ser, command, 5)
    sendlog(f"Sending command: {command}",log)
    sendlog(response,log)
    print(response)
    if "0% packet loss" not in response:
        print("Switch not configured")
        sendlog("Switch not configured",log)
        return False
    else:
        print("Switch configured")
        sendlog("Switch configured",log)
        return True

def send_config_json(ser,log):
    command = "sudo rm /host/FW_Update/config_nokia.json"
    response = send_command(ser, command, 1)
    print(response)

    with open("/host/FW_Update/config_db_nokia.json", "r") as f: 
        for line in f:
            line = line.replace('\n', '')
            command = f"echo '{line}' >> /host/FW_Update/config_nokia.json"
            print(f"Sending command: {command}")
            sendlog(f"Sending command: {command}",log)
            response = send_command(ser, command, 1)

            if response:
                sendlog(response,log)
                print("Response from switch:")
                print(response)

def config_nokia(ser, log):
    command = "sudo sed -i 's/^enabled=true$/enabled=false/' /etc/sonic/updategraph.conf"
    print(f"Sending command: {command}")
    sendlog(f"Sending command: {command}",log)
    response = send_command(ser, command, sleep=4)

    if response:
        sendlog(response,log)
        print("Response from switch:")
        print(response)

    send_config_json(ser,log)

    command = "sudo cp /etc/sonic/config_db.json /etc/sonic/config_db_backup.json "
    print(f"Sending command: {command}")
    sendlog(f"Sending command: {command}",log)
    response = send_command(ser, command, sleep=5)

    command = "sudo cp /host/FW_Update/config_nokia.json /etc/sonic/config_db.json "
    print(f"Sending command: {command}")
    sendlog(f"Sending command: {command}",log)
    response = send_command(ser, command, sleep=5)

    command = "sudo config reload –y"
    print(f"Sending command: {command}")
    sendlog(f"Sending command: {command}",log)
    response = send_command(ser, command, sleep=15)
    print(response)
    sendlog(response,log)

    command = "yes"
    print(f"Sending command:{command}")
    response = send_command(ser,command,sleep=85)
    print(response)
    sendlog(response,log)

    command = "sudo reboot"
    print(f"Sending command: {command}")
    sendlog(f"Sending command: {command}",log)
    response = send_command(ser, command, sleep=160)
    print(response)
    sendlog(response,log)

def update_sonic(ser,log):
    command = "sudo scp admin@172.16.0.1:/host/FW_Update/*.bin /host/FW_Update/"
    print(f"Sending command: {command}")
    sendlog(f"Sending command: {command}",log)
    response = send_command(ser, command, sleep=20)
    print(response)
    sendlog(response,log)

    response = send_command(ser,"yes",sleep=10)
    print(response)
    sendlog(response,log)
    response = send_command(ser,"Temp123!", sleep=120)
    print(response)
    sendlog(response,log)


    command = "sudo sonic-installer install /host/FW_Update/sonic-marvell-armhf-20220531.34.bin -y"
    print(f"Sending command: {command}")
    sendlog(f"Sending command: {command}",log)
    response = send_command(ser, command, sleep=300)
    print(response)
    sendlog(response,log)

    #command = "yes"
    #print(f"Sending command: {command}")
    #sendlog(f"Sending command: {command}",log)
    #response = send_command(ser, command, sleep=500)
    #print(response)
    #sendlog(response,log)

    command = "sudo reboot"
    print(f"Sending command: {command}")
    sendlog(f"Sending command: {command}",log)
    response = send_command(ser, command, sleep=300)
    print(response)
    sendlog(response,log)
    
def main(serial_port):

    #os.system("sudo touch /host/FW_Update/nokia_updating.txt")

    # Update with your serial port
    baudrate = 9600  # Default baud rate for many switches (check your device's manual)
    logfile = "/host/FW_Update/nokia_config.log"
    # Connect to the switch
    ser = connect_to_switch(serial_port, baudrate)
 
    if ser:
     #   mac = get_mac(ser)
        if not check_version(ser,logfile):
            print("Start NOKIA switch config and update")
            command = "sudo mkdir /host/FW_Update"
            print(f"Sending command: {command}")

            response = send_command(ser, command, sleep=2)
            sendlog(f"Sending command: {command}",logfile)
            sendlog(response,logfile)

            command = "sudo chmod 777 /host/FW_Update"
            print(f"Sending command: {command}")
            response = send_command(ser, command, sleep=2)
            sendlog(f"Sending command: {command}",logfile)
            sendlog(response,logfile)

            config_nokia(ser,logfile)
            
            time.sleep(30)
            ser.close()


            ser = connect_to_switch(serial_port, baudrate)

            if not check_config:
                send_data_sf("Nokia switch failed config")
                os.system("sudo rm /host/FW_Update/nokia_updating.txt")
                return 1
                
            update_sonic(ser,logfile)
            
            ser.close()
            time.sleep(10)
            ser = connect_to_switch(serial_port, baudrate)

            if not check_version(ser,logfile):
                sendlog("Nokia switch OS update failed",logfile)
                send_data_sf("Nokia switch OS update failed")
                os.system("sudo rm /host/FW_Update/nokia_updating.txt")
                return 1

            command = "echo admin:$(LANG=C perl -e '{0}') | sudo chpasswd -e".format('print crypt("Temp123!", "salt"),"\n"')
            print(f"Sending command: {command}")
            response = send_command(ser, command, sleep=2)
            sendlog(f"Sending command: {command}",logfile)

            os.system("ssh-keygen -f '/home/admin/.ssh/known_hosts' -R '172.16.0.5'")
            sendlog("Nokia switch update and config finish",logfile)
            os.system("sudo touch /host/FW_Update/nokia.finished")
            os.system("sudo rm /host/FW_Update/nokia_updating.txt")
        else:
            print("Nokia switch OS already updated, checking config")
            if not check_config:
                config_nokia(ser,logfile)
                if not check_config:
                    send_data_sf("Nokia switch failed config")
                    os.system("sudo rm /host/FW_Update/nokia_updating.txt")
                    return 1
                else:
                    sendlog("Nokia switch update and config finish",logfile)
            else:
                sendlog("Nokia switch already finish config and update",logfile)
        #Close the connection
        ser.close()
        print("Connection closed.")
        send_data_sf("Nokia switch update and config finish")
        os.system("sudo touch /host/FW_Update/nokia.finished")
    else:
        print("Check serial cable connection!")
        send_data_sf("Check serial cable connection")
        return 1
    return 0

if __name__ == "__main__":
    os.system("pip3 install pyserial")

    import serial
    serial_port = "/dev/ttyUSB0"
    os.system("sudo chmod 777 {0}".format(serial_port))
    if not os.path.exists("/host/FW_Update/nokia.finished") and not os.path.exists("/host/FW_Update/nokia_updating.txt"):
        main(serial_port)
    else:
        print("Switch already configured")
    print("done")

