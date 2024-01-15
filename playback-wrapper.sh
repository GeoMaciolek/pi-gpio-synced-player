#!/bin/bash
playerLocation="$HOME/Downloads/pi-gpio-synced-player"

# Seconds of wait tine before playback starts automatically
waitTime=30
playerCommand="python pi-gpio-synced-player.py"

echo -e "
                           [ Playback starts in $waitTime seconds. ]
+-------------+-----------------------------------------------------------------+
| Start Now   | Press any key.                                                  |
| Cancel/Exit | Press [ Q ] or Ctrl+C to exit / prevent the player from loading |
+-------------+-----------------------------------------------------------------+

Playback Wrapper Script (this): $0
Player Location:                $playerLocation
Player Command:                 $playerCommand
"

# waits for a keypress, or the timeout being reached
read -r -s -t "$waitTime" -n1 input
if [[ $input = "q" ]] || [[ $input = "Q" ]]; then
    echo -e "\nExiting."
    exit 0
fi

echo -e "\nStarting player."
cd "$playerLocation" || exit 1
eval "$playerCommand"

echo -e "\nPlayback finished. Closing in 60 sec"
sleep 60
