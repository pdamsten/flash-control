# Description

Control Godox flash settings from a destop app.

![gui](https://petridamsten.com/media/flash-control.png "GUI")

## Additional features

- Write all the info in gui to image metadata when tethering
- Use nanoKontrol 2 midi controller to adjust flash settings

# Installing
## Dependencies
### Python 3
#### MacOS
    brew install python3
    brew install pip3
    brew install exiftool
    
Tested with python 3.13 on macOS Sequoia 15.4

### Python packages

Run install script in main folder to install dependencies and fis app bundle.

    ./install.sh


## nanoKontrol2 configuration

nanoKontrol2 must be configured "Control Mode: CC" and "Led Mode: External". Settings are found under Control/Common in Korg Kontrol Editor.

## Install app

    git clone https://github.com/pdamsten/flash-control.git

## Run

    cd flash-control && ./flascontrol.py
