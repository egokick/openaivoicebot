import os
import sys
import subprocess
import argparse
import time
import pyaudio
from openai_get_response import stream_chat_with_gpt
from text_to_speech_eleven_labs import *
import text_to_speech_windows
from google.cloud import speech_v1
from google.cloud.speech_v1 import types
from google.api_core.exceptions import *
from threading import Timer
import numpy as np

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_credentials.json"

RATE = 16000 
CHUNK = int(RATE / 10)  # 100ms 
 
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
    except Unknown as e:
        print("Error while transcribing audio stream:", e)
        return None     
    except OutOfRange:
        pass
    
def call_text_to_speech(latestTranscript, fullTranscript, use_local_voice, audio_stream):
        sentence = ""        
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
                # Windows free voice
                if use_local_voice:
                    print("ai: " + sentence)
                    text_to_speech_windows.speak(sentence)
                    sentence = ""
                    first_iteration = False

                # Fancy AI voice (paid)
                else:
                    sentence = sentence.lstrip()
                    print("ai: " + sentence)
                    get_audio_stream(sentence, audio_stream_queue)            
                    sentence = ""
                    
                    if first_iteration is False and audio_playing.is_set():
                        try:
                            audio_thread1.join() # Wait for the previous audio to finish playing before moving on to play the next audio stream
                            audio_playing.clear()                
                        except:
                            pass

                    first_iteration = False
                    start_time = time.time()
                    
                    audio_thread1 = play_audio_stream(audio_stream_queue, audio_playing)
        
        if not use_local_voice and audio_playing.is_set():
            try:
                audio_thread1.join() # Wait for the previous audio to finish playing
                audio_playing.clear()                
            except:
                pass
                
        return fullResponse 

def audio_generator(audio_stream):
    for _ in range(sys.maxsize):
        data = audio_stream.read(CHUNK) 
        yield data

def start_bot(requests, audio_stream, bot_name, use_local_voice, alwaysListen):

    folder_path = 'chathistory'
    file_name = bot_name + '.json'
    file_path = os.path.join(folder_path, file_name)

    # Check if the folder exists, if not, create it
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    if not os.path.exists(file_path):
        with open(file_path, 'w') as file:
            pass  # Just create the file, don't write anything
    
    stats = "{ 'Name': 'Addy', 'Age': '28', 'JobTitle': 'Personal Assistant', 'Personality': 'Friendly, Direct', 'Intelligence': 'Extremely High', 'Traits': 'Good at remembering detail, great social skills', 'Setting': 'home office',  'Job Description': 'Extremely helpful assistant that can do anything.' }"
    fullTranscript = [{'role': 'system', 'content':  "You are a helpful assistant secretary.  Please review your character sheet and play the role. Character sheet: " + stats + ". Please stay in character. Introduce yourself, ask for my name."}]

    with open(file_path, 'r') as file:
        file_contents = file.readlines()
        if file_contents:        
            for line in file_contents:
                fullTranscript.append(json.loads(line.strip()))

    last_call_time = time.time()  # Initialize timestamp variable
    first_iteration = True

    while True:
   
        if not first_iteration:
            print("Listening...") 
            userInputText = transcribe_audio_stream(requests)
            print("user: " + userInputText)
        else:            
            userInputText = "Hello."

        time_since_last_call = time.time() - last_call_time        

        if(alwaysListen or first_iteration or time_since_last_call <= 30.0 or "robot" in userInputText.lower()):
            first_iteration = False
            botResponse = call_text_to_speech(userInputText, fullTranscript, use_local_voice, audio_stream)
            last_call_time = time.time()
            fullTranscript.append({'role': 'user', 'content': userInputText})
            fullTranscript.append({'role': 'assistant', 'content': botResponse})

            with open(file_path, 'a') as file:
                file.write(json.dumps({'role': 'user', 'content': userInputText}) + '\n')
                file.write(json.dumps({'role': 'assistant', 'content': botResponse}) + '\n')

        else:
            userInputText = ""

        time.sleep(0.1) 

def main(use_local_voice):    

    # todo: allow mic option to be changed by user         
    # todo: display audio wave in console next to each device name    
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

    requests = (
        speech_v1.StreamingRecognizeRequest(audio_content=content)
        for content in audio_generator(audio_stream)
    )
 
    start_bot(requests, audio_stream, bot_name="Addy", use_local_voice=True, alwaysListen=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process command line arguments")
    parser.add_argument("--use-local-voice", dest="use_local_voice", action="store_true", help="Use local free voice")
    parser.set_defaults(use_local_voice=False)
    args = parser.parse_args()

    main(args.use_local_voice)
