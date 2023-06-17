#!/usr/bin/env python
#import confy
import os
import sys
import requests
import json
import socket
import re
import threading
from netaddr import IPAddress
from platform   import system as system_name
import subprocess, platform
#from subprocess import call   as system_call, DEVNULL, STDOUT
from subprocess import call   as system_call
version = '1.20'
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

#nbtscan 10.1.1.0-255
#arp -a
def check_if_file_exists(path):
    isFile = os.path.isfile(path) 
    return isFile

def check_if_dir_exists(path):
    isDir = os.path.isdir(path)
    return isDir


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

def scan_for_devices():
    #intefaces_lookup = ['ifconfig']
    #il = system_call(intefaces_lookup)
    il = subprocess.Popen("route -n", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    p_stdout = il.stdout.read()
    p_stderr = il.stderr.read()
    il_lines = p_stdout.decode('utf-8').split("\n")
    networks = []
    for i in il_lines:
        row = re.split(r'\s+', i)
        if len(row) > 1:
           try: 
                IPAddress(row[0])
                network = row[0]
                if network != '0.0.0.0':
                   netmask = row[2]
                   prefix_network = IPAddress(netmask).netmask_bits()
                   networks.append(str(network)+'/'+str(prefix_network))
           except:
                pass
                #print ('invalid ip')
    print (networks)
    
        #print (i)
    devices_found = []
    #for n in networks:
    #      il = subprocess.Popen("nbtscan "+n, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    #      p_stdout = il.stdout.read()
    #      p_stderr = il.stderr.read()
    #      nb_lines = p_stdout.decode('utf-8').split("\n")
    #      for h in nb_lines:
    #           row = re.split(r'\s+', h)
    #           try:
    #               IPAddress(row[0])
    #               nb_ip = row[0]
    #               netbios_name = row[1]
    #               #print (nb_ip)
    #               #print (netbios_name)
    #               devices_found.append({'netbios_name': netbios_name,'ip':nb_ip})
    #               
    #           except:
    #               pass
    #               #print ('invalid ip')
    #print (p_stdout.decode('utf-8'))
    arp = subprocess.Popen("arp | grep -v incomplete | grep -v 'Address' ", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    p_stdout = arp.stdout.read()
    p_stderr = arp.stderr.read()
    arp_lines = p_stdout.decode('utf-8').split("\n")
    for a in arp_lines:
        row = re.split(r'\s+', a)
        if len(row) > 2:
           arp_ip = row[0]
           arp_mac = row[2]
           dfcount = 0
           #found = False
           #for df in devices_found:
           #    if df['ip'] == arp_ip:
           #        found=True
           #        devices_found[dfcount]['mac'] = arp_mac
           #    dfcount = dfcount + 1
           #if found is False:
           devices_found.append({'netbios_name':'', 'ip': arp_ip, 'mac': arp_mac}) 

    for n in networks:
          il = subprocess.Popen("nbtscan "+n, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
          p_stdout = il.stdout.read()
          p_stderr = il.stderr.read()
          nb_lines = p_stdout.decode('utf-8').split("\n")
          for h in nb_lines:
               row = re.split(r'\s+', h)
               try:
                   IPAddress(row[0])
                   nb_ip = row[0]
                   netbios_name = row[1]

                   found = False
                   dfcount = 0
                   for df in devices_found:
                        if df['ip'] == nb_ip:
                              devices_found[dfcount]['netbios_name'] = netbios_name
                        dfcount = dfcount + 1
                   #print (nb_ip)
                   #print (netbios_name)
                   #devices_found.append({'netbios_name': netbios_name,'ip':nb_ip})
                   
               except:
                   pass
                   #print ('invalid ip')
    #print (p_stdout.decode('utf-8'))

 
    print (devices_found)
    data = {'devices': json.dumps(devices_found),}
    r = requests.post(host_url+'mon/update-system/?system_id='+str(system_id)+'&key='+str(api_key)+'&version='+version, data = data)
    print (r.text)

    #return True 

    #command = ['nbtscan 10.1.1.0-255']

def ping_name(mon_type_id,host,mac_address, ip_addr):
      print ("PING NAME")
      print (host) 

      arp = subprocess.Popen("arp -n | grep -v incomplete | grep -v 'Address' | grep '"+mac_address+"' | awk '{print $1}' | sed 's/[()]//g'", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
      p_stdout = arp.stdout.read()
      p_stderr = arp.stderr.read()
      ip_address = p_stdout.decode('utf-8')
      if len(ip_address) > 6:
        pass
      else:
         ip_address = ip_addr
      print (ip_address)
      pr = ping(ip_address)
      print (pr)
      return str(pr)


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
    print ("PING")
    print (ping_response)
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

def disk():
    #df -h | grep '^/dev/'
    disk_array = []
    disk_resp = subprocess.Popen("df -h  | grep '^/dev/' ", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    p_stdout = disk_resp.stdout.read()
    p_stderr = disk_resp.stderr.read()
    resp = p_stdout.decode('utf-8')
    resp_array = resp.splitlines()
    for row in resp_array:
        line_array = re.split("\s+", row) 
        disk_array.append(line_array)
    return disk_array 

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

def nettraf():
    pass 

    nettraf_array = []
    nettraf_resp = subprocess.Popen('cat /proc/net/dev  | grep -v "|"', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    p_stdout = nettraf_resp.stdout.read()
    p_stderr = nettraf_resp.stderr.read()
    resp = p_stdout.decode('utf-8')
    resp_array = resp.splitlines()
    for row in resp_array:
        row = re.sub("^\s+", "", row)
        line_array = re.split("\s+", row)
        nettraf_array.append(line_array)
    return nettraf_array

def get_lastlogins():
    last_logins = []
    last_logins_resp = subprocess.Popen('last -wiFa -s -3days | grep -v "system boot"', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    p_stdout = last_logins_resp.stdout.read()
    p_stderr = last_logins_resp.stderr.read()
    resp = p_stdout.decode('utf-8')    
    return resp

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
if obj['scan_network_for_devices'] is True:
   thread = threading.Thread(target=scan_for_devices(), args=())
   thread.start()

   #sfd = scan_for_devices()
   pass

print ("Starting System Checks")
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
      disk_resp = disk()
      data = {'disks': json.dumps(disk_resp),} 
      r = requests.post(host_url+'mon/update-system-monitor/?system_monitor_id='+str(s['check_id'])+'&response='+''+'&key='+str(api_key), data = data)
      #df -h --output=source,pcent
      #df -h | grep '^/dev/'
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
   elif s['mon_type_id'] == 11:
      net_traf = nettraf()
      data = {'nettraf': json.dumps(net_traf),}
      r = requests.post(host_url+'mon/update-system-monitor/?system_monitor_id='+str(s['check_id'])+'&response='+''+'&key='+str(api_key), data = data)
   elif s['mon_type_id'] == 12:
      pingresp = ping_name(s['mon_type_id'],s['host'],s['mac_address'], s['ip_address'])
      r = requests.get(host_url+'mon/update-system-monitor/?system_monitor_id='+str(s['check_id'])+'&response='+pingresp.lower()+'&key='+str(api_key))   
   elif s['mon_type_id'] == 13:
       fd_exists = check_if_dir_exists(str(s['string_check']))
       r = requests.get(host_url+'mon/update-system-monitor/?system_monitor_id='+str(s['check_id'])+'&response='+str(fd_exists)+'&key='+str(api_key))
   elif s['mon_type_id'] == 14:
       fd_exists = check_if_file_exists(str(s['string_check']))
       r = requests.get(host_url+'mon/update-system-monitor/?system_monitor_id='+str(s['check_id'])+'&response='+str(fd_exists)+'&key='+str(api_key))      
   elif s['mon_type_id'] == 15:
       lastlogins = get_lastlogins()
       data = {'lastlogins': json.dumps(lastlogins),}       
       r = requests.post(host_url+'mon/update-system-monitor/?system_monitor_id='+str(s['check_id'])+'&response=''&key='+str(api_key), data = data)
