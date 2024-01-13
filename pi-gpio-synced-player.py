ver = 'pi-gpio-synced-player.py 0.6.1 - vlc edition'


#############
#
# TODO
#
# * Change pin logic
# When pin goes high, pause, reset time to beginning
# When pin goes low, resume playback
#
# this may require the use of callbacks, and `darksidesync` module`



import time
import vlc
import configparser
import inspect # For debugging (identify calling function)

from datetime import datetime, timedelta
from pprint import pprint

############################
### Application Settings ###

CONFIG_FILE = 'pi-gpio-synced-player.ini'

# Set to "primary" for main / controller, or "secondary" for the listener units
MODE_DEFAULT = 'primary'

# MEDIA_FILE - no default is included, this must be specified in the
# pi-gpio-synced-player.ini file

# Set to True to skip GPIO etc - for testing NOT on a pi
TEST_MODE_FAKE_GPIO_DEFAULT = False

# Set to True to run in fullscreen mode
FULLSCREEN_MODE_DEFAULT = True

# Loop forever? Except for testing, set to: True 
PLAY_FOREVER_DEFAULT = True

# For testing - playback loop count
PLAYBACK_COUNT_DEFAULT = 3

# What GPIO pins are used for the main/secondary communication
GPIO_LISTEN_PIN_DEFAULT = 4     # note - 3 has internal pull-up resistor, 4 has pull-down resistor
GPIO_TRANSMIT_PINS_DEFAULT = [17,27,22] # set as a list - can have only one member, though, if only one needed

# How long to let the media play after initially loading the file (to get the duration.) Minimum of 0.5 recommended
PLAYBACK_AFTER_LOAD_DURATION_SEC_DEFAULT: float = 0.5 

# How long to keep the GPIO pins high (in seconds)
PIN_TX_DURATION_SEC_DEFAULT: float = 2.0

# delay (in seconds) after initial load command before pause. MUST BE AT LEAST 1 SECOND!
LOAD_WAIT_DURATION_DEFAULT = 2

# On-screen Time/playback Display Enabled? Normally set: False
osd_enabled = True

### End Application Settings ###
################################

def timestamp():
    return datetime.now().strftime("%H:%M:%S.%f")[:11]

def dprint(msg: str = None):
    """Prints a message with a timestamp & the calling function name.

    If no message is provided, only the timestamp & function name are printed.

    Args:
        msg (str): The message to print (optional)
    """
    module_name = str(inspect.stack()[1][3])
    # module_name = str(inspect.stack()[1].function)
    if module_name == '<module>':
        module_name = 'MAIN'
    debug_msg = f'[{timestamp()} {MODE[:3]}] {module_name}()'
    if msg:
        debug_msg += f': {msg}'

    print(debug_msg)

def config_split_list(configstring: str, delimiter: str = ',', cast_to_int: bool = True) -> list:
    """Splits a config string into a list, using the specified delimiter

    Args:
        configstring (str): The string to split
        delimiter (str, optional): The delimiter to split on. Defaults to ','.

    Returns:
        list: The list of strings
    """

    output_list = []
    for x in configstring.split(delimiter):
        if cast_to_int:
            output_list.append(int(x.strip()))
        else:
            output_list.append(x.strip())

    return(output_list)

def vid_quit(vlc_player, instance):
    dprint('vid_quit() called. calling vlc_player.stop() & waiting 1 second')
    vlc_player.stop()
    time.sleep(1)
    dprint('calling vlc_player.release()')
    vlc_player.release()
    dprint('calling instance.release()')
    instance.release()

    dprint('Player and Instance have been released; exiting vid_quit()')

# Reset to start - assumes video is playing, and leaves it paused after
def wait_for_gpio(gpio_listen_pin: int, debug_mode_sleep_sec: int = 6):
    """Waits for a GPIO pin to go high (rising edge)

    Args:
        gpio_listen_pin (int, optional): The GPIO pin to listen on. Defaults to (global) gpio_listen_pin. TODO: FIX GLOBALS
        debug_mode_sleep_sec (int, optional): How long to sleep in debug mode. Defaults to 6.
    """
    if TEST_MODE_FAKE_GPIO:
        dprint('TEST MODE, "Waiting for a rising pin" (just sleep 5)')
        time.sleep(debug_mode_sleep_sec)
        dprint(f'We got a (fake) rising pin!')
    else:
        dprint(f'Waiting for a rising pin: {gpio_listen_pin}.')
        GPIO.wait_for_edge(gpio_listen_pin, GPIO.RISING)
        dprint('We got a rising pin!') 

