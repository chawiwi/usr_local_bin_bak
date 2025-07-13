#!/bin/bash
/usr/local/bin/RM_Monitor.py >> /var/log/rm_monitor.log 2>&1
/usr/local/bin/mdaas.py >> /var/log/mdaas.log 2>&1
/usr/local/bin/swlog >> /var/log/swlog.log 2> &1