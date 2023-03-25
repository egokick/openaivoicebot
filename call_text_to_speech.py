import os
import sys
import subprocess
import pyaudio
from google.cloud import speech_v1
from google.cloud.speech_v1 import types
from google.api_core.exceptions import OutOfRange
from threading import Timer

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_credentials.json"

RATE = 16000
CHUNK = int(RATE / 10)  # 100ms

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

    is_muted = False

    def audio_generator():
        nonlocal is_muted
        for _ in range(sys.maxsize):
            data = audio_stream.read(CHUNK)
            if not is_muted:
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
    is_muted = False

    def process_transcript(response):
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
        nonlocal buffer, is_muted
        if buffer:
            is_muted = True
            text = " ".join(buffer)
            command = f'python text_to_speech_v2.py "{text}"'
            subprocess.run(command, shell=True, check=True)
            buffer.clear()
            is_muted = False

    # Start transcribing audio from the microphone
    transcribe_audio_stream(process_transcript)

if __name__ == "__main__":
    main()
