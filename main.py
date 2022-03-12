"""
Speech recognition test for raspberry pi

sudo apt install flac
sudo pip3 install speechrecognition
"""

import speech_recognition as sr

a = sr.Recognizer()
with sr.Microphone() as source:
    print("Speak now")
    audio = a.listen(source)
    data = a.recognize_google(audio, None, "en-US", True)
    print(data)