def gpio_setup_transmit_pins():
    # Set up the pins for the main/secondary communication
    if not TEST_MODE_FAKE_GPIO:
        for gpio_transmit_pin in GPIO_TRANSMIT_PINS:
            dprint(f"setting up pin {gpio_transmit_pin} as output, default to LOW")
            GPIO.setup(gpio_transmit_pin, GPIO.OUT, initial=GPIO.LOW)
    else:
        dprint("[TEST MODE] - We would be setting up all transmit pins")


def gpio_initialize():
    if not TEST_MODE_FAKE_GPIO:
        dprint("Initializing GPIO interface, GPIO.setmode(GPIO.BCM)")
        GPIO.setmode(GPIO.BCM)
    else:
        dprint("[TEST MODE] We would be setting the GPIO mode.")

def gpio_close():
    if not TEST_MODE_FAKE_GPIO:
        dprint("Closing GPIO interface: GPIO.cleanup()")
        GPIO.cleanup()
    else:
        dprint("[TEST MODE] We would be closing the GPIO pins.")

def gpio_send_pin_high():
    if not TEST_MODE_FAKE_GPIO:
        for gpio_transmit_pin in GPIO_TRANSMIT_PINS:
            dprint(f"Set pin {gpio_transmit_pin} to HIGH")
            GPIO.output(gpio_transmit_pin, GPIO.HIGH)
    else:
        dprint("[TEST MODE] We would be setting the GPIO pins high.")

def gpio_send_pin_low():
    if not TEST_MODE_FAKE_GPIO:
        for gpio_transmit_pin in GPIO_TRANSMIT_PINS:
            dprint("Setting pin {gpio_transmit_pin} to LOW")
            GPIO.output(gpio_transmit_pin, GPIO.LOW)
    else:
        dprint("[TEST MODE] We would be setting the GPIO pins low.")

def setup_gpio_listen_pin():
    if not TEST_MODE_FAKE_GPIO:
        # GPIO.setup(gpio_listen_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        dprint(f"Setting up pin {GPIO_LISTEN_PIN} as input, with pull-down resistor enabled")
        GPIO.setup(GPIO_LISTEN_PIN, GPIO.IN, GPIO.PUD_DOWN)
    else:
        dprint("[TEST MODE] We would be setting up the GPIO listen pin.")

def player_launch(media_file:str, set_playback_count=1) -> (vlc.MediaPlayer, vlc.Instance, vlc.Media):
    """launch the media player

    Args:
        media_file (str): The file to play.
        set_playback_count (int, optional): The number of times to play the media. Defaults to 1.

    Returns:
        (vlc.MediaPlayer, vlc.Instance, vlc.Media, duration [int]): a tuple of the player, instance, and media
    """
    dprint('Intializing VLC instance, player, and media, and loading media')
    try:

        # creating a vlc instance - with a LONG repeat number
        vlc_instance = vlc.Instance(f'--input-repeat={set_playback_count}')
     
        # creating a media player
        vlc_player = vlc_instance.media_player_new()

        # load the media (and return the media object)
        vlc_media = player_open_file(instance=vlc_instance, player=vlc_player, input_file=media_file)

    except vlc.VLCException as e:
        dprint('Failed creating VLC context, error:')
        dprint(e)
        return 1
    
    if FULLSCREEN_MODE:
        vlc_player.set_fullscreen(1)

    # Play a little bit to get the duratioN!    
    dprint('Playing briefly, to get video duration.')
    vlc_player.play()
    time.sleep(PLAYBACK_AFTER_LOAD_DURATION_SEC)
    vlc_player.pause()
    
    dprint('Done with brief playback, retrieving media duration.')

    media_duration = vlc_media.get_duration()
    dprint(f'vlc_media.get_duration() returned {media_duration}ms [{timedelta(milliseconds=media_duration)}]')

    
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
    # print(f'player_open_file([player], {input_file})')

    media = instance.media_new(input_file)

    player.set_media(media)

    return media

def player_reset_to_start(player: vlc.MediaPlayer):
    dprint('Resetting to start [player.set_time(0)]')
    player.set_time(0)
    dprint('Done, time reset.')

def player_pause(player: vlc.MediaPlayer):
    dprint('Pausing playback.')
    player.pause()
    dprint('(Pause function complete)')

def player_prepare_to_restart(player: vlc.MediaPlayer):
    dprint('Preparing to restart playback')
    player_pause(player=player)
    player_reset_to_start(player=player)

def player_resume(player):
    dprint('Resuming playback [calling player.play()]')
    playing_status = player.get_state()
    player.play()

def player_start_at_beginning(player):
    dprint("Starting playback at beginning: player_reset_to_start(), then player_resume()")
    player_reset_to_start(player=player)
    if player.get_state() != vlc.State.Playing:
        dprint(f'Playback is not currently playing (State: {player.get_state()})')
        player_resume(player=player)

