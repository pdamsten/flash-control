# Description

Control Godox flash settings from a destop app.

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
    
Tested with python 3.13

### Python packages

pywebview for html based gui

    pip install pywebview

bleak for bluetooth communication to godox trigger

    pip install bleak

## Install app

    git clone https://github.com/pdamsten/flash-control.git

## Run

    cd flash-control && ./flascontrol.py
