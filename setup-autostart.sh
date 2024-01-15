#!/bin/bash

autostartFile="/etc/xdg/lxsession/LXDE-pi/autostart"
playerAutostartCommandFile=lxde-autostart

playerAutostartCommandFileTemplate="$playerAutostartCommandFile-template"

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
if [ ! -f "$playerAutostartCommandFileTemplate" ]; then
    echo "Player autostart command file not found. Exiting."
    exit 1
fi

# Replace the tilde in the player autostart command file with the home directory
d=$'\03'
sed "s${d}\~${d}$HOME$d" < "$playerAutostartCommandFileTemplate" > "$playerAutostartCommandFile"


# Check if the modified player autostart command file exists
if [ ! -f "$playerAutostartCommandFile" ]; then
    echo "(Generated) player autostart command file not found. Exiting."
    exit 1
fi


# Copy the player autostart command file to the autostart file
echo "Adding player autostart command to autostart file."
cat "$playerAutostartCommandFile" >> "$autostartFile"



# Check if the player autostart command was added to the autostart file
if grep -q "pi-gpio-synced-player" "$autostartFile"; then
    echo "Player autostart command added to autostart file."
else
    echo "Error: Player autostart command not added to autostart file. Exiting."
    exit 1
fi
