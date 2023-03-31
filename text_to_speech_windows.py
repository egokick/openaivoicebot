import pyttsx3
import time
import threading
import queue

def speak(text):
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    # for i, voice in enumerate(voices):
    #     print(f"Voice {i}: {voice.name}, ID: {voice.id}")

    engine.setProperty('voice', 'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-GB_HAZEL_11.0')
    engine.say(text)
    engine.runAndWait()

def get_audio_stream(sentence, audio_stream_queue):
    tts_thread = threading.Thread(target=speak, args=(sentence,))
    tts_thread.start()

    tts_thread.join()  # Wait for the speak function to finish

# The rest of your code remains unchanged
