#!/bin/bash
DIR=$(dirname "$(readlink -f "$0")")
cd $DIR
git pull 
/usr/lib/python-remote-monitor/venv/bin/pip3 install -r requirements.txt
