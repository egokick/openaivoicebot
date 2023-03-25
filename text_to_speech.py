import argparse
import requests
import json
from io import BytesIO
from pydub import AudioSegment
from pydub.playback import play
import queue
import threading
import json

with open('creds.json') as f:
    creds = json.load(f)

VOICE_ID = "q4NcZ1UIsrVIO7oAFQc5" # cara "ZM3cm9AU0Fbq9tiQUoKZ"
API_KEY = creds['ELEVEN_LABS_API_KEY'] 
API_BASE_URL = "https://api.elevenlabs.io"
ENDPOINT = f"/v1/text-to-speech/{VOICE_ID}/stream"

def text_to_speech(text: str, stability: float, similarity_boost: float, audio_queue: queue.Queue):
    headers = {
        "Content-Type": "application/json",
        "xi-api-key": API_KEY,
    }

    data = {
        "text": text,
        "voice_settings": {
            "stability": stability,
            "similarity_boost": similarity_boost,
        },
    }

    response = requests.post(API_BASE_URL + ENDPOINT, headers=headers, data=json.dumps(data), stream=True)

    if response.status_code == 200:
        for chunk in response.iter_content(chunk_size=4096):
            audio_queue.put(chunk)
        audio_queue.put(None)  # Signal the end of the audio stream
    else:
        raise Exception(f"API call failed with status code {response.status_code} and response text: {response.text}")


def play_audio(audio_queue: queue.Queue):
    audio_stream = BytesIO()
    while True:
        chunk = audio_queue.get()
        if chunk is None:
            break
        audio_stream.write(chunk)

    audio_stream.seek(0)
    audio = AudioSegment.from_file(audio_stream, format="mp3")
    play(audio)


def special_play_audio(text):
    stability = 0.7
    similarity_boost = 0.7

    audio_queue = queue.Queue()
    playback_thread = threading.Thread(target=play_audio, args=(audio_queue,))
    playback_thread.start()

    text_to_speech(text, stability, similarity_boost, audio_queue)

    playback_thread.join()
    
def main(args):
    stability = 0.3
    similarity_boost = 0.7

    audio_queue = queue.Queue()
    playback_thread = threading.Thread(target=play_audio, args=(audio_queue,))
    playback_thread.start()

    text_to_speech(args.text, stability, similarity_boost, audio_queue)

    playback_thread.join()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert text to speech using the Eleven Labs API")
    parser.add_argument("text", type=str, help="The text to be converted to speech")
    args = parser.parse_args()

    main(args)
