#!/bin/bash
  
find "/WIN/NetApp/Response" -type f -mtime +20 -exec rm {} \;
find "/WIN/t6j/sfconfig" -type f -mtime +20 -exec rm {} \;
find "/RACKLOG/t6j/RM_logs" -type d -mtime +30 -exec rm -r {} \;
find "/RACKLOG/t6j/RM_logs" -type f -name "*updating.log" -mtime +3 -exec rm {} \;
find "/RACKLOG/t6k/RM_logs" -type d -mtime +30 -exec rm -r {} \;
find "/RACKLOG/t6k/RM_logs" -type f -name "*updating.log" -mtime +3 -exec rm {} \;
find "/WIN/T6K/sfconfig" -type f -mtime +20 -exec rm {} \;
find "/RACKLOG/t6h/RM_logs" -type d -mtime +30 -exec rm -r {} \;
find "/RACKLOG/t6h/RM_logs" -type f -name "*updating.log" -mtime +3 -exec rm {} \;
find "/WIN/T6H/sfconfig" -type f -mtime +20 -exec rm {} \;
find "/RACKLOG/t6g/RM_logs" -type d -mtime +30 -exec rm -r {} \;
find "/RACKLOG/t6g/RM_logs" -type f -name "*updating.log" -mtime +3 -exec rm {} \;
find "/WIN/T6G/sfconfig" -type f -mtime +20 -exec rm {} \;
