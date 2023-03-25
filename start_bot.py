import os
import sys
import subprocess
import time
import pyaudio
from openai_get_response import stream_chat_with_gpt
from text_to_speech import special_play_audio as playaudio
from google.cloud import speech_v1
from google.cloud.speech_v1 import types
from google.api_core.exceptions import OutOfRange
from threading import Timer
import numpy as np

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_credentials.json"

RATE = 16000
CHUNK = int(RATE / 10)  # 100ms
is_muted = False

def generate_sine_wave(frequency=10, duration=0.1, sample_rate=RATE, volume=0.01):
    samples = int(sample_rate * duration)
    t = np.linspace(0, duration, samples, False)
    sine_wave = volume * np.sin(frequency * 2 * np.pi * t)
    audio_data = sine_wave.astype(np.float32).tobytes()
    return audio_data

def transcribe_audio_stream(callback):
    client = speech_v1.SpeechClient()
    config = types.RecognitionConfig(
        encoding=speech_v1.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code="en-US",
    )

    streaming_config = types.StreamingRecognitionConfig(
        config=config,
        interim_results=True,
    )

    audio_interface = pyaudio.PyAudio()
    audio_stream = audio_interface.open(
        rate=RATE, channels=1, format=pyaudio.paInt16, input=True, frames_per_buffer=CHUNK
    )

    def audio_generator():
        global is_muted
        for _ in range(sys.maxsize):
            data = audio_stream.read(CHUNK)
            if is_muted:
                data = generate_sine_wave()  # Generate low-frequency sine wave
            else:
                data = audio_stream.read(CHUNK)  # Read audio data from the microphone
            yield data

    requests = (
        speech_v1.StreamingRecognizeRequest(audio_content=content)
        for content in audio_generator()
    )

    try:
        responses = client.streaming_recognize(streaming_config, requests)
        for response in responses:
            callback(response)
    except OutOfRange:
        pass
    finally:
        audio_stream.stop_stream()
        audio_stream.close()
        audio_interface.terminate()

def main():
    buffer = []
    timer = None
    global is_muted

    def process_transcript(response):
        global is_muted
        nonlocal buffer, timer
        if timer:
            timer.cancel()
        for result in response.results:
            if result.is_final:
                transcript = result.alternatives[0].transcript.strip()
                buffer.append(transcript)

        if buffer:            
            timer = Timer(1, call_text_to_speech)
            timer.start()

    def call_text_to_speech():
        global is_muted
        nonlocal buffer
        if buffer:
            is_muted = True
            text = " ".join(buffer)

            sentence = ""
            print("user: " + text)
            for openai_response in stream_chat_with_gpt(text):
                openai_response = openai_response.replace('\n', '')
                openai_response = openai_response.replace('\r', '')
               
                sentence += openai_response
                word_count = len(sentence.split())

                if(word_count > 26 or (len(sentence) > 2 and (sentence[-1]=='.' or sentence[-2]=='.'))):
                    print("ai: " + sentence)             
                    playaudio(sentence)   
                    sentence = ""                
            
            # plays last sentence
            if(len(sentence)> 1):
                print("ai: " + sentence)  
                playaudio(sentence)
                sentence = ""
           
            buffer.clear()
            is_muted = False

    # Start transcribing audio from the microphone
    transcribe_audio_stream(process_transcript)

if __name__ == "__main__":
    main()
