#!/usr/bin/env python
#import confy
import os
import sys
import requests
import json
import socket
from platform   import system as system_name
#from subprocess import call   as system_call, DEVNULL, STDOUT
from subprocess import call   as system_call
version = '1.3'
host_url = 'https://monitor.digitalreach.com.au/'
print ("Running remote monitor version "+version)

system_id = sys.argv[1]
api_key = sys.argv[2]

#file="/etc/machine-id"
#path=file
#fp=open(path,'r+');
machine_id = None
if os.path.isfile("/etc/machine-id"):
   machine_id = open("/etc/machine-id", 'r').read().strip()
#   print machine_id+"-DD"
if machine_id is None:
   print ("Machine ID error")
   exit()

# (1, 'webconnect', ('Web Page - String')),
# (2, 'ping', ('Ping')),
# (3, 'portopen',('Port Open')),
# (4, 'diskcheck', ('Disk Check'))

def socket_connect(host,port):
    #print ("SOCKET")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(30)
    result = None

    try:
       result = sock.connect_ex((host,port))
    except socket.gaierror:
       pass

    if result == 0:
       return True
    else:
       return False

def ping(host):
    """
    Returns True if host (str) responds to a ping request.
    Remember that a host may not respond to a ping (ICMP) request even if the host name is valid.
    """
    # Ping command count option as function of OS
    param = '-n' if system_name().lower()=='windows' else '-c'

    # Building the command. Ex: "ping -c 1 google.com"
    command = ['ping', param, '4', host]
    # Pinging
#    ping_response = system_call(command, stdout=DEVNULL, stderr=STDOUT) == 0
    ping_response = system_call(command) == 0
    return ping_response

r = requests.get(host_url+'mon/get-system-monitor/?system_id='+str(system_id)+'&key='+str(api_key)+'&version='+version+'&machine_id='+machine_id)
json_resp = r.json()
#print r.text
obj = json.loads(r.text)
if obj['result'] == 'error':
   print (obj['message'])
   exit()
print (obj['system_name'])

# system_monitor
for s in obj['system_monitor']:
   print (s['check_name'])
   print (s['mon_type_id'])
   
   if s['mon_type_id'] == 1:
      a = None
      html_str = ''
      try:
         a = requests.get(s['host'])
      except Exception as e:
         a = None
         html_str = ''
         pass

      if a:
          html_str = a.text
      #print a.text
      #print (s['string_check'])
      found = 'false'
      if str(s['string_check']) in html_str:
         found = 'true'
      else:
         found = 'false'
      r = requests.get(host_url+'mon/update-system-monitor/?system_monitor_id='+str(s['check_id'])+'&response='+found.lower()+'&key='+str(api_key))
   elif s['mon_type_id'] == 2:
      pingresp = str(ping(s['host']))
      r = requests.get(host_url+'mon/update-system-monitor/?system_monitor_id='+str(s['check_id'])+'&response='+pingresp.lower()+'&key='+str(api_key))  
   elif s['mon_type_id'] == 3:
      socket_resp = str(socket_connect(s['host'],int(s['port'])))
      r = requests.get(host_url+'mon/update-system-monitor/?system_monitor_id='+str(s['check_id'])+'&response='+socket_resp.lower()+'&key='+str(api_key))
   elif s['mon_type_id'] == 4:
      #df -h --output=source,pcent
      pass
   elif s['mon_type_id'] == 5:
      SECURITY_UPDATES = os.popen('apt-get upgrade -s| grep ^Inst |grep security  | wc -l').read()    
      r = requests.get(host_url+'mon/update-system-monitor/?system_monitor_id='+str(s['check_id'])+'&response='+SECURITY_UPDATES+'&key='+str(api_key))


#for i in r:
#    print (r['system_name'])

