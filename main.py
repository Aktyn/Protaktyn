#!/usr/bin/python
# -*- coding:utf-8 -*-
"""
Raspberry Pi project code

SETUP
sudo apt install flac
sudo apt install ffmpeg
sudo apt-get install libportaudio0 libportaudio2 libportaudiocpp0 portaudio19-dev
sudo pip3 install speechrecognition

in case of libcblas.so.3 errors: sudo apt-get install libatlas-base-dev
"""

from src.core import Core

if __name__ == "__main__":
    print('''
Raspberry Pi project code with multiple functionality and speech control
Author: Aktyn
        
Available arguments:
    nogui - doesn't display any GUI window
    use-epaper - uses ePaper display
    disable-speaker - disables voice generator
    start-module="MODULE NAME" - automatically starts specified module (available modules: scoreboard, robot)
''')
    Core()
