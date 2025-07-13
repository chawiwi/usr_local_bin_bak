#!/usr/bin/python3.6
import sys
import zeep
import time
import datetime
import os
import subprocess
import json
import csv
import shutil
import hashlib
import threading
from zeep import Client
from pathlib import Path
UUT_Flag="/tmp/api_mode" #DM this will allow us to differentiate if UUT is communicating directly with SF through API or via handshake function, based on each device environment (UUT or Controller Device Environment)
if os.path.isfile(UUT_Flag):
	Executing_Device="UUT"
else:
	Executing_Device="CONTROLLER"
URL_List = [] #DM create list for API URL or URLs
API_Inventory_File="/usr/local/bin/API_L10.csv" #DM This file contains site-specific information for controller mode only, currently it contains the API URL
Rack_List = "/home/sudo_free_execution/Rack_List.txt"
Temp_Dir = "/home/job_reports/"
if Executing_Device == "UUT" and os.path.isfile("/tmp/api_direct"): #If UUT is executing API_Relay.py and should be using direct mode (flag created by startup when API URL is maintained as boot parameter)
	Temp_Dir = "/tmp/"
	q = subprocess.Popen('cat /proc/cmdline | tr " " "\n"', stdout=subprocess.PIPE, shell=True)
	for line in q.stdout:
		line2 = line.strip().decode('UTF-8')
		if "api_mode" in line2.lower():
			Defined_API_URLS = line2.split('=')[1]
			if ";" in Defined_API_URLS:
				API_URLS = Defined_API_URLS.split(";")
			else:
				URL_List.append(Defined_API_URLS)
				API_URLS = URL_List
else:
	API_URLS = ['http://192.168.66.20/AMA_L10/AMAService.svc?singleWsdl']
def print_red(print_item): #to print in red font
	if API_Action_Lower == "--help" or API_Action_Lower == "-?":
		print('\x1b[1;31;40m{0}\x1b[0m'.format(print_item),flush=True)
	else:
		Curr_Time = time.strftime("%m-%d-%y-%H:%M:%S")
		print('\x1b[1;31;40m{0} - {1}\x1b[0m'.format(Curr_Time,print_item),flush=True)
def print_yellow(print_item): #to print in yellow font
	if API_Action_Lower == "--help" or API_Action_Lower == "-?":
		print('\x1b[1;33;40m{0}\x1b[0m'.format(print_item),flush=True)
	else:
		Curr_Time = time.strftime("%m-%d-%y-%H:%M:%S")
		print('\x1b[1;33;40m{0} - {1}\x1b[0m'.format(Curr_Time,print_item),flush=True)
def print_white(print_item): #to print in white font
	if API_Action_Lower == "--help" or API_Action_Lower == "-?":
		print('\x1b[1;37;40m{0}\x1b[0m'.format(print_item),flush=True)
	else:
		Curr_Time = time.strftime("%m-%d-%y-%H:%M:%S")
		print('\x1b[1;37;40m{0} - {1}\x1b[0m'.format(Curr_Time,print_item),flush=True)
def print_pink(print_item):  #to print in pink font
	if API_Action_Lower == "--help" or API_Action_Lower == "-?":
		print('\x1b[0;35;40m{0}\x1b[0m'.format(print_item),flush=True)
	else:
		Curr_Time = time.strftime("%m-%d-%y-%H:%M:%S")
		print('\x1b[0;35;40m{0} - {1}\x1b[0m'.format(Curr_Time,print_item),flush=True)
def print_teal(print_item):  #to print in teal font
	if API_Action_Lower == "--help" or API_Action_Lower == "-?":
		print('\x1b[1;36;40m{0}\x1b[0m'.format(print_item),flush=True)
	else:
		Curr_Time = time.strftime("%m-%d-%y-%H:%M:%S")
		print('\x1b[1;36;40m{0} - {1}\x1b[0m'.format(Curr_Time,print_item),flush=True)
def md5(fname): #function to check md5sum of provided argument, used in handshake mode to check if this script has been modified and if modification has been done, it will exit the iteration to restart with updates
	hash_md5 = hashlib.md5()
	with open(fname, "rb") as f:
		for chunk in iter(lambda: f.read(4096), b""):
			hash_md5.update(chunk)
	return hash_md5.hexdigest()
