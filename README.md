# Description

Control Godox flash settings from a destop app. The application is currently somewhere between proof of concept and alpha, so expect some bugs if you want to tinker with it.

![gui](https://petridamsten.com/media/flash-control.png "GUI")

## Additional features

- Write all the info in gui to image metadata when tethering
- Use nanoKontrol 2 midi controller to adjust flash settings

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


