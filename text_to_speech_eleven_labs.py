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
        audio_stream = BytesIO()
        for chunk in response.iter_content(chunk_size=4096):
            audio_stream.write(chunk)
        audio_stream.seek(0)
        audio_queue.put(audio_stream)
    else:
        raise Exception(f"API call failed with status code {response.status_code} and response text: {response.text}")

def play_audio_stream(audio_stream_queue, audio_playing):
    while not audio_stream_queue.empty():
        audio_stream = audio_stream_queue.get()
        audio = AudioSegment.from_file(audio_stream, format="mp3")
        speedup_factor = 1  # Increase this value to make the audio faster
        audio = audio.set_frame_rate(int(audio.frame_rate * speedup_factor))

        audio_playing.set()
        audio_thread = threading.Thread(target=play, args=(audio, ))
        audio_thread.start()

        return audio_thread

def get_audio_stream(text, audio_stream_queue):
    stability = 0.3
    similarity_boost = 0.95

    tts_thread = threading.Thread(target=text_to_speech, args=(text, stability, similarity_boost, audio_stream_queue))
    tts_thread.start()

    tts_thread.join()  # Wait for the text_to_speech thread to finish

def play_audio(audio_queue: queue.Queue):
    audio_stream = BytesIO()    
    while True:        
        chunk = audio_queue.get()
        if chunk is None:
            break

        audio_stream.write(chunk)

    audio_stream.seek(0)
    audio = AudioSegment.from_file(audio_stream, format="mp3")    
    speedup_factor = 1 # Increase this value to make the audio faster
    audio = audio.set_frame_rate(int(audio.frame_rate * speedup_factor))

    play(audio)

def special_play_audio(text):
    stability = 0.3
    similarity_boost = 0.95

    audio_queue = queue.Queue()

    text_to_speech(text, stability, similarity_boost, audio_queue)
    play_audio(audio_queue)   

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

    # Call the special_play_audio function instead of the main function
    special_play_audio(args.text)
