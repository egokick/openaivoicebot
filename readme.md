# Install
run install.bat

# Setup
you'll need to create your own creds.json file which looks like this
```
{
    "OPENAI_API_KEY": "??",
    "ELEVEN_LABS_API_KEY": "???"
}
```
and a gcp_credentials.json file and put it in the root directory.

you won't have access to the voiceId I'm using for eleven labs. So you'll need to change the VOICE_ID in the text_to_speech.py file

# Run the bot
```
python start_bot.py
```

# Run the bot with voice disabled

```
python start_bot.py --disable-voice
```


# Misc
chunk api documentation into smaller text files
```
python split_text.py elevenlabs-api.txt
```
