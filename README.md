# Description

Control Godox flash settings from a destop app. The application is currently somewhere between proof of concept and alpha, so expect some bugs if you want to tinker with it.

![gui](https://petridamsten.com/media/flash-control.png "GUI")

## Additional features

- Write all the info in gui to image metadata when tethering
- Use nanoKONTROL2 midi controller to adjust flash settings

## Hardware requirements

- Mac or PC with Linux or Windows
- Godox trigger with bluetooth 
- Korg nanoKONTROL2 (optional)

## Keyboard / Nano shortcuts

- numbers or . or - or Enter : set power of active group eg. press 55 and group gets power 5.5
- Esc or Backspae : Cancel power
- O (nano PREV): Sound on/off
- Z (nano RECORD) : Modelling light on/off
- A - L : select group
- Space (nano S): Activate/deactivate group
- M (nano M): TTL / Manual toogle
- R (nano R): Reset modifiers etc. in active group
- nano STOP : test
- nano slider : adjust full stops
- nano knob : adjust fractions

# Installing
## MacOS
### Python 3 & exiftool
    brew install python3
    brew install pip3
    brew install exiftool
    
Tested with python 3.13 on macOS Sequoia 15.4

### Install app

    git clone https://github.com/pdamsten/flash-control.git

### Python packages

Run install script in main folder to install dependencies and fix app bundle path.

    ./install.sh

## Windows
### Python 3 & exiftool

Download and install python 3. Remeber to add check mark to "Add python to path". https://www.python.org/downloads/

Download and install exiftool. https://exiftool.org

### Install app

    git clone https://github.com/pdamsten/flash-control.git

### Python packages

Run install script in main folder to install dependencies and add icon to the desktop.

    ./install.bat

## nanoKontrol2 configuration

nanoKontrol2 must be configured "Control Mode: CC" and "Led Mode: External". Settings are found under Control/Common in Korg Kontrol Editor.


