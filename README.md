# pi-gpio-synced-player

## Overview

A quick script to facilitate synchronized playback of video across multiple
Raspberry Pi units

### Why

This is a modification of a script written for a specific art installation. It
likely won't be broadly useful!

## Details

This script uses the `vlc` player, and the `python-vlc` Python module (for playback
control), with simple GPIO communications to ensure players start in sync.

## Wiring

![Pi 3B GPIO Pinout](assorted-resources/pinout.png)

## Usage

### Setup

Note - it would be better to use a `virtualenv`, but for the sake of simplicity
when running on a small embedded device like a pi only running one task, this
uses system-wide package installation.

#### Install vlc and python-vlc on each Pi

```bash
sudo apt update
sudo apt install vlc
sudo apt install python3-vlc
```

Note: on older (?) versions of raspbian, you may get an error about
`python3-vlc` not being installed. In that case (and **only** in that case),
run the following:

```bash
sudo pip3 install python-vlc
```


Copy the `pi-gpio-synced-player.example.conf` file to `pi-gpio-synced-player.conf`
and edit it to match your setup. (The most important lines are `MediaFile` and `PlayerMode`)

#### Install the script

Get up a terminal on each Pi, and clone the repo:

```bash
cd ~/Downloads
git clone https://github.com/GeoMaciolek/pi-gpio-synced-player.git
```

#### Autostart

To have the script run automatically on boot:
(note - on Debian 11, you will be prompted for your password)

```bash
cd ~/Downlods/pi-gpio-synced-player
./setup-autostart.sh
```

(This will add the needed lines from `lxde-autostart-template` to the system-wide
`/etc/xdg/lxsession/LXDE-pi/autostart` file.)

#### Running

To launch the player, you can either run the script directly:

```bash
cd ~/Downloads/pi-gpio-synced-player
python3 pi-gpio-synced-player.py
```

Or, you may use the wrapper script - included for auto-launch purposes.
    
```bash
cd ~/Downloads/pi-gpio-synced-player
./playback-wrapper.sh
```

## How It Works

Short version: the `primary` player sets the GPIO pin to `HIGH` and waits for a
half second or so. The secondary players reset playback to the start of the video,
and wait for the GPIO pin to go `LOW`. The primary player sets the pin to `LOW`
and starts playback itself, as do the secondaries.

## Additional Thoughts

### Credits

- Walt, for the original script, using `omxplayer` and `rPI.GPIO`
- Rem, for moral support and testing

### mpv

Note: another version of the script uses the `mpv` player &  `pympv` Python
module, but it has not been modularized or merged with the primary script. Use
at your own risk!
