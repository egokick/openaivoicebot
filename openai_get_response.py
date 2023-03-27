import os
import sys
import json
import openai
import asyncio

with open('creds.json') as f:
    creds = json.load(f)

# Set API key
openai.api_key = creds['OPENAI_API_KEY']

# Send request and stream response
def stream_chat_with_gpt(input_string, fullTranscript):
    transcript = fullTranscript 
    transcript.append({'role': 'user', 'content': input_string})

    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages = transcript,
        temperature=0,
        stream=True  # this time, we set stream=True
    )

    for chunk in response:        
        if "choices" in chunk:
            for choice in chunk["choices"]:
                if "finish_reason" in choice and choice["finish_reason"] == "stop":
                    yield "!|!|TERMINATE!|!|!"
                elif "delta" in choice and "content" in choice["delta"]:
                    yield choice["delta"]["content"] # (choice["delta"]["content"], end="")

# Run function
if __name__ == "__main__":    
    # Get input from command-line
    input_text = sys.argv[1]
    loop = asyncio.get_event_loop()
    loop.run_until_complete(stream_chat_with_gpt(input_text))