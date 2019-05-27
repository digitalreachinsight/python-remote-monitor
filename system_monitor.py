#!/usr/bin/env python
#import confy
import os
import sys
import requests
import json
import socket
from platform   import system as system_name
import subprocess, platform
#from subprocess import call   as system_call, DEVNULL, STDOUT
from subprocess import call   as system_call
version = '1.15'
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

def cpu_usage():
   #cpu_usage = "echo $[100-$(vmstat 1 2|tail -1|awk '{print $15}')]"
   # all cpu cores
#   cpu_usage = "echo $[$(vmstat 1 2|tail -1|awk '{print $13}')]"
   cpu_usage = "echo $(vmstat 1 10|tail -1|awk '{print $13}')"
#   cpu_resp = system_call(cpu_usage, shell=True)
   cpu_resp = subprocess.Popen("echo $(vmstat 1 10|tail -1|awk '{print $13}')", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
   p_stdout = cpu_resp.stdout.read()
   p_stderr = cpu_resp.stderr.read()
   return p_stdout.decode('utf-8') 

def memory():
    mem_resp = subprocess.Popen("free -m | grep 'Mem:' | awk '/Mem:/ { print $2.\":\"$3.\":\"$4 } /buff\/cache/ { print $3 }'", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    p_stdout = mem_resp.stdout.read()
    p_stderr = mem_resp.stderr.read()
    print (p_stdout.decode('utf-8'))
    return p_stdout.decode('utf-8')

def swap():
    mem_resp = subprocess.Popen("free -m | grep 'Swap:' | awk '/Swap:/ { print $2.\":\"$3.\":\"$4 } /buff\/cache/ { print $3 }'", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    p_stdout = mem_resp.stdout.read()
    p_stderr = mem_resp.stderr.read()
    print (p_stdout.decode('utf-8'))
    return p_stdout.decode('utf-8')

def ping2(mon_type, server='www.google.com', count=1, wait_sec=1):
    """
    :rtype: dict or None
    """
    resp = {}
    cmd = "ping -c {} -W {} {}".format(count, wait_sec, server).split(' ')
    print ("START PING 2")
    try:
            output = subprocess.check_output(cmd).decode().strip()
            lines = output.split("\n")
            total = lines[-2].split(',')[3].split()[1]
            loss = lines[-2].split(',')[2].split()[0]
            timing = lines[-1].split()[3].split('/')
            resp = {
                'type': 'rtt',
                'min': timing[0],
                'avg': timing[1],
                'max': timing[2],
                'mdev': timing[3],
                'total': total,
                'loss': loss,
            }
    except Exception as e:
            print(e)
            resp = {'avg': None,'loss' : '100%'}
    if mon_type == 6:
        return resp['avg']
    if mon_type == 7:
        return resp['loss']

# system_monitor

r = requests.get(host_url+'mon/get-system-monitor/?system_id='+str(system_id)+'&key='+str(api_key)+'&version='+version+'&machine_id='+machine_id)
json_resp = r.json()
print (r.text)
obj = json.loads(r.text)
if obj['result'] == 'error':
   print (obj['message'])
   exit()
print (obj['system_name'])

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
      print (found)
   elif s['mon_type_id'] == 2:
      pingresp = str(ping(s['host']))
      print (pingresp)
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
   elif s['mon_type_id'] == 6:
      pingresp = str(ping2(s['mon_type_id'], s['host'],10,1))
      print (pingresp)
      r = requests.get(host_url+'mon/update-system-monitor/?system_monitor_id='+str(s['check_id'])+'&response='+pingresp.lower()+'&key='+str(api_key))
   elif s['mon_type_id'] == 7:
      pingresp = str(ping2(s['mon_type_id'], s['host'],10,1))
      print (pingresp)
      r = requests.get(host_url+'mon/update-system-monitor/?system_monitor_id='+str(s['check_id'])+'&response='+pingresp.lower()+'&key='+str(api_key))
   elif s['mon_type_id'] == 8:
      cpuresp = str(cpu_usage())
      print ("CPU USAGE")
      print (cpuresp)
      r = requests.get(host_url+'mon/update-system-monitor/?system_monitor_id='+str(s['check_id'])+'&response='+cpuresp+'&key='+str(api_key))

   elif s['mon_type_id'] == 9:
      memory = str(memory())
      print (host_url+'mon/update-system-monitor/?system_monitor_id='+str(s['check_id'])+'&response='+memory+'&key='+str(api_key))
      r = requests.get(host_url+'mon/update-system-monitor/?system_monitor_id='+str(s['check_id'])+'&response='+memory+'&key='+str(api_key))
      #print (r)
   elif s['mon_type_id'] == 10:
      swap = str(swap())
      r = requests.get(host_url+'mon/update-system-monitor/?system_monitor_id='+str(s['check_id'])+'&response='+swap+'&key='+str(api_key))
      #print (r)

#for i in r:
#    print (r['system_name'])