def RLT_File(Rack_SN): #Function meant to query Rack level data from SF
	RLT_File = "{0}{1}.txt".format(Temp_Dir,Rack_SN)
	if os.path.isfile(RLT_File): #Delete existing file if exists
		os.system("rm -rf {0}".format(RLT_File))
	print_white("Requesting RLT File for Rack SN: {0}".format(Rack_SN))
	for API_URL in API_URLS:
		API_Station = "QUERY"
		API_Type = "RLT"
		client = Client(API_URL)
		res = client.service.SendRequest(API_Station,Rack_SN,API_Type)
		f = open(RLT_File, 'w')
		data = client.get_type('ns1:ArrayOfConfigCollection')()
		parameter_list= (res['Assets'])
		if (res['Msg'] == "OK"):
			configs =  parameter_list['Asset']
			for item in configs:
				for key in item: #DM to avoid a parsing issue, replace nonexisting items with blank items
					if item[key] == None:
						item[key] = ""
				try:
					final_line = item['Type']+","+item['Serial']+","+item['PartNumber']+","+item['Asset']+","+item['Position'].replace("A","")+","+item['ETH0MAC']+","+item['ETH1MAC']+","+item['TestPosition']+","+item['PositionSub']
					f.write(final_line+'\n')
				except:
					print_red(key, ' : ', item[key])
					print_red("Issue detected during Type {0} Check".format(item['Type']))
					print_red("Item:{0}".format(item))
					print_red("Info sent to Shop Floor:")
					print_red("API Function:SendRequest")
					print_red("Station:{0}".format(API_Station))
					print_red("UUID:{0}".format(Rack_SN))
					print_red("Type:{0}".format(API_Type))
					if API_URLS[-1] != API_URL:
						print_yellow("Query over API URL {0} has failed, retrying with URL {1} from API URL List: {2}".format(API_URL,API_URLS[-1],API_URLS))
						continue
					if API_Action_Lower != "handshake":
						sys.exit(1)
		f.close()
		os.system("chmod -R 777 {0}".format(RLT_File))
		return RLT_File