def player_wait_for_end(player: vlc.MediaPlayer, duration: int,
                        ms_before_end_to_stop: float = 600,
                        wait_state_ms: int  = 200,
                        debug_message_frequency_sec: int = 5):
    """
    This function waits until the media player is near the end of the media
    file, printing diagnostic messages every 5 seconds (by default).

    Args:
        player (vlc.MediaPlayer): The media player instance.
        duration (int): The total duration of the media file in ms.
        ms_before_end_to_stop (float, optional): How many ms before the end of the media file to stop. Default: 600
        wait_state_ms (int, optional): How many ms to wait between checks. Default: 200
        debug_message_frequency_sec (int, optional): Print debug msgs every __ seconds. Defaults to 5. 0 to disable

    """

    # checks current time/pos of media player, compares  w/the specified duration
    # If current time is less than the duration minus a small buffer (three times the wait state), 
    # pause execution for a short period (defined by wait_state_ms) and check again.

    dprint('##### Beginning player_wait_for_end()  #####')
    
    # Always ensure we stop at least 3 wait states from the end of the video
    if ms_before_end_to_stop > wait_state_ms * 3:
        near_the_end = duration - ms_before_end_to_stop
    else:
        near_the_end = duration - (wait_state_ms * 3)

    dprint(f'near_the_end = duration - (wait_state_ms*3)')
    dprint(f'{near_the_end} = {duration} - ({wait_state_ms}*3)')

    debug_line_count = 0
    lines_to_skip_between_print = (debug_message_frequency_sec * 1000) // wait_state_ms
    # lines_to_skip_between_print = 0

    # dprint('lines_to_skip_between_print = debug_message_frequency_ms // wait_state_ms')
    # dprint(f'{lines_to_skip_between_print} = {debug_message_frequency_ms} // {wait_state_ms}')

    readable_duration = str(timedelta(seconds=duration // 1000))

    current_time = player.get_time()
    current_time_seconds = current_time // 1000 
    while current_time < near_the_end:
        # Only print debugging stuff if debug_message_frequency_sec is enabled (ie  not 0)
        if debug_message_frequency_sec != 0:
            if debug_line_count == 0:

                current_time_seconds = current_time // 1000 
                current_playback_timestamp = str(timedelta(seconds=current_time_seconds))

                percent_complete = int((current_time / duration) * 100)
                dprint(f'Waiting for playback to finish. [{current_playback_timestamp} / {readable_duration}] ({percent_complete}%)')
            if debug_line_count >= lines_to_skip_between_print:
                debug_line_count = 0
            else:
                debug_line_count += 1

        # dprint('All playback loops complete!')
        time.sleep(wait_state_ms / 1000)
        current_time = player.get_time()


    dprint('#### End of video player_wait_for_end() ####')


################################
# Begin Main Application Logic #
################################

# Load configuration options
config_parsed = configparser.ConfigParser()
config_parsed.read(CONFIG_FILE)

# Check for media file - exit if none is specified
if not config_parsed.has_option('Video', 'MediaFile'):
    print(f'ERROR: No media file specified in {CONFIG_FILE}')
    exit(1)

conf = {
    #     # Video
    'MEDIA_FILE': config_parsed.get('Video', 'MediaFile'),
    'FULLSCREEN_MODE': config_parsed.getboolean('Video', 'Fullscreen', fallback=FULLSCREEN_MODE_DEFAULT),
    'PLAY_FOREVER': config_parsed.getboolean('Video', 'PlayForever', fallback=PLAY_FOREVER_DEFAULT),
    'PLAYBACK_COUNT': config_parsed.getint('Video', 'PlaybackCount', fallback=PLAYBACK_COUNT_DEFAULT),

    # Sync
    'MODE': config_parsed.get('Sync', 'SyncMode', fallback=MODE_DEFAULT),
    # Split the below into a list
    'GPIO_TRANSMIT_PINS': config_split_list(config_parsed.get('Sync', 'TransmitPins', fallback=','.join(str(x) for x in GPIO_TRANSMIT_PINS_DEFAULT))),
    'GPIO_LISTEN_PIN': int(config_parsed.get('Sync', 'ListenPin', fallback=GPIO_LISTEN_PIN_DEFAULT)),
    'LOAD_WAIT_DURATION': config_parsed.getfloat('Sync', 'LoadWaitDuration', fallback=LOAD_WAIT_DURATION_DEFAULT),
    'PIN_TX_DURATION_SEC': config_parsed.getfloat('Sync', 'PinTxDurationSec', fallback=PIN_TX_DURATION_SEC_DEFAULT),

    # Advanced
    'PLAYBACK_AFTER_LOAD_DURATION_SEC': config_parsed.getfloat('Advanced', 'PlaybackAfterLoadDurationSec', fallback=PLAYBACK_AFTER_LOAD_DURATION_SEC_DEFAULT),

    # Debug
    'TEST_MODE_FAKE_GPIO': config_parsed.getboolean('Debug', 'FakeGPIO', fallback=TEST_MODE_FAKE_GPIO_DEFAULT),
    # 'osd_enabled': config_parsed.getboolean('video', 'osd_enabled', fallback=osd_enabled)
    # }
}

# Video
MEDIA_FILE = conf['MEDIA_FILE']
LOAD_WAIT_DURATION = conf['LOAD_WAIT_DURATION']
FULLSCREEN_MODE = conf['FULLSCREEN_MODE']
PLAY_FOREVER = conf['PLAY_FOREVER']
PLAYBACK_COUNT = conf['PLAYBACK_COUNT']

# Sync
MODE = conf['MODE']
GPIO_TRANSMIT_PINS = conf['GPIO_TRANSMIT_PINS']
GPIO_LISTEN_PIN = conf['GPIO_LISTEN_PIN']
LOAD_WAIT_DURATION = conf['LOAD_WAIT_DURATION']
PIN_TX_DURATION_SEC = conf['PIN_TX_DURATION_SEC']

# Advanced
PLAYBACK_AFTER_LOAD_DURATION_SEC = conf['PLAYBACK_AFTER_LOAD_DURATION_SEC']

# Debug
TEST_MODE_FAKE_GPIO = conf['TEST_MODE_FAKE_GPIO']
PIN_TX_DURATION_SEC = conf['PIN_TX_DURATION_SEC']

dprint('Configuration loaded from file:')
pprint(conf)


# Initialize pi GPIO

if not TEST_MODE_FAKE_GPIO:
    import RPi.GPIO as GPIO

gpio_initialize()

dprint(f'{ver} in mode: {MODE}')

current_playback_count = 1

if PLAY_FOREVER:
    set_playback_count = 65535
else:
    set_playback_count = PLAYBACK_COUNT

# Initialize player (regardless of primary or secondary mode)
player, instance, media, duration = player_launch(media_file=MEDIA_FILE, set_playback_count=set_playback_count)

dprint('Player init should be done')

# print(player)
# print(instance)

if MODE == 'primary':

    dprint('Primary mode initializing.')
    gpio_setup_transmit_pins()
    print('\n\nNote: to terminate prematurely, hit [Control]-[C] at the text screen. ([f] to  exit fullscreen, and/or [alt]-[tab] to switch windows)\n\n')

    # Wait for file to load / buffer
    dprint(f'Sleeping for {LOAD_WAIT_DURATION} sec. for file to load / buffer')
    time.sleep(LOAD_WAIT_DURATION)      # (2 sec by default)
    
    # Begin standard playback loop
    while (current_playback_count <= PLAYBACK_COUNT) or PLAY_FOREVER:
        dprint(f'Video playback count: {current_playback_count}/{PLAYBACK_COUNT}')
                                                                    
        # Pins to high - 2nd trigger
        gpio_send_pin_high()
        player_prepare_to_restart(player=player)

        # Pins to low
        time.sleep(PIN_TX_DURATION_SEC)
        gpio_send_pin_low()
        player_resume(player=player)

        dprint(f'Waiting for the end of the video...')
        player_wait_for_end(player=player, duration=duration, ms_before_end_to_stop=3000)
        dprint(f'player_wait_for_end() returned - Video has ended!')

        current_playback_count += 1

    dprint(f'We have played the number of times specified ({PLAYBACK_COUNT}), exiting media player')
    vid_quit(vlc_player=player, instance=instance)
    
    gpio_close() # Cleanup pins

# Otherwise, run as secondary
elif MODE == 'secondary':
    # Set up listening pin
    setup_gpio_listen_pin()

  
    # Wait for file to load / buffer, one second shorter than the primary
    dprint(f'Sleeping for {LOAD_WAIT_DURATION - 1} seconds, for file to load / buffer (1 sec shorter than primary)')
    time.sleep(LOAD_WAIT_DURATION - 1)      # [2 - 1] seconds by default
    dprint('Prepared to start (as secondary)')

    # Begin standard playback loop
    while (current_playback_count <= PLAYBACK_COUNT) or PLAY_FOREVER:
        # Wait for RISE (GPIO going High on Main)

        # wait_for_gpio(gpio_listen_pin=GPIO_LISTEN_PIN)
        # player_start_at_beginning(player=player)
        dprint(f'Waiting for the end of the video...')
        player_wait_for_end(player=player, duration=duration, ms_before_end_to_stop=1000)
        dprint(f'player_wait_for_end() returned - Video has ended!')


    gpio_close()
    vid_quit(vlc_player=player, instance=instance)

else:
    print(f"ERROR: Mode should be set to 'primary' or 'secondary', not {MODE}")
    exit

dprint('Script complete, exiting.\r\rNote: if keyboard is not working, hit Control-C, then type "reset" and hit enter')
