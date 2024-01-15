#!/bin/bash

autostartScript="lxterm-wrapper.sh"
playbackWrapperScript="playback-wrapper.sh"
# OS Specific files
lxdeAutostartFile="/etc/xdg/lxsession/LXDE-pi/autostart"

wayfireAutostartFile="$HOME/.config/wayfire.ini"
# Player name used in wayfire.ini
playerName="wavesplayer"

### Init some variables

autostartSciptLocation="$PWD/$autostartScript"
playbackWrapperScriptLocation="$PWD/$playbackWrapperScript"


# Identify suppurted Raspbian versions
case $(cat /etc/debian_version) in
11.*) VERSION=11;;
12.*) VERSION=12;;
*) VERSION=OTHER;;
esac

if [ "$VERSION" = "OTHER" ]; then
    echo "This script is only for Raspbian 11 (Bullseye) and 12 (Bookworm). Exiting."
    exit 1
fi

# exit if running as root
if [[ $EUID -eq 0 ]]; then
   echo "This script must be run as a standard user, not root. Exiting." 
   exit 1
fi

# Check if autostart script (to be installed) exists in the expected location
if [ -f "$autostartSciptLocation" ]; then
    echo "Existing autostart script where none expected: $autostartSciptLocation. Exiting."
    exit 1
fi

#### Create lxterm wrapper ####
wrapperStart="lxterminal -l -e '"
wrapperEnd="; bash'"

wrapperCommand="$wrapperStart$playbackWrapperScriptLocation$wrapperEnd"
echo "Creating wrapper script: $autostartSciptLocation"
echo "      $wrapperCommand"
echo "$wrapperCommand" > "$autostartSciptLocation"

chmod +x "$autostartSciptLocation"


############################################################
### Raspberry Pi OS 11 (Bullseye) version (LXDE / lxsession)

if [ "$VERSION" = "11" ]; then
    echo "Installing autostart for Raspberry Pi OS 11 (Bullseye) (LXDE / lxsession)"

    # Check if lxde's autostart file exists
    if [ ! -f "$lxdeAutostartFile" ]; then
        echo "No LXDE autostart file where expected: $lxdeAutostartFile. Exiting."
        exit 1
    fi


    # Check if autostart file contains the player command
    if grep -q "$autostartScript" "$lxdeAutostartFile"; then
        echo "Autostart file already contains the player command. Exiting."
        exit 1
    fi

    # Copy the player autostart command file to the autostart file
    echo "Adding player autostart command to autostart file."

    autostartLine="@$autostartSciptLocation"

    # Note - adds a newline at the end. This is intentional.
    # echo "$autostartLine" >> "$lxdeAutostartFile"
    echo "$autostartLine" | sudo tee -a "$lxdeAutostartFile"

    # Check if the player autostart command was added to the autostart file
    if grep -q "$autostartScript" "$lxdeAutostartFile"; then
        echo "Player autostart command added to autostart file."
    else
        echo "Error: Player autostart command not added to autostart file. Exiting."
        exit 1
    fi
    echo "Installation of autostart complete"
    exit 0
fi

###################################################
### Raspberry Pi OS 12 (Bookworm) version (wayfire)

if [ "$VERSION" = "12" ]; then

    echo "Installing autostart for Raspberry Pi OS 12 (Bookworm) (wayfire)"

    # Check for wayfire autostart file
    if [ ! -f "$wayfireAutostartFile" ]; then
        echo "No wayfire autostart file where expected: $wayfireAutostartFile. Exiting."
        exit 1
    fi

    # If wayfire.ini file already has an our entry, exit
    if grep -q "$playerName" "$wayfireAutostartFile"; then
        echo "wayfire.ini file already has an entry for $playerName. Exiting."
        exit 1
    fi

    wayfireLauncherLine="$playerName = $autostartSciptLocation"

    # if wayfire.ini file already has an autostart section, insert line below it
    if grep -q "\[autostart\]" "$wayfireAutostartFile"; then
        echo "Adding line to existing [autpstart] section of $wayfireAutostartFile"
        sed -i "/\[autostart\]/a $wayfireLauncherLine" "$wayfireAutostartFile"
        exit 0
    else
        echo "Adding [autostart] section to $wayfireAutostartFile"
        echo -e "\n[autostart]" >> "$wayfireAutostartFile"
        echo "$wayfireLauncherLine" >> "$wayfireAutostartFile"
        exit 0
    fi
fi

echo "The script shouldn't  get here, so, if you see this, something went wrong. Exiting."
exit 1