#!/bin/bash
# Daily purge Project files
for entry in /WIN/*
do
	cfg='loop'
	dir=$entry/$cfg
	if [ -d $dir ]; 
	then
		# delete outdated loop files, folder /WIN/{entry}/loop
		echo "purge $dir"
		find $dir -mtime +90 -exec rm -rf {} \;
	fi
	cfg='50G'
	dir=$entry/$cfg
	if [ -d $dir ]; 
	then
		echo "purge $dir"
		# delete outdated 50G files, /WIN/{entry}/50G
		find $dir -mtime +7 -exec rm -rf {} \;
	fi
done