def Send2sf_Function(send2sf_sn,send2sf_message,send2sf_status,send2sf_station,send2sf_racksn): #Function meant to send UUT status to SF
	starttime= "2018-05-24 04:17:25"
	error=""
	failure=""
	action=""
	asset=""
	message_for_csv=send2sf_message.replace(",",";") #DM modify message to ignore comma in message to have correct csv fields
	Wiki_Error_Parser = "/home/project/TE_tools/tools/sf_msg_transform_AMA.py" #Wiki error parser which translates an error into a expected wiki page, currently not used until the best implementation method has been found
	send2sf_status = send2sf_status.upper() #DM Translate status to upper, For example: FaIl -> FAIL, to make it easier for Shop Floor, Reports and everyone viewing test status
	if send2sf_status != "PASS" and send2sf_status != "WARNING" and send2sf_status != "FAIL" and send2sf_status != "START": #DM only START,PASS and FAIL are stored in Database, everything else will be NA, hence add status: before message to convey proper status
		send2sf_message = "{0}:{1}".format(send2sf_status,send2sf_message)
	for API_URL in API_URLS:
		client = Client(API_URL)
		ans = client.get_type('ns1:StatusCollection')()
		start = datetime.datetime.strptime(starttime,"%Y-%m-%d %H:%M:%S")
		start = start.replace(tzinfo=datetime.timezone.utc).replace(microsecond=0).isoformat()
		end = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).replace(microsecond=0).isoformat() #DM send in UTC Time
		start = end
		log_time=str(datetime.datetime.utcnow()) #Time for logging purposes only
		log_time=log_time.split(' ')[0] #Time for logging purposes only
		# fill the request structure
		ans.Station = send2sf_station.strip()
		ans.RackAsset = send2sf_racksn
		ans.AssetNumber = ""
		ans.SerialNumber = send2sf_sn.strip()
		ans.TestStatus = send2sf_status.strip()
		ans.ErrorDesc = send2sf_message.strip()
		ans.TestEndTime = datetime.datetime.strptime(end, "%Y-%m-%dT%H:%M:%S+00:00")
		ans.TestStartTime = datetime.datetime.strptime(start, "%Y-%m-%dT%H:%M:%S+00:00")
		ans.ErrorCode = error.strip()
		ans.FailureAnalysis = failure.strip()
		ans.CorrectiveAction = action.strip()
		# if send2sf_status == "FAIL" or send2sf_status == "WARNING":
			# Wiki_debug_page = subprocess.check_output("{0} '{1}'".format(Wiki_Error_Parser,send2sf_message), shell = True).rstrip().decode('UTF-8').split('^')[1]
			# Wiki_debug_page = "https://qdg.quantade.com/index.php/{0}".format(Wiki_debug_page)
			# ans.CorrectiveAction = Wiki_debug_page.strip() #DM CA to contain wiki page? Perhaps we can use this in the future
			# print ("Wiki_debug_page="+Wiki_debug_page)
		# else:
			# ans.CorrectiveAction = action.strip()
		print_white("Sending Status to Shop Floor: SN {0}, Message: {1}, {2} in Station: {3}".format(send2sf_sn,send2sf_message,send2sf_status,send2sf_station))
		if Executing_Device == "UUT": #UUT will store status report here
			Temp_Dir="/win/Serverinfo/"
		else:
			Temp_Dir = "/home/job_reports/" #Controller will store status report here
		Status_Report = "{0}Status_List_{1}.csv".format(Temp_Dir,log_time)
		if not os.path.isfile(Status_Report): #If Status report does not exist, create header
			os.system("echo 'Timestamp,Platform,Model,Rack Serial Number,UUT Serial,Message,Status,Station' > {0}".format(Status_Report)) #add header to report
		send2sf_platform = ""
		send2sf_model = ""
		if Executing_Device == "UUT":
			UUT_SFC_File = "/test/{0}.txt".format(send2sf_sn) #DM check if SFC File exists to get Platform and Model from SFC File
		else:
			UUT_SFC_File = "{0}{1}.txt".format(Temp_Dir,send2sf_sn) #DM check if SFC File exists to get Platform and Model from SFC File
		if send2sf_sn != "": #get Platform(A5W_PY) and Model(TETRA01) for Status report
			if not os.path.isfile(UUT_SFC_File):
				Query_SF_File(send2sf_sn)
			with open(UUT_SFC_File) as Line_Reader:
				for line in Line_Reader:
					if "MODEL" in line.upper():
						send2sf_platform = line.split('=')[1].strip() #get Platform of UUT for which a Status will be sent to Shop Floor
					if "PARTN" in line.upper():
						send2sf_model = line.split('=')[1].strip() #get Platform of UUT for which a Status will be sent to Shop Floor
			Line_Reader.close()
		os.system("echo '{0},{1},{2},{3},{4},{5},{6},{7}' >> {8}".format(datetime.datetime.utcnow(),send2sf_platform,send2sf_model,send2sf_sn,send2sf_racksn,message_for_csv,send2sf_status,send2sf_station,Status_Report)) #Write status to status report
		client = Client(API_URL)
		ans_cont = client.get_type('ns0:ArrayOfStatusCollection')()
		ans_cont['StatusCollection'].append(ans)
		res = client.service.SaveStatus(ans_cont) #send info to SF
		if (res['Msg'] != "OK"):
			print_red("Status failed,details below:")
			print(res)
			print_red("Info sent to Shop Floor:")
			print_red("API Function:SaveStatus")
			print(ans)
			if API_URLS[-1] != API_URL:
				print_yellow("Query over API URL {0} has failed, retrying with URL {1} from API URL List: {2}".format(API_URL,API_URLS[-1],API_URLS))
				continue
			if API_Action_Lower != "handshake": #exit with non-zero exit code if not running in handshake mode to not trigger false failure when monitoring handshake mode and to allow other checks to know that query has failed
				sys.exit(1)
			else:
				return 1
