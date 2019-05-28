#!/bin/bash

yum install python34 python-pip git -y
pip install -U pip
pip install -U virtualenv
cd /usr/lib/
git clone https://github.com/digitalreachinsight/python-remote-monitor.git 
cd /usr/lib/python-remote-monitor/
virtualenv -p python34 venv
/usr/lib/python-remote-monitor/venv/bin/pip3 install -r requirements.txt 
chmod +x /usr/lib/python-remote-monitor/update.sh
groupadd drmonitor
useradd -m drmonitor -g drmonitor -s /usr/sbin/nologin
chown -R drmonitor.drmonitor /usr/lib/python-remote-monitor/
