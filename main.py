"""
Speech recognition test for raspberry pi

sudo apt install flac
sudo apt install ffmpeg
sudo apt-get install libportaudio0 libportaudio2 libportaudiocpp0 portaudio19-dev
sudo pip3 install speechrecognition
"""

from src.core import Core

if __name__ == "__main__":
    print("Speech recognition test for raspberry pi")
    Core()
