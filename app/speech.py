from flask import current_app

import os
import requests
import io

from io import BytesIO
import time
import pyttsx3
from gtts import gTTS

import tempfile

def speech2text(file):
    API_URL = "https://api-inference.huggingface.co/models/openai/whisper-large-v3"
    headers = {"Authorization": f'Bearer {os.getenv("HUGGING_FACE_API")}'}

    response = requests.post(API_URL, headers=headers, data=file)
    return response.json()

def text2speech(text):
    audio_stream = BytesIO()  # Create an in-memory byte stream

    try:
        os_name = os.name
        if os_name == 'nt':
            # Use pyttsx3 to generate audio and save to a temporary file first
            temp_file = "temp.mp3"
            engine = pyttsx3.init()
            engine.setProperty('rate', 150)  # Speed of speech
            engine.setProperty('volume', 0.9)  # Volume level (0.0 to 1.0)

            voices = engine.getProperty('voices')
            engine.setProperty('voice', voices[1].id)  # Use female voice

            # Save the generated speech to a temporary file
            engine.save_to_file(text, temp_file)
            engine.runAndWait()

            # Read the file content into the BytesIO stream
            with open(temp_file, 'rb') as f:
                audio_stream.write(f.read())

            # Clean up the temporary file after reading
            os.remove(temp_file)

        elif os_name == 'posix':
            # Use gTTS to write directly to the byte stream
            tts = gTTS(text=text, lang='en')
            tts.write_to_fp(audio_stream)  # Write to byte stream

        # Reset the pointer to the beginning of the stream
        audio_stream.seek(0)
        return audio_stream

    except Exception as e:
        print(f"Error generating speech: {e}")
        return None

class GroqLLMProcessor:
    def __init__(self, system_prompt, model_name="mixtral-8x7b-32768", temperature=0):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.url = "https://api.groq.com/openai/v1/chat/completions"
        self.model_name = model_name
        self.temperature = temperature
        self.messages = [{"role": "system", "content": system_prompt}]

    def _invoke_groq(self):
        """Make a request to the Groq API."""
        response = requests.post(
            self.url,
            json={
                "model": self.model_name,
                "temperature": self.temperature,
                "messages": self.messages,
            },
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def add_message(self, role, content):
        """Add a user or assistant message to the conversation history."""
        self.messages.append({"role": role, "content": content})

    def process(self, user_input):
        """Add user input, get response, and measure response time."""
        self.add_message("user", user_input)
        start_time = time.time()
        response = self._invoke_groq()
        elapsed_time = int((time.time() - start_time) * 1000)
        print(f"Response Time: {elapsed_time}ms")
        return response
        
def speech2speech(file, system_prompt, history):
    """Handle the full speech-to-speech pipeline."""
    user_input = speech2text(file)
    print("user: ", user_input)
    llm = GroqLLMProcessor(system_prompt)
    response_text = llm.process(user_input['text'])
    print("ai: ", response_text)
    return text2speech(response_text)
    