#!/usr/bin/env python3

""" RTP program will generate the commodity file (autolink)
    This will need send to SFC folder
"""
SCAN_DIR='/RACKLOG/Autolink'
SF_DIR='/SFC/Autolink/'

from genericpath import isdir
from operator import le
import os
import shutil
import datetime
import logging

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
    today_fdr = datetime.datetime.now().strftime('%m-%d-%y')
    if not os.path.exists(SCAN_DIR):
        os.makedirs(SCAN_DIR)
    if not os.path.exists(SF_DIR):
        os.makedirs(SF_DIR)

    os.chdir(SCAN_DIR)
    files = os.listdir(SCAN_DIR)
    for f in files:
        if f.startswith('B') or f.startswith('M'):
            logging.info(f'copy to:{SF_DIR+f}')
            shutil.copy(f, SF_DIR+f)

            if os.path.isdir(today_fdr) is False:
                os.mkdir(today_fdr)
            today_fdr = os.path.join(today_fdr, '')
            try:
                shutil.move(f, today_fdr)
            except Exception as error:
                logging.error(error)
                os.unlink(f)
                
            


        

