#!/bin/bash

autostartWrapperScript="lxterm-wrapper.sh"
playbackWrapperScript="playback-wrapper.sh"
# OS Specific files
lxdeAutostartFile="/etc/xdg/lxsession/LXDE-pi/autostart"

wayfireAutostartFile="$HOME/.config/wayfire.ini"
# Player name used in wayfire.ini
playerName="wavesplayer"

### Init some variables

autostartWrapperScriptLocation="$PWD/$autostartWrapperScript"
playbackWrapperScriptLocation="$PWD/$playbackWrapperScript"

failMsg='Autostart setup FAILED.'

# Identify suppurted Raspbian versions
case $(cat /etc/debian_version) in
11.*) VERSION=11;;
12.*) VERSION=12;;
*) VERSION=OTHER;;
esac

if [ "$VERSION" = "OTHER" ]; then
    echo "This script is only for Raspbian 11 (Bullseye) and 12 (Bookworm). $failMsg"
    exit 1
fi

# exit if running as root
if [[ $EUID -eq 0 ]]; then
   echo "This script must be run as a standard user, not root or with sudo. Exiting." 
   exit 1
fi

# Check if autostart script (to be installed) exists in the expected location
if [ -f "$autostartWrapperScriptLocation" ]; then
    echo "Error: Trying to generate autostart wrapper script, but existing script found"
    echo "where none expected: $autostartWrapperScriptLocation. $failMsg"
    exit 1
fi

#### Create lxterm wrapper ####
wrapperStart="lxterminal -l -e '"
wrapperEnd="; bash'"

wrapperCommand="$wrapperStart$playbackWrapperScriptLocation$wrapperEnd"
echo "Creating wrapper script: $autostartWrapperScriptLocation"
echo "      $wrapperCommand"
echo "$wrapperCommand" > "$autostartWrapperScriptLocation"

chmod +x "$autostartWrapperScriptLocation"


############################################################
### Raspberry Pi OS 11 (Bullseye) version (LXDE / lxsession)

if [ "$VERSION" = "11" ]; then
    echo "Installing autostart for Raspberry Pi OS 11 (Bullseye) (LXDE / lxsession)"

    # Check if lxde's autostart file exists
    if [ ! -f "$lxdeAutostartFile" ]; then
        echo "No LXDE autostart file where expected: $lxdeAutostartFile. $failMsg"
        exit 1
    fi


    # Check if autostart file contains the player command
    if grep -q "$autostartWrapperScript" "$lxdeAutostartFile"; then
        echo "Autostart file already contains the player / wrapaper command. $failMsg"
        exit 1
    fi

    # Copy the player autostart command file to the autostart file
    echo "Adding player autostart command to autostart file."

    autostartLine="@$autostartWrapperScriptLocation"

    # Note - adds a newline at the end. This is intentional.
    # echo "$autostartLine" >> "$lxdeAutostartFile"
    echo "$autostartLine" | sudo tee -a "$lxdeAutostartFile"

    # Check if the player autostart command was added to the autostart file
    if grep -q "$autostartWrapperScript" "$lxdeAutostartFile"; then
        echo "Player autostart command added to autostart file."
    else
        echo "Error: Player autostart command wasn't successfully appended to autostart file."
        echo "$failMsg"
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
        echo "No wayfire autostart file where expected: $wayfireAutostartFile."
        echo "System not configured for wayfire, or using some other autostart method?"
        echo "$failMsg"
        exit 1
    fi

    # If wayfire.ini file already has an our entry, exit
    if grep -q "$playerName" "$wayfireAutostartFile"; then
        echo "wayfire.ini file already has an entry for $playerName."
        echo "(Has this setup already been run?) $failMsg"
        exit 1
    fi

    wayfireLauncherLine="$playerName = $autostartWrapperScriptLocation"

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

echo "The script shouldn't  get here, so, if you see this, something went wrong. $failMsg"
exit 1