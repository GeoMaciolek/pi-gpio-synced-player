ver = 'pi-gpio-synced-player.py 0.6 - vlc edition'

import time
import vlc

from datetime import datetime

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

def timestamp():
    return datetime.now().strftime("%H:%M:%S.%f")

def vid_quit(vlc_player):
    #print('send_key("q")')
    vlc_player.quit()

# Reset to start - assumes video is playing, and leaves it paused after
def wait_for_gpio():
    if TEST_MODE:
        print('[TEST MODE] Waiting for a rising pin (just sleep 5).')
        time.sleep(5)
        print(f'{timestamp()} - We got (fake) rising pin!')
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
        print(f"{timestamp()} - [TEST MODE] We would be setting the GPIO pins high.")

def gpio_send_pin_low():
    if not TEST_MODE:
        for gpio_transmit_pin in gpio_transmit_pins:
            GPIO.output(gpio_transmit_pin, GPIO.LOW)
    else:
        print(f"{timestamp()} - [TEST MODE] We would be setting the GPIO pins low.")

def setup_gpio_listen_pin():
    if not TEST_MODE:
        # GPIO.setup(gpio_listen_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(gpio_listen_pin, GPIO.IN, GPIO.PUD_DOWN)
    else:
        print("[TEST MODE] We would be setting up the GPIO listen pin.")

def player_launch(media_file:str, set_playback_count=1) -> (vlc.MediaPlayer, vlc.Instance, vlc.Media):
    """launch the media player

    Args:
        media_file (str): The file to play.
        set_playback_count (int, optional): The number of times to play the media. Defaults to 1.

    Returns:
        (vlc.MediaPlayer, vlc.Instance, vlc.Media, duration [int]): a tuple of the player, instance, and media
    """
    try:

        # creating a vlc instance - with a LONG repeat number
        vlc_instance = vlc.Instance(f'--input-repeat={set_playback_count}')
     
        # creating a media player
        vlc_player = vlc_instance.media_player_new()

        # load the media
        vlc_media = player_open_file(instance=vlc_instance, player=vlc_player, input_file=media_file)

    except vlc.VLCException as e:
        print('failed creating context')
        print(e)
        return 1
    
    vlc_player.set_fullscreen(1)

    # Play a little bit to get the duratioN!    
    vlc_player.play()
    time.sleep(0.1)
    vlc_player.pause()

    media_duration = vlc_media.get_duration()

    
    # if osd_enabled:
    #     player.set_option('osc')

    return vlc_player, vlc_instance, vlc_media, media_duration

def player_open_file(instance, player, input_file) -> vlc.Media:
    """_summary_

    Args:
        instance (vlc.Instance): the instance of the VLC module
        player (vlc.MediaPlayer): the player instance itself
        input_file (string): the filepath/filename of the file to play

    Returns:
        vlc.Media: media file (instance)
    """
    print(f'player_open_file([player], {input_file})')

    media = instance.media_new(input_file)

    player.set_media(media)

    return media

def player_reset_to_start(player: vlc.MediaPlayer):
    print('Resetting to start')
    player.set_time(0)
    print('time reset.')

def player_resume(player):
    print('Resuming playback')
    player.play()

def player_start_at_beginning(player):
    print("Starting playback at beginning: player_reset_to_start(), then player_resume()")
    player_reset_to_start(player=player)
    player_resume(player=player)

def player_wait_for_end(player: vlc.MediaPlayer, duration: int):
    """
    This function waits until the media player is near the end of the media file.

    Args:
        player (vlc.MediaPlayer): The media player instance.
        duration (int): The total duration of the media file in milliseconds.

    """

    # checks current time/pos of media player, compares  w/the specified duration
    # If current time is less than the duration minus a small buffer (three times the wait state), 
    # pause execution for a short period (defined by wait_state_ms) and check again.
    # print('Waiting...')
    wait_state_ms = 100
    near_the_end = duration - (wait_state_ms*3)
    while player.get_time() < near_the_end:
        time.sleep(wait_state_ms // 1000)

# Intialize pi GPIO
gpio_initialize()

print(f'{ver} in mode: {mode}')

count = 0

if play_forever:
    set_playback_count = 65535
else:
    set_playback_count = playback_count

print('Running player init')
# Initialize player (regardless of primary or secondary mode)
player, instance, media, duration = player_launch(media_file=media_file, set_playback_count=set_playback_count)

print('Player init should be done')

# Get file length in ms
# duration = media.get_duration()

print(f'{duration=}')
print(player)
print(instance)

print('sleeping after init')
time.sleep(3)
print('continuing')

if mode == 'primary':

    print('++++ Loading ++++')
    gpio_setup_transmit_pins()
    print('Note: to terminate prematurely, hit [q] in the video player, and Control-C at the text screen')
    time.sleep(2)

#    # Set Pin 2 ito High
#    GPIO.output(gpio_transmit_pin, GPIO.HIGH)

    # Wait for file to load / buffer
    time.sleep(load_wait_duration // 1000)      # [5] sec
    
    # Begin standard playback loop
    while (count <= playback_count) or play_forever:
                                                                    
        # Pins to high - 2nd trigger
        gpio_send_pin_high()

        print(f'{timestamp()} - launch: player_start_at_beginning()')
        player_start_at_beginning(player=player)
        print(f'{timestamp()} - end:    player_start_at_beginning()')
        # Pins to low
        time.sleep(0.5)
        gpio_send_pin_low()

        print(f'{timestamp()} - Waiting for the end of the video...')
        player_wait_for_end(player=player, duration=duration)
        print(f'{timestamp()} - Video has ended!')

        count += 1

    # Cleanup pins(during testing etc)
    gpio_close()
    vid_quit()

# Otherwise, run as secondary
elif mode == 'secondary':
    # Set up listening pin
    setup_gpio_listen_pin()

    # Wait for file to load / buffer
    time.sleep(load_wait_duration - 1)      # [5 - 1] sec


    print('Prepared to start (as secondary)')

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
