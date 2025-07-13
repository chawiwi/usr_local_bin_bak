#!/usr/bin/env python3
#Generate AC files in this folder
from re import sub
import glob
import subprocess
import logging
import os
from isc_dhcp_leases import Lease, IscDhcpLeases


if __name__ == '__main__':
    """ This program send batch RM commands by arrays of serial number 
    """
    sns = []
    line = input('Paste Arrays of Serial numbers (press enter twice if you copy from Test Monitor):\n').strip()
    while len(str(line)) != 0:
        sns.append(line.strip())
        line = input()

    # Search for RM MAC address by serial number
    if len(sns) == 0:
        logging.error('No serial number inputed')
        exit(1)

    for sn in sns:
        with open(f'{sn}.txt', 'w') as snfile:
            snfile.write('ACTION=AC_CYCLE\n')
           