def Query_SF_File(Server_SN): #Query SFC File from Shop Floor
	print_white("Requesting SFC File for SN: {0}".format(Server_SN))
	Station_Query(Server_SN) #First retrieve test station before querying SFC File for UUT
	API_Type = "CONFIG"
	API_Station = station
	if station == "REPAIR" or station == None: #If UUT has failed (Station= Repair) or UUT has passed the final test station in SF, change Station to Query to always be able to get a SFC File, this way UUT can start test and perform what checks are needed to proceed
		API_Station = "QUERY"
	for API_URL in API_URLS:
		client = Client(API_URL)
		res = client.service.SendRequest(API_Station,Server_SN,API_Type)
		Gen_SFC_File="{0}{1}.txt".format(Temp_Dir,Server_SN)
		if os.path.isfile(Gen_SFC_File): #Delete if SFC File exists
			os.system("rm -rf {0}".format(Gen_SFC_File))
		f = open(Gen_SFC_File, 'at')
		parameter_list= (res['Configs'])
		if (res['Msg'] == "OK"):
			configs =  parameter_list['Config']
			for item in configs:
				if "Parameter" in item:
					if "Value" in item:
						if item['Value'] != None:
							str = item['Parameter']+"="+item['Value']
							f.write(str+'\n')
						else:
							str = item['Parameter']+"="
							f.write(str+'\n')
						err = "Success"
					else:
						err = "Response is missing Value element"
				else:
					err = "Response is missing Parameter element"
		else:
			print_red("SFC File Query has failed, details below:")
			print(res)
			print_red("Info sent to Shop Floor:")
			print_red("API Function:SendRequest")
			print_red("Station:{0}".format(API_Station))
			print_red("UUID:{0}".format(Server_SN))
			print_red("Type:{0}".format(API_Type))
			os.system("rm -rf {0}".format(Gen_SFC_File))
			if API_URLS[-1] != API_URL:
				print_yellow("Query over API URL {0} has failed, retrying with URL {1} from API URL List: {2}".format(API_URL,API_URLS[-1],API_URLS))
				continue
			if API_Action_Lower != "handshake": #exit with non-zero exit code if not running in handshake mode to not trigger false failure when monitoring handshake mode and to allow other checks to know that query has failed
				sys.exit(1)
		f.close()
		os.system("chmod -R 777 {0}".format(Gen_SFC_File))
		return Gen_SFC_File
def Station_Query(Server_SN): #Query UUT Test Station
	global station
	station=""
	if API_Action_Lower == "handshake": #If running in handshake mode, print current time for logging purposes
		print_white("Requesting Current Test Station for SN: {0}".format(Server_SN))
	for API_URL in API_URLS:
		API_Type = "SYSTEM"
		client = Client(API_URL)
		res = client.service.ReturnStatus(Server_SN,API_Type)
		if (res['Msg'] != "OK"):
			print_yellow("API Query with Type {0} did not work. Retry with Type MB".format(API_Type))
			API_Type = "MB"
			res = client.service.ReturnStatus(Server_SN,API_Type)
		if (res['Msg'] == "OK"):
			assets =  res['Asset']
			for item in assets:
				station = item['Station']
		else:
			print_red("Station Query has failed, details below:")
			print(res)
			print_red("Info sent to Shop Floor:")
			print_red("API Function:ReturnStatus")
			print_red("UUID:{0}".format(Server_SN))
			print_red("Type:{0}".format(API_Type))
			if API_URLS[-1] != API_URL:
				print_yellow("Query over API URL {0} has failed, retrying with URL {1} from API URL List: {2}".format(API_URL,API_URLS[-1],API_URLS))
				continue
			if API_Action_Lower != "handshake": #DM for handshake, we do not need to exit the code. Handshake logic will delete the request if it's not successful
				sys.exit(1)
		if station != None:
			station = station.upper()
		if station == "":
			if API_URLS[-1] != API_URL:
				print_yellow("Query over API URL {0} has failed, retrying with URL {1} from API URL List: {2}".format(API_URL,API_URLS[-1],API_URLS))
				continue
			if API_Action_Lower != "handshake": #exit with non-zero exit code if not running in handshake mode to not trigger false failure when monitoring handshake mode and to allow other checks to know that query has failed
				sys.exit(1)
		if API_Action_Lower == "station_query": #DM this is when UUT performs UUT Station Query, to return output. for All possibilities, such as Controller running or UUT requesting SFC File, do not print Station
			print(station)
		return station
