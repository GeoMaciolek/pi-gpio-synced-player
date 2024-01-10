ver = 'pi-gpio-synced-player.py 0.5 - mpv edition'

import time
import mpv

# Set to True to skip GPIO etc - for testing NOT on a pi
TEST_MODE = False

############################
### Application Settings ###

# Set to "primary" for main / controller, or "secondary" for the listener units
mode = 'primary'

# Filename to play
media_file = 'your_media_file.mp4'
# Other examples:
# mfile = 'rem/synctest2.mp4'
# mfile = 'bbb.mp4'

# Loop forever? Except for testing, set to: True 
play_forever = True

# For testing - playback loop count
playback_count = 3

# On-screen Time/playback Display Enabled? Normally set: False
osd_enabled = True

# What GPIO pins are used for the main/secondary communication
gpio_listen_pin = 4     # note - 3 has internal pull-up resistor, 4 has pull-down resistor
gpio_transmit_pins = [17,27,22] # set as a list - can have only one member, though, if only one needed

# delay after initial load command before pause  
load_wait_duration = 2

if not TEST_MODE:
    import RPi.GPIO as GPIO


### End Application Settings ###
################################

def vid_pauseplay():
    print('send_key(" ")')

def vid_rewind():
    print('send_key("i")')

def vid_quit():
    print('send_key("q")')

# Reset to start - assumes video is playing, and leaves it paused after
def wait_for_gpio():
    if TEST_MODE:
        print('[TEST MODE] Waiting for a rising pin (just sleep 5).')
        time.sleep(5)
        print('We got a rising pin!')
    else:
        print('Waiting for a rising pin.')
        GPIO.wait_for_edge(gpio_listen_pin, GPIO.RISING)
        print('We got a rising pin!') 

def gpio_setup_transmit_pins():
    # Set up the pins for the main/secondary communication
    if not TEST_MODE:
        for gpio_transmit_pin in gpio_transmit_pins:
            GPIO.setup(gpio_transmit_pin, GPIO.OUT, initial=GPIO.LOW)
    else:
        print("[TEST MODE] We would be initing the GPIO pins.")


def gpio_initialize():
    if not TEST_MODE:
        GPIO.setmode(GPIO.BCM)
    else:
        print("[TEST MODE] We would be setting the GPIO mode.")

def gpio_close():
    if not TEST_MODE:
        GPIO.cleanup()
    else:
        print("[TEST MODE] We would be closing the GPIO pins.")

def gpio_send_pin_high():
    if not TEST_MODE:
        for gpio_transmit_pin in gpio_transmit_pins:
            GPIO.output(gpio_transmit_pin, GPIO.HIGH)
    else:
        print("[TEST MODE] We would be setting the GPIO pins high.")

def gpio_send_pin_low():
    if not TEST_MODE:
        for gpio_transmit_pin in gpio_transmit_pins:
            GPIO.output(gpio_transmit_pin, GPIO.LOW)
    else:
        print("[TEST MODE] We would be setting the GPIO pins low.")

def setup_gpio_listen_pin():
    if not TEST_MODE:
        # GPIO.setup(gpio_listen_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(gpio_listen_pin, GPIO.IN, GPIO.PUD_DOWN)
    else:
        print("[TEST MODE] We would be setting up the GPIO listen pin.")

def player_launch():
    """launch the media player

    Returns:
        mpv.Context: the player context
    """
    try:
        player = mpv.Context()
    except mpv.MPVError:
        print('failed creating context')
        return 1
    
    player.set_option('input-default-bindings')
    if osd_enabled:
        player.set_option('osc')
    player.set_option('input-vo-keyboard')
    player.set_option('loop', 'yes')
    player.set_option('pause') # start playback paused
    player.initialize()

    return player

def player_open_file(player, input_file):
    print(f'player.play({input_file})')
    player.command('loadfile', input_file)

def player_reset_to_start(player):
    print('Resetting to start')
    player.set_option('pause', 'yes')
    player.command('seek','0','absolute')

def player_resume(player):
    print('Resuming playback')
    player.set_option('pause', 'no')

def player_start_at_beginning(player):
    print("Starting playback at beginning: player_reset_to_start(), then player_resume()")
    player_reset_to_start(player=player)
    player_resume(player=player)

def player_wait_for_end(player):
    print('Waiting...')
    while player.get_property('time-pos') < (player.get_property('duration')-0.3):
        time.sleep(0.1)
        # print(player.get_property('time-pos'))

    # while True:
        # event = player.wait_event(.01)
        # if event.id == mpv.Events.none:
        #     continue
        # print(f"mpv event: {event.name}")
        # if event.id in [mpv.Events.end_file, mpv.Events.shutdown]:
        #     return True


# Intialize pi GPIO
gpio_initialize()

print(f'{ver} in mode: {mode}')

count = 0

if mode == 'primary':

    print('++++ Loading ++++')
    gpio_setup_transmit_pins()
    print('Note: to terminate prematurely, hit [q] in the video player, and Control-C at the text screen')
    time.sleep(2)

#    # Set Pin 2 ito High
#    GPIO.output(gpio_transmit_pin, GPIO.HIGH)
#
    # Load file
    player = player_launch()
    player_open_file(player=player, input_file=media_file)

    # Wait for file to load / buffer
    time.sleep(load_wait_duration)      # [5] sec
    
    # Begin standard playback loop
    while (count <= playback_count) or play_forever:
                                                                    
        # Pins to high - 2nd trigger
        gpio_send_pin_high()

        player_start_at_beginning(player=player)

        # Pins to low (will include the [1 sec] delay of keypress
        gpio_send_pin_low()

        print('Waiting for the end of the video...')
        player_wait_for_end(player=player)
        print('Video has ended!')

        count += 1

    # Cleanup pins(during testing etc)
    gpio_close()
    vid_quit()

# Otherwise, run as secondary
elif mode == 'secondary':
    # Set up listening pin
    setup_gpio_listen_pin()
    # Initialize (load, reset to start)
    player = player_launch()
    player_open_file(player=player, input_file=media_file)

    # Wait for file to load / buffer
    time.sleep(load_wait_duration - 1)      # [5 - 1] sec


    print('++++ Prepared to start ++++')

    # Begin standard playback loop
    while (count <= playback_count) or play_forever:
        # Wait for RISE (GPIO going High on Main)
        wait_for_gpio()
        player_start_at_beginning(player=player)

    gpio_close()
    vid_quit()

else:
    print(f"Mode should be set to 'primary' or 'secondary', not {mode}")

print('++++ End ++++')
print('Note: if keyboard is not working, hit Control-C, then type "reset" and hit enter')
