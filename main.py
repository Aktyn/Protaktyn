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
    nogui - disables PyQt5 GUI
    no-full-screen - disable PyQT5 full-screen mode window
    use-epaper - uses ePaper display
    disable-speaker - disables voice generator
    speak="Words to say at start" - automatically speaks given command
''')
    Core()