def Checkin_Function(checkin_racksn,checkin_Test_Location): #DM Function to allow checkin via API
	Input_Type="RACK"
	Input_TestLocation_Length=len(checkin_Test_Location)
	if Input_TestLocation_Length != 3: #Full location needed to prevent any issues in Database and during testing of Rack
		print_red("Please enter full Rack Testing Location. EG: A03")
		sys.exit(1)
	Input_TestLocation_FC=checkin_Test_Location[0] #Get first character to ensure test line is correct and to copy any files to correct line if needed
	Input_Position=""
	Input_PositionSub=""
	for API_URL in API_URLS:
		client = Client(API_URL)
		ans = client.get_type('ns1:CheckInCollection')()
		# fill the request structure
		ans.UUID = checkin_racksn
		ans.Type = Input_Type
		ans.TestLocation = checkin_Test_Location
		ans.Position = Input_Position
		ans.PositionSub = Input_PositionSub
		ans_cont = client.get_type('ns0:ArrayOfCheckInCollection')()
		ans_cont['CheckInCollection'].append(ans)
		res = client.service.CheckIn(ans_cont)
		if (res['Msg'] != "OK") and (res['Msg'] != "0"):
			print_red("Rack Checkin of {0} on Location {1} has failed,details below:".format(checkin_racksn,checkin_Test_Location))
			print(res)
			print_red("Info sent to Shop Floor:")
			print_red("API Function:CheckIn")
			print(ans)
			if API_URLS[-1] != API_URL:
				print_yellow("Query over API URL {0} has failed, retrying with URL {1} from API URL List: {2}".format(API_URL,API_URLS[-1],API_URLS))
				continue
			sys.exit(1)
		else:
			print_white("Rack Checkin of {0} on Location {1} has been successful.".format(checkin_racksn,checkin_Test_Location))
			os.system("echo {0} {1} >> {2}".format(checkin_racksn,checkin_Test_Location,Rack_List)) #Add into list to see which Racks are all checked-in
def Checkout_Function(checkout_racksn): #DM Function to allow checkout via API
	Input_Type="RACK"
	with open(Rack_List) as Line_Reader:
		for line in Line_Reader:
			if checkout_racksn in line:
				Input_TestLocation = line.split(' ')[1].strip()
	Input_Position=""
	Input_PositionSub=""
	for API_URL in API_URLS:
		client = Client(API_URL)
		ans = client.get_type('ns1:CheckOutCollection')()
		# fill the request structure
		ans.UUID = checkout_racksn
		ans.Type = Input_Type
		ans.TestLocation = Input_TestLocation
		ans.Position = Input_Position
		ans.PositionSub = Input_PositionSub
		ans_cont = client.get_type('ns0:ArrayOfCheckOutCollection')()
		ans_cont['CheckOutCollection'].append(ans)
		res = client.service.CheckOut(ans_cont)
		if (res['Msg'] != "OK"):
			print_red("Rack Checkout of {0} has failed,details below:".format(checkout_racksn))
			print(res)
			print_red("Info sent to Shop Floor:")
			print_red("API Function:CheckOut")
			print(ans)
			if API_URLS[-1] != API_URL:
				print_yellow("Query over API URL {0} has failed, retrying with URL {1} from API URL List: {2}".format(API_URL,API_URLS[-1],API_URLS))
				continue
			sys.exit(1)
		else:
			print_white("Rack Checkout of {0} has been successful.".format(checkout_racksn))
			with open(Rack_List) as Line_Reader:
				for line in Line_Reader:
					if checkout_racksn in line:
						Remove_Rack_Line = line.strip()
						os.system("sed -i 's/{0}//g' {1}".format(Remove_Rack_Line,Rack_List)) #Remove rack information from list of racks in test
			Line_Reader.close()
