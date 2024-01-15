#!/bin/bash

autostartFile="/etc/xdg/lxsession/LXDE-pi/autostart"
playerAutostartCommandFile=lxde-autostart

# exit if not running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root. Exiting." 
   exit 1
fi

# Check if autostart file exists
if [ ! -f "$autostartFile" ]; then
    echo "Autostart file not found. Exiting."
    exit 1
fi

# Check if autostart file contains the player command
if grep -q "pi-gpio-synced-player" "$autostartFile"; then
    echo "Autostart file already contains the player command. Exiting."
    exit 1
fi

# Check if the player autostart command file exists
if [ ! -f "$playerAutostartCommandFile" ]; then
    echo "Player autostart command file not found. Exiting."
    exit 1
fi

# Copy the player autostart command file to the autostart file
cat "$playerAutostartCommandFile" >> "$autostartFile"
