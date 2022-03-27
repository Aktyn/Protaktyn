from gtts import gTTS
from io import BytesIO

from pydub import AudioSegment
from pydub.playback import play


def speak(text: str):
    output = gTTS(text, lang='en', slow=False)
    fp = BytesIO()
    output.write_to_fp(fp)
    fp.seek(0)

    song = AudioSegment.from_file(fp, format="mp3")
    song -= 20  # decrease volume by 20 decibels
    play(song)