def API_RHBT(Background_API_Request): #API Request handshake background Task
	Process_File = "Y" #DM this flag is to let API Handshake mode know it's fine to send request to SF
	LASF = "{0}{1}".format(Temp_Dir,RASF) #LASF = Local API Service File
	FRASF = "{0}{1}".format(API_Request_Path,RASF) #FRASF = Full Remote API Service File #Full path of API request File
	API_Response = "{0}{1}".format(API_Request_Path,RASF.replace("Request","Response")) #File containing contents from SF that API will return back to UUT
	API_H_Fun = ""
	API_H_Serial = ""
	API_H_Mess = ""
	API_H_Status = ""
	API_H_Station = ""
	API_H_RackSN = ""
	API_Request_Processed="Y" #DM set flag to yes and if any issue is detected, flag will be set to no so that the request from UUT is not deleted but checked during next iteration
	if os.path.isfile(LASF):
		os.remove(LASF)
	shutil.copyfile(FRASF, LASF)
	with open(LASF) as Line_Reader:
		for line in Line_Reader:
			try:
				if "FUNCTION:" in line.upper():
					API_H_Fun = line.split(':')[1].strip().replace(" ","") #API Handshake Function, function that will be called by API
				if "SERIAL:" in line.upper():
					API_H_Serial = line.split(':')[1].strip() #API Handshake Serial, Serial of UUT that will be used when calling a function
				if "MESSAGE:" in line.upper():
					API_H_Mess = line.split(':',1)[1].strip() #API Handshake Message, UUT Test Mesage, EG: Flash Bios
				if "STATUS:" in line.upper():
					API_H_Status = line.split(':')[1].strip() #API Handshake Status, UUT Test Status, EG: Reboot
				if "STATION:" in line.upper():
					API_H_Station = line.split(':')[1].strip() #API Handshake Station, UUTs current Station that's being sent in
				if "RACKSN:" in line.upper():
					API_H_RackSN = line.split(':')[1].strip() #API Handshake Rack Serial Number, Current UUTs Rack Serial
			except:
				print_yellow("API Request File: {0} has an issue. Ignoring it".format(LASF))
				os.system("cat {0}".format(LASF))
				Process_File = "N"
	Line_Reader.close()
	if API_H_Serial.upper() == "TBC":
		print_yellow("Serial Number: {0} is invalid, deleting request".format(API_H_Serial))
		os.system("rm -f {0}".format(FRASF)) #DM remove file containing invalid SN
		Process_File="N"
	if Process_File == "Y":
		if API_H_Fun.lower() == "sfc_file":
			Gen_SFC_File = Query_SF_File(API_H_Serial)
			if os.path.isfile(Gen_SFC_File): #DM file not generated, if error, delete request and wait for new request
				shutil.copyfile(Gen_SFC_File, API_Response)
			else:
				API_Request_Processed="N"
				os.system("rm -f {0}".format(FRASF)) #DM invalid status file, delete and have UUT send new, valid request
		elif API_H_Fun.lower() == "rlt_file":
			if API_H_Serial == "": #DM No serial sent, delete and have UUT resend with it's next iteration but store information in Status Report for TE investigation
				os.system("rm -f {0}".format(FRASF))
				API_Request_Processed="N"
			else:
				Gen_RLT_File = RLT_File(API_H_Serial)
				shutil.copyfile(Gen_RLT_File, API_Response)
		elif API_H_Fun.lower() == "station_query":
			Station_Return = Station_Query(API_H_Serial)
			f = open(LASF, 'w')
			f.write(str(Station_Return))
			f.close()
			shutil.copyfile(LASF, API_Response)
		elif API_H_Fun.lower() == "send2sf":
			ret = Send2sf_Function(API_H_Serial,API_H_Mess,API_H_Status,API_H_Station,API_H_RackSN)
			if ret != None:
				print(ret)
				API_Request_Processed="N"
				print_red("send2sf function has failed")
				os.system("rm -f {0}".format(FRASF)) #DM remove file for several reasons 1)status could be outdated or invalid 2)it may cause confusion with repair Team if old status gets sent once Repair Action has been added
			if API_H_Serial == "": #DM No serial sent, delete and have UUT resend with it's next iteration but store information in Status Report for TE investigation
				os.system("rm -f {0}".format(FRASF)) #DM invalid status file, delete and have UUT send new, valid request
			if ret == None: #send2sf handshake has been successful
				os.system("echo OK > {0}".format(API_Response))
		else:
			print_yellow("Function: |{0}| is not yet implemented for handshake function".format(API_H_Fun))
			API_Request_Processed="N"
		if API_Request_Processed == "Y":
			os.system("rm -f {0}".format(LASF))
			os.system("rm -f {0}".format(FRASF))



