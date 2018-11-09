#!/bin/bash

apt install python3 virtualenv python3-pip git -y
cd /usr/lib/
git clone https://github.com/digitalreachinsight/python-remote-monitor.git 
cd /usr/lib/python-remote-monitor/
virtualenv -p python3 venv
pip install -r requirements.txt 
