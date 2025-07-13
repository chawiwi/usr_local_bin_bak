#!/bin/bash

# Get the permissions of /dev/null
permissions=$(stat -c "%a" /dev/null)

# Check if the permissions are equal to 644 (rw-r--r--)
if [ "$permissions" -eq 644 ]; then
    # Run the specified commands
    rm -f /dev/null
    mknod -m 666 /dev/null c 1 3
    echo "Commands executed successfully."
else
    echo "File /dev/null does not have the expected permissions."
fi