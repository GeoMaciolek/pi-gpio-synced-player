#!/bin/bash
playerLocation="$HOME/Downloads/pi-gpio-synced-player"

# Seconds of wait tine before playback starts automatically
waitTime=30
# Run the player twice (with a 10 second delay between) to work around the "fullscreen issue?"
briefInitialPlayback=true
# How long to wait during the above initial playback phase - happens 3x?
sleepTime=3
playerCommand="sleep 200"
# playerCommand="python pi-gpio-synced-player.py"

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
    playerPid="$!"
    echo "Player launched (pid $playerPid), waiting 15 sec"
    sleep 15
    echo "Kill pid $playerPid:"
    kill "$playerPid"
    sleep 1
    echo "Kill -9 pid $playerPid:"
    kill -9 "$playerPid"
    sleep 1
    exit 1
    # echo "Player launched (pid $playerPid), waiting $sleepTime sec"
    # sleep "$sleepTime"
    # echo "Killing pid $playerPid"
    # kill "$playerPid"
    # echo "Sleeping another $sleepTime sec"
    # sleep "$sleepTime"
    # echo "Killing player (kill -9 $playerPid)"
    # kill -9 "$!"
    # echo "Player terminated, waiting one last $sleepTime sec"
    # sleep "$sleepTime"
    # echo "..."
    # sleep "$sleepTime"
    # echo "..."
    # sleep "$sleepTime"
    # echo "..."
    # sleep "$sleepTime"
fi

echo -e "\nStarting player."
cd "$playerLocation" || exit 1
eval "$playerCommand"

echo -e "\nPlayback finished. Closing in 60 sec"
sleep 60
