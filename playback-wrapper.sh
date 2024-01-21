#!/bin/bash
playerLocation="$HOME/Downloads/pi-gpio-synced-player"

# Seconds of wait tine before playback starts automatically
waitTime=30
# Run the player twice (with a 10 second delay between) to work around the "fullscreen issue?"
briefInitialPlayback=true
# How long to wait during the above initial playback phase - happens 3x?
sleepTime=7
playerCommand="python pi-gpio-synced-player.py"

echo -e "
                           [ Playback starts in $waitTime seconds. ]
+-------------+-----------------------------------------------------------------+
| Start Now   | Press any key.                                                  |
| Cancel/Exit | Press [ Q ] or Ctrl+C to exit / prevent the player from loading |
+-------------+-----------------------------------------------------------------+"

if [ "$briefInitialPlayback" = true ]; then
    echo -e "Note: playback will appear to start, then terminate, then start a second time.
This is expected behavior as part of the 'fullscreen issue workaround.'"
fi

echo -e "
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

# Launches the player in the background, waits X seconds, terminates it, continues
if [ "$briefInitialPlayback" = true ]; then
    echo -e "\nStarting player (temporary/brief)."
    cd "$playerLocation" || exit 1
    eval "$playerCommand" &
    echo "Player launched, waiting"
    sleep "$sleepTime"
    kill "$!"
    sleep "$sleepTime"
    kill -9 "$!"
    echo "Player terminated, waiting"
    sleep "$sleepTime"
fi

echo -e "\nStarting player."
cd "$playerLocation" || exit 1
eval "$playerCommand"

echo -e "\nPlayback finished. Closing in 60 sec"
sleep 60