def main():
	if Executing_Device == "CONTROLLER":
		if not os.path.isfile(API_Inventory_File):
			print_red("{0} does not exist".format(API_Inventory_File))
			os._exit(1)
		with open(API_Inventory_File) as Line_Reader:
			for line in Line_Reader:
				if "API_URL" in line.upper():
					Defined_API_URLS = line.split(',')[1].strip()
					if ";" in Defined_API_URLS:
						API_URLS = Defined_API_URLS.split(";")
					else:
						URL_List.append(Defined_API_URLS)
						API_URLS = URL_List
			Line_Reader.close()
		if Defined_API_URLS == "":
			print_red("Unable to determine API URL from {0}".format(API_Inventory_File))
			print_red("Please help check if it's maintained in proper format: API_URL,$URL")
			print_red("For example, from QCG: API_URL,http://10.245.97.38/AMAL11/AMAService.svc?singleWsdl")
			print_red("If multiple URLs are maintained, please help separate the URLs with semicolon ;. For Example:, from QCG: API_URL,http://10.245.97.38/AMAL11/AMAService.svc?singleWsdl;http://10.245.97.39/AMAL11_Test/AMAService.svc?singleWsdl")
			os._exit(1)
	if len(sys.argv) == 1:
		print_red("Please provide the action to be requested from SF API")
		print_yellow("For a help menu, please add a argument when calling the script")
		print_yellow("For Example {0} --help or {0} -?".format(sys.argv[0]))
		sys.exit(1)
	Starting_API_M5_sum = md5(sys.argv[0])
	API_Action = sys.argv[1] #action Name #spaces are not allowed in action names to standadize input
	API_Action_Lower = sys.argv[1].lower() #Action name but in lowercase to simplify coding
	if " " in API_Action:
		print_red("Empty spaces are not allowed in action items")
		sys.exit(1)
	if API_Action == "-help" or API_Action == "--?":
		print_red("For help Menu, please call --help or -?")
		sys.exit(0)
	Allowed_API_Action_List = ['RLT_File','send2sf','SFC_File','Station_Query','CheckIn','CheckOut','Handshake','test']
	if API_Action_Lower == "--help" or API_Action_Lower == "-?":
		print_yellow("API URL for Controller is read from: {0}".format(API_Inventory_File))
		print_teal("*Example from QCG: API_URL,http://10.245.97.38/AMAL11/AMAService.svc?singleWsdl")
		print_yellow("Actions are not case sensitive")
		print_yellow("Allowed Actions: {0}".format(Allowed_API_Action_List))
		print_yellow("Action explanations:")
		print_white("*RLT_File: Requests Rack RLT File for a given Rack")
		print_pink("**Usage: {0} RLT_File <RACKSN>".format(sys.argv[0]))
		print_teal("**Example: {0} RLT_File QCGAMA2240007".format(sys.argv[0]))
		print_white("*send2sf: Send status to Shop Floor")
		print_pink("**Usage: {0} send2sf <UUT_SN> '<MESSAGE>' <STATUS> <STATION> <RACKSN>".format(sys.argv[0]))
		print_teal("**Example: {0} send2sf J223409Y9 \"Fail to do DMC12CHK\" WARNING FST QCGAMA2242025".format(sys.argv[0]))
		print_white("*SFC_File: Request SFC File for Server or MB SN")
		print_pink("**Usage: {0} SFC_File <UUT_SN> or {0} SFC_File <MB_SN>".format(sys.argv[0]))
		print_teal("**Example: {0} SFC_File QTFCTW234012F".format(sys.argv[0]))
		print_white("*Station_Query: Request current test Station for Server SN")
		print_pink("**Usage: {0} Station_Query <UUT_SN> or {0} Station_Query <MB_SN>".format(sys.argv[0]))
		print_teal("**Example: {0} Station_Query QCG0522420007".format(sys.argv[0]))
		print_white("*CheckIn: Check In Rack for testing")
		print_pink("**Usage: {0} CheckIn <RACKSN> <Test_Location>".format(sys.argv[0]))
		print_teal("**Example: {0} CheckIn QCGAMA2243055 G23".format(sys.argv[0]))
		print_white("*CheckOut: Check Out Rack after testing has finished")
		print_pink("**Usage: {0} CheckOut <RACKSN>".format(sys.argv[0]))
		print_teal("**Example: {0} CheckOut QCGAMA2243055".format(sys.argv[0]))
		print_white("*Handshake: Program will run in Handshake mode and monitor for any API requests that are sent by UUTs and stored in /win/API_Request/")
		print_pink("**Usage: {0} Handshake".format(sys.argv[0]))
		print_white("*test: test function only intended for testing purposes".format(sys.argv[0]))
		print_pink("**Usage: {0} test <query>".format(sys.argv[0]))
		print_teal("**Example: {0} test TWA1UB22500203".format(sys.argv[0]))
		sys.exit(0)
	API_Action_Allowed = 0
	for Allowed_API_Action in Allowed_API_Action_List:
		if API_Action_Lower == Allowed_API_Action.lower():
			API_Action_Allowed = 1
			break
	if API_Action_Allowed == 0:
		print_red("API Action {0} is not allowed".format(API_Action))
		print_red("Current API Action allowed list (Actions are not case sensitive):{0}".format(Allowed_API_Action_List))
		sys.exit(1)
	if API_Action_Lower == "rlt_file":
		if len(sys.argv) != 3:
			print_red("RackSN is missing for SF query:{0} RLT_File <RACKSN>".format(sys.argv[0]))
			if API_Action_Lower != "handshake":
				sys.exit(1)
		RackSN = sys.argv[2]
		RLT_File(RackSN)
	elif API_Action_Lower == "send2sf":
		if len(sys.argv) != 7:
			print_red("Please enter all relevant data:{0} send2sf <UUT_SN> '<MESSAGE>' <STATUS> <STATION> <RACKSN>".format(sys.argv[0]))
			if API_Action_Lower != "handshake":
				sys.exit(1)
		serial=sys.argv[2]
		message=sys.argv[3]
		status=sys.argv[4].upper() #Please be careful if Status is PASS because PASS is used ONLY when station is pass, everything else should not be pass #DM only PASS, FAIL and START will be saved in DB, everything else will be slightly modified, for example: FRU-FINISH PASS but RUNNING:BIOS FLASH if you want to send "BIOS FLASH" with "RUNNING" Status
		station=sys.argv[5].upper()
		rack=sys.argv[6].upper()
		Send2sf_Function(serial,message,status,station,rack)
	elif API_Action_Lower == "sfc_file":
		if len(sys.argv) != 3:
			print_red("Server SN is missing for SF query:{0} SFC_File <UUT_SN> or {0} SFC_File <MB_SN>".format(sys.argv[0]))
			if API_Action_Lower != "handshake":
				sys.exit(1)
		sfc_file_serial=sys.argv[2]
		Query_SF_File(sfc_file_serial)
	elif API_Action_Lower == "station_query":
		if len(sys.argv) != 3:
			print_red("MB SN is missing for SF query:{0} Station_Query <UUT_SN>".format(sys.argv[0]))
			if API_Action_Lower != "handshake":
				sys.exit(1)
		station_query_serial=sys.argv[2]
		Station_Query(station_query_serial)
	elif API_Action_Lower == "checkin":
		if len(sys.argv) != 4:
			print_red("Please enter all relevant data:{0} CheckIn <RACKSN> <Test_Location>".format(sys.argv[0]))
			sys.exit(1)
		Input_UUID=sys.argv[2].upper().strip()
		Input_TestLocation=sys.argv[3].upper().strip()
		Checkin_Function(Input_UUID,Input_TestLocation)
	elif API_Action_Lower == "checkout":
		if len(sys.argv) != 3:
			print_red("Please enter all relevant data:{0} CheckOut <RACKSN>".format(sys.argv[0]))
			sys.exit(1)
		Input_UUID=sys.argv[2].upper().strip()
		Checkout_Function(Input_UUID)
	elif API_Action_Lower == "handshake":
		while(True):
			Request_Back_Threads = []
			Production_Lines = (os.listdir("/mnt/"))
			for Prod_Line in Production_Lines:
				API_Request_Path="/mnt/{0}/win/API_Request/".format(Prod_Line)
				if os.path.exists("{0}".format(API_Request_Path)):
					Line_Requests=sorted(os.listdir(API_Request_Path))
					for RASF in Line_Requests: #RASF = Remote API Service File #Filename only
						if "request" not in RASF.lower(): #DM ignore returned API Responses that were not yet processed by UUT
							continue
						Request_Back = threading.Thread(target=API_RHBT,args=(RASF,))
						Request_Back_Threads.append(Request_Back)
						Request_Back.start()
						time.sleep(0.1) #time sleeping after processing each request
					for x in Request_Back_Threads:
						x.join()
				time.sleep(0.5) #time sleeping after processing each line
			Current_API_M5_sum = md5(sys.argv[0]) #DM get current md5sum after all Lines have been checked for API requests and stop running API Script in handshake mode if Script has been changed to restart with latest changes
			if Starting_API_M5_sum != Current_API_M5_sum:
				print_yellow("{0} has been changed. Exiting current iteration".format(sys.argv[0]))
				os._exit(0)
	else:
		print_red("What is the meaning of {0}, life and the universe?".format(API_Action))
		sys.exit(1)


if __name__ == "__main__":
	API_Action = sys.argv[1] #action Name #spaces are not allowed in action names to standadize input
	API_Action_Lower = sys.argv[1].lower() #Action name but in lowercase to simplify coding
	if " " in API_Action:
		print_red("Empty spaces are not allowed in action items")
		sys.exit(1)
	if API_Action == "-help" or API_Action == "--?":
		print_red("For help Menu, please call --help or -?")
		sys.exit(0)
	main()