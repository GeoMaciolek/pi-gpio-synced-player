#!/bin/bash

autostartFile="/etc/xdg/lxsession/LXDE-pi/autostart"
autostartScript="lxterm-wrapper.sh"

### Init some variables
autostartSciptLocation="$PWD/$autostartScript"

# exit if not running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root. Exiting." 
   exit 1
fi

# Check if autostart script exists in the expected location
if [ ! -f "$autostartSciptLocation" ]; then
    echo "No autostart script where expected: $autostartSciptLocation. Exiting."
    exit 1
fi

# Check if autostart file contains the player command
if grep -q "$autostartScript" "$autostartFile"; then
    echo "Autostart file already contains the player command. Exiting."
    exit 1
fi

# Copy the player autostart command file to the autostart file
echo "Adding player autostart command to autostart file."

autostartLine="@$autostartSciptLocation"

# Note - adds a newline at the end. This is intentional.
echo "$autostartLine" >> "$autostartFile"

# Check if the player autostart command was added to the autostart file
if grep -q "$autostartScript" "$autostartFile"; then
    echo "Player autostart command added to autostart file."
else
    echo "Error: Player autostart command not added to autostart file. Exiting."
    exit 1
fi
