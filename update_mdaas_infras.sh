#!/bin/bash
expectedVersion="202310.4.1"
currentVersion=$(docker ps | grep mdaas-infra | awk -F'mdaas-infra:' '{split($2, a, " "); print a[1]}')

if [ "$expectedVersion" = "$currentVersion" ]; then
    echo "Current Version is expected"
elif [ "$expectedVersion" != "$currentVersion" ]; then
    echo "$currentVersion is not expected version $expectedVersion"
    echo "Attempting Update"
    cd /home/container 
    chmod +x install_"$expectedVersion".sh
    yes '' | ./install_"$expectedVersion".sh ZOMBIE_KILLER_CYCLE_MIN=10
else
    echo "Variables are not defined"
fi