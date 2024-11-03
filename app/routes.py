from flask import Blueprint, current_app, request, redirect, jsonify, make_response, send_file
from flask_cors import CORS

import uuid

from werkzeug.utils import secure_filename

import requests

import os
from PIL import Image

import json
from datetime import datetime
from time import sleep
import re

from .chat import HuggingChat, ClaudeChat, GptChat
from .image import Txt2Img, Image3D
from .speech import speech2text, text2speech, speech2speech

main = Blueprint('main', __name__)

CORS(main)

def get_chat_engine(model_name):
    """Factory function to get the corresponding chat engine based on the model name."""
    model_to_engine = {
        'Mistral-7B-Instruct-v0.2': HuggingChat,
        'Nous-Hermes-2-Mixtral-8x7B-DPO': HuggingChat,
        'Mixtral-8x7B-Instruct-v0.1': HuggingChat,
        'claude-2.1': ClaudeChat,
        'claude-2.0': ClaudeChat,
        'claude-instant-1.2': ClaudeChat,
        'gpt-3.5-turbo': GptChat,
        'gpt-4': GptChat,
        'gpt-4-turbo': GptChat
    }
    chat_engine_cls = model_to_engine.get(model_name)
    if chat_engine_cls:
        return chat_engine_cls(model_name)
    return None

@main.route('/create-image', methods=['POST'])
def createImage():
    try:
        image_data = request.get_json()
        image_type = image_data.get('type', 1)
        engine = None

        model = image_data.get('model', 'anything-v5')

        print(image_data)
        if image_type == 1:
            engine = Txt2Img(model)
        elif image_type == 3:
            engine = Image3D(model)
        else:
            engine = Txt2Img(model)

        status, data = engine.createImage(image_data)

        return jsonify(data), 200 if status else 400
    except Exception as e:
        current_app.logger.error(str(e))
        return jsonify(str(e)), 500

@main.route('/fetch-image', methods=['POST'])
def fetchImage():
    try:
        image_data = request.get_json()
        image_type = image_data.get('type', 1)
        engine = None
        model = image_data.get('model', 'anything-v5')
        print(image_data)
        if image_type == 1:
            engine = Txt2Img(model)
        elif image_type == 3:
            engine = Image3D(model)
        else:
            engine = Txt2Img(model)

        status, data = engine.fetchImage(image_data)

        print(data)
        return jsonify(data), 200 if status else 400
    except Exception as e:
        current_app.logger.error(str(e))
        return jsonify(str(e)), 500

@main.route('/chat', methods=['POST'])
def chat():
    try:
        chat_data = request.get_json()
        model = chat_data.get('model', 'Nous-Hermes-2-Mixtral-8x7B-DPO')
        data = json.loads(chat_data.get('data', "{}"))
        history = chat_data.get('history', [])

        output = ''
        status = False

        chatEngine = get_chat_engine(model)

        if chatEngine == None:
            return jsonify(output), 400
        
        status, output, summary, emotion = chatEngine.chat(data, history)
        print(output)
        return jsonify({'msg': output, 'summary': summary, 'emotion': emotion}), 200 if status else 400
    
    except Exception as e:
        current_app.logger.error(str(e))
        return jsonify(str(e)), 500

@main.route('/search', methods=['POST'])
def search():
    try:
        chat_data = request.get_json()
        model = chat_data.get('model', 'Nous-Hermes-2-Mixtral-8x7B-DPO')
        data = json.loads(chat_data.get('data', "{}"))
        history = chat_data.get('history', [])
        status = False

        chatEngine = get_chat_engine(model)

        if chatEngine == None:
            return jsonify([]), 400
        
        status, output = chatEngine.chat(data, history)
        url_pattern = r"\b((?:https?://)?(?:(?:www\.)?(?:[\da-z\.-]+)\.(?:[a-z]{2,6})|(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)|(?:(?:[0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,7}:|(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}|(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}|(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}|(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:(?:(?::[0-9a-fA-F]{1,4}){1,6})|:(?:(?::[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(?::[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(?:ffff(?::0{1,4}){0,1}:){0,1}(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])|(?:[0-9a-fA-F]{1,4}:){1,4}:(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])))(?::[0-9]{1,4}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])?(?:/[\w\.-]*)*/?)\b"
        urls = re.findall(url_pattern, output)
        print(urls)
        return jsonify(urls), 200 if status else 400
    
    except Exception as e:
        current_app.logger.error(str(e))
        return jsonify(str(e)), 500

@main.route('/speech-text', methods=['POST'])
def speech_text():
    try:
        file = request.files.get('file')
        if not file or file.filename == '':
            return jsonify({'error': 'No file provided or filename is empty'}), 400

        data = speech2text(file)
        print(data['text'])
        return data['text'], 200
    except Exception as e:
        current_app.logger.error(str(e))
        return jsonify(str(e)), 500

@main.route('/text-speech', methods=['POST'])
def text_speech():
    try:
        data = request.get_json()
        text = data.get('text', '')

        if not text:
            raise ValueError("Text cannot be empty")

        # Generate audio and get the file path
        audio_stream = text2speech(text)

        if audio_stream:
            # Send the audio file as a response
            return send_file(audio_stream, mimetype='audio/mpeg', as_attachment=True, download_name='speech.mp3')

    except Exception as e:
        current_app.logger.error(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@main.route('/speech-speech', methods=['POST'])
def speech_speech():
    try:
        file = request.files.get('file')
        
        # Retrieve JSON data from the 'data' field in the form
        json_data = request.form.get('data')
        data = json.loads(json_data) if json_data else {}

        # Extract specific values from the JSON
        system = data.get('system', '')
        history = data.get('history', [])

        # Validate the file
        if not file or file.filename == '':
            return jsonify({'error': 'No file provided or filename is empty'}), 400

        # Process the file and data
        audio_stream = speech2speech(file, system, history)
        
        if audio_stream:
            # Send the audio file as a response
            return send_file(audio_stream, mimetype='audio/mpeg', as_attachment=True, download_name='speech.mp3')
    except Exception as e:
        current_app.logger.error(str(e))
        return jsonify(str(e)), 500