ver = 'PYTHON 3 - Master/slave with pause rew play, no-osd.'

import RPi.GPIO as GPIO
import time
import os
import keyboard

############################
### Application Settings ###

# Set to "primary" for main / controller, or "secondary" for the listener units
mode = 'secondary'

# Filename to play
mfile = 'trim2.mp4'

# File Length - set to 0 if not used!
length_hours = 0
length_minutes = 0
length_seconds = 20

# Loop forever? Except for testing, set to: True 
play_forever = False

# For testing - playback loop count
playback_count = 3

# On-screen Time/playback Display Enabled? Normally set: False
osd_enabled = True

# What GPIO pins are used for the main/secondary communication
gpio_listen_pin = 4     # note - 3 has internal pull-up resistor, 4 has pull-down resistor
gpio_transmit_pins = [17,27,22] # set as a list - can have only one member, though, if only one needed

# delay after initial load command before pause  
load_wait_duration = 2
keyboard_pause_duration = 0.5     # delay between trigger highs / lows

# Set the omx command line options
#   note: --loop is enabled to avoid having to reload
#   the file, but is NOT itself timing-accurate!
if osd_enabled:
     omx_cmd = 'omxplayer --loop ' + mfile
else:
    omx_cmd = 'omxplayer --loop --no-osd ' + mfile


### End Application Settings ###
################################

def send_key(key: str):
    keyboard.send(key)                  # Pause
    time.sleep(keyboard_pause_duration) # ... key wait [0.5] sec ...

def vid_pauseplay():
    send_key(" ")

def vid_rewind():
    send_key("i")

def vid_quit():
    send_key("q")

# Reset to start - assumes video is playing, and leaves it paused after
def vid_reset_to_start():
    vid_pauseplay()
    time.sleep(2)
    vid_rewind()


# Calculate loop time
# Loop time(in seconds) - set to length of file + 5
offset_duration = 4
loop_duration =(3600 * length_hours) +(60 * length_minutes) + length_seconds


# Intialize pi GPIO
GPIO.setmode(GPIO.BCM)

print(f'{ver} in mode: {mode}')

count = 0

if mode == 'primary':

    print('++++ Loading ++++')
    for gpio_transmit_pin in gpio_transmit_pins:
        GPIO.setup(gpio_transmit_pin, GPIO.OUT, initial=GPIO.LOW)
    print('Note: to terminate prematurely, hit [q] in the video player, and Control-C at the text screen')
    time.sleep(2)

#    # Set Pin 2 ito High
#    GPIO.output(gpio_transmit_pin, GPIO.HIGH)
#
    # Load file
    os.popen(omx_cmd)

    # Wait for file to load / buffer
    time.sleep(load_wait_duration)      # [5] sec
    
    vid_pauseplay() 
    vid_reset_to_start()
    time.sleep(2)

#            # (total wait time from above w/pin HIGH: 6 sec [load_wait_duration + keyboard_pause_duration])
#
#    # Set Pin 2 to low(off)
#    GPIO.output(gpio_transmit_pin, GPIO.LOW)
#    time.sleep(keyboard_pause_duration+1)

    # Begin standard playback loop
    while (count <= playback_count) or play_forever:
                                                                    
        # Pins to high - 2nd trigger
        for gpio_transmit_pin in gpio_transmit_pins:
            GPIO.output(gpio_transmit_pin, GPIO.HIGH)

        vid_pauseplay() # Start Playback

        # Pin2 to low (will include the [1 sec] delay of keypress
        for gpio_transmit_pin in gpio_transmit_pins:
            GPIO.output(gpio_transmit_pin, GPIO.LOW)

        time.sleep(loop_duration)

        vid_reset_to_start()

        count += 1

    # Cleanup pins(during testing etc)
    GPIO.cleanup()
    vid_quit()

# Otherwise, run as secondary
elif mode == 'secondary':
    # Set up listening pin
    GPIO.setup(gpio_listen_pin, GPIO.IN, GPIO.PUD_DOWN)
    # Initialize (load, reset to start)
    print("os.popen(omx_cmd)                          # LOAD file")

    # Wait for file to load / buffer
    time.sleep(load_wait_duration - 1)      # [5 - 1] sec
    
    vid_pauseplay()
    vid_reset_to_start()
    time.sleep(1)

    print('++++ Waiting for start ++++')

    # Begin standard playback loop
    while (count <= playback_count) or play_forever:

        print('Waiting for a rising pin.')
        # Wait for RISE (GPIO going High on Main)
        GPIO.wait_for_edge(gpio_listen_pin, GPIO.RISING)                        # Detect RISE
        print('We got a rising pin!') 
        vid_pauseplay()

        # Wait for loop to finish before allowing video to restart
        time.sleep(loop_duration)

        # Jump to beinning to wait for pin/start.
        vid_reset_to_start()
    GPIO.cleanup()
    vid_quit()

else:
    print(f"Mode should be set to 'primary' or 'secondary', not {mode}")

print('++++ End ++++')
print('Note: if keyboard is not working, hit Control-C, then type "reset" and hit enter')



