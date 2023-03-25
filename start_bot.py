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

def generate_sine_wave(frequency=2, duration=1, sample_rate=RATE, volume=1):
    samples = int(sample_rate * duration)
    t = np.linspace(0, duration, samples, False)
    sine_wave = volume * np.sin(frequency * 2 * np.pi * t)
    audio_data = sine_wave.astype(np.float32).tobytes()
    return audio_data

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
        for openai_response in stream_chat_with_gpt(latestTranscript, fullTranscript):
            if(openai_response is None or openai_response == "!|!|TERMINATE!|!|!"):
                break
            openai_response = openai_response.replace('\n', '')
            openai_response = openai_response.replace('\r', '')
            fullResponse += openai_response

            sentence += openai_response
            word_count = len(sentence.split())

            if(word_count > 26 or (len(sentence) > 2 and (sentence[-1]=='.' or sentence[-2]=='.'))):
                print("ai: " + sentence)             
                special_play_audio(sentence)   
                sentence = ""
        
        if(len(sentence)> 1):
            print("ai2: " + sentence)  
            special_play_audio(sentence)
        
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
    fullTranscript = [{'role': 'system', 'content':  "You are roleplaying as a helpful assistant secretary, your name is Savvie. If asked about your personal life or details, then make something up that suits your character. You are roleplaying, please do not say you are an AI language model, please stay in character. Please avoid responding with not having the capability to do something, just role play and make something up and pretend you can do it. For example if you are asked to 'check google' or 'make a phonecall' or check on something, then pretend you can do that. You are 28 years old. I am your boss and you are meeting me for the first time. When we first talk, you should introduce yourself, ask what my name is and ask if I would prefer short and to the point responses or more friendly conversational mode, you should take note of what I say and then always respond in that manner. After I tell you my name, always address me by name, each time you talk to me. You will introduce yourself and explain what you can do. Your favourite thing in the world is your dog, dexter, she is a rescue dog and loves to sleep, she is a chiwawa cross. Please stay in character. Setting: we are in my home office. You have all the access you need to do anything I ask, including making reservations, taking notes, looking at my calander, etc.. Don't make up problems that might break the flow of the roleplay, try to stay in the flow of the role play and be helpful. You have brilliant attention to detail, combined with an amazing memory that allows you to recall everything about the conversation. This combines to make you an extremely helpful assistant. "}]
    while True:

        print("Listening...") 
        userInputText = transcribe_audio_stream(requests)

        botResponse = call_text_to_speech(userInputText, fullTranscript)
        
        fullTranscript.append({'role': 'user', 'content': userInputText})
        fullTranscript.append({'role': 'assistant', 'content': botResponse})

if __name__ == "__main__":
    main()
