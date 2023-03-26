import os
import sys
import subprocess
import time
import pyaudio
from openai_get_response import stream_chat_with_gpt
from text_to_speech import *
from google.cloud import speech_v1
from google.cloud.speech_v1 import types
from google.api_core.exceptions import OutOfRange
from threading import Timer
import numpy as np

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_credentials.json"

RATE = 16000 
CHUNK = int(RATE / 10)  # 100ms
is_muted = False

 
def transcribe_audio_stream(requests):
    client_transcribe = speech_v1.SpeechClient()
    config = types.RecognitionConfig(
        encoding=speech_v1.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code="en-US",
    )

    streaming_config = types.StreamingRecognitionConfig(
        config=config,
        interim_results=True,
    )
    
    try:
        responses = client_transcribe.streaming_recognize(streaming_config, requests)        
        for response in responses:            
            for result in response.results:
                if result.is_final:                    
                    transcript = result.alternatives[0].transcript.strip()                    
                    return transcript        
    except OutOfRange:
        pass
    
def main():    

    print("starting...", end="")

    def call_text_to_speech(latestTranscript, fullTranscript):
        sentence = ""
        print("user: " + latestTranscript)
        fullResponse = ""

        audio_stream_queue = queue.Queue()
        audio_playing = threading.Event()

        start_time = time.time()
        first_iteration = True
        for openai_response in stream_chat_with_gpt(latestTranscript, fullTranscript):
            if openai_response != "!|!|TERMINATE!|!|!":
                openai_response = openai_response.replace('\n', '')
                openai_response = openai_response.replace('\r', '')
                fullResponse += openai_response

            sentence += openai_response
            word_count = len(sentence.split())

            elapsed_time = time.time() - start_time

            first_run = first_iteration and (word_count > 3 and len(sentence) > 2 and (sentence[-1]=='.' or sentence[-2]=='.'))
            has_sentence = (elapsed_time > 1 and (word_count > 3 and len(sentence) > 2 and (sentence[-1]=='.' or sentence[-2]=='.'))) or (word_count > 50 and (sentence[-1]=='.' or sentence[-2]=='.'))

            if has_sentence or first_run or openai_response == "!|!|TERMINATE!|!|!":
                sentence = sentence.lstrip()
                print("ai: " + sentence)
                get_audio_stream(sentence, audio_stream_queue)            
                sentence = ""
                
                if first_iteration is False and audio_playing.is_set():
                    try:
                        audio_thread1.join() # Wait for the previous audio to finish playing
                        audio_playing.clear()                
                    except:
                        pass

                first_iteration = False
                start_time = time.time()
                
                audio_thread1 = play_audio_stream(audio_stream_queue, audio_playing)
        
        if audio_playing.is_set():
            try:
                audio_thread1.join() # Wait for the previous audio to finish playing
                audio_playing.clear()                
            except:
                pass
                
        return fullResponse 
                   
    audio_interface = pyaudio.PyAudio()    
    device_info = audio_interface.get_default_input_device_info()
    device_name = device_info["name"]
    audio_stream = audio_interface.open(
        rate=RATE, channels=1, format=pyaudio.paInt16, input=True, frames_per_buffer=CHUNK,
    )

    # check if audio stream is active
    if audio_stream.is_active():
        print(f"Audio stream is open successfully with default device: {device_name}")
    else:
        print("Audio stream failed to open")

    def audio_generator():
        for _ in range(sys.maxsize):
            data = audio_stream.read(CHUNK) 
            yield data

    requests = (
        speech_v1.StreamingRecognizeRequest(audio_content=content)
        for content in audio_generator()
    )

    # Start transcribing audio from the microphone
    stats = "{ 'Name': 'Addy', 'Age': '28', 'JobTitle': 'Personal Assistant', 'Personality': 'Friendly, Direct', 'Intelligence': 'Extremely High', 'Traits': 'Good at remembering detail, great social skills', 'Setting': 'home office',  'Job Description': 'Extremely helpful assistant that can do anything.' }"
    fullTranscript = [{'role': 'system', 'content':  "You are roleplaying as a helpful assistant secretary. Please review your character sheet carefully and play that role. Character sheet: " + stats + ". Please stay in character unless you can't do something or don't have access to something. Ask for my name and always refer to me by name when you are speaking with me."}]
    while True:

        print("Listening...") 
        userInputText = transcribe_audio_stream(requests)

        botResponse = call_text_to_speech(userInputText, fullTranscript)
        
        fullTranscript.append({'role': 'user', 'content': userInputText})
        fullTranscript.append({'role': 'assistant', 'content': botResponse})

if __name__ == "__main__":
    main()
