from gtts import gTTS, gTTSError
from io import BytesIO
from pydub import AudioSegment
from pydub.playback import play


def speak(text: str, lang='en', volume_decrease=20):
    try:
        output = gTTS(text, lang=lang, slow=False)
        fp = BytesIO()
        output.write_to_fp(fp)
        fp.seek(0)
        song = AudioSegment.from_file(fp, format="mp3")
        song -= volume_decrease  # decrease volume by 20 decibels
        play(song)
    except gTTSError:
        print("Error: Could not generate speech.")
