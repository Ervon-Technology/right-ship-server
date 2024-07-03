#!/bin/bash
source /home/ubuntu/right-ship-server/venv/bin/activate
/usr/bin/python3 /home/ubuntu/right-ship-server/app.py >> /home/ubuntu/right-ship-server/script_run.log 2>&1
