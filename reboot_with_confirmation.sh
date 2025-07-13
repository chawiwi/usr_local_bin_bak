#!/bin/bash

# Define ANSI escape codes for red text
RED='\033[0;91m'
NC='\033[0m'  # No color

# Display a warning in bright red
echo -e "${RED}THIS IS A PXE. ARE YOU SURE? (Type YES to proceed)${NC}"

# Read user input
read user_input

# Check if the input is 'YES' (case-sensitive)
if [[ "$user_input" == "YES" ]]; then
    # Execute the requested command
    exec "$@"
else
    echo "Command execution aborted."
fi
