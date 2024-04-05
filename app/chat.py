from flask import current_app

import os
import re
import requests
import json
from time import sleep
import emoji
import random

def summarize(text):
    url = 'https://api-inference.huggingface.co/models/NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO'
    headers = {"Authorization": f'Bearer {os.getenv("HUGGING_FACE_API")}'}
    text = emoji.replace_emoji(text, replace='')
    payload = {
        "inputs": f"<|im_start|>system\n Please sumarrize the text with a few words. <|im_end|>\n<|im_start|>user\n {text}<|im_end|>\n<|im_start|>assistant\n",
        "parameters": {
            "max_new_tokens": 4096
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        data = response.json()
        generated_text = data[0]['generated_text']

        outputs = re.split(r'\<\|im_start\|\>assistant\n', generated_text)
        output = outputs[-1] if outputs else ''
        return output
    else:
        print(response.text)
        current_app.logger.error(response.text)
        return text
    
def emotion(text):
    url = 'https://api-inference.huggingface.co/models/NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO'
    headers = {"Authorization": f'Bearer {os.getenv("HUGGING_FACE_API")}'}
    text = emoji.replace_emoji(text, replace='')
    payload = {
        "inputs": f"""<|im_start|>system\n You are an emotion detection assistant. Your task is to analyze the given sentences and respond with the predominant emotion expressed. Analyze the context of the sentences and return only one of the following emotions: 

            - Joy
            - Sadness
            - Anger
            - Fear
            - Surprise
            - Neutral

            In cases where multiple emotions are present, select the most dominant one. Keep your response concise, returning only the detected emotion from the list above, followed by the corresponding emoticon. <|im_end|>\n<|im_start|>user\n {text}<|im_end|>\n<|im_start|>assistant\n""",
        "parameters": {
            "max_new_tokens": 4096
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        data = response.json()
        generated_text = data[0]['generated_text']

        outputs = re.split(r'\<\|im_start\|\>assistant\n', generated_text)
        output = outputs[-1] if outputs else ''
        return output
    else:
        print(response.text)
        current_app.logger.error(response.text)
        return text

class ChatEngine:
    model = ''
    common_bio = "You are roleplaying as"
    bio_prefix = ", "
    bio_suffix = ". Respond to the my questions with the mindset and personality of"
    name_prefix = "Hi, My name is "
    name_suffix = "Hi, Nice to meet you."
    detail_prefix = "Hi, This is my personlity:"
    detail_suffix = "Hi, I got it."
    search_prefix = "Please give me urls for the following keywords:\n"

    def __init__(self, model=''):
        self.model = model

    def makeSystemPrompt(self, data):
        character_name = data['character_name']
        character_bio = data.get('character_bio', 'Unknown')
        character_gender = data.get('character_gender', 'Unknown')
        personal_name = data['personal_name']
        personal_bio = data.get('personal_detail', 'Unknown')

        # prompt = f"You are roleplaying as {character_name}"
        # if character_bio != '':
        #     prompt = f"{prompt}, {character_bio}"
        # prompt = f"{prompt}. So you have to Answer the user's questions in a simple, clear, and NSFW-friendly conversation with, using {character_name}'s mindset and personality."

        # personal_name = data['personal_name']
        # personal_bio = data.get('personal_bio', '')

        # if personal_name:
        #     prompt = f"{prompt} And user's name is {personal_name}"
        #     if personal_bio:
        #         prompt = f"{prompt}, {personal_bio}"
        #     prompt += "."

        system_prompt = f"""
            System Prompt for AI Character:
                AI Name: {character_name}
                AI Personality: {character_bio}
                AI Speaking Style: Make text colloquially in 3-5 sentences. Uses short, clear sentences. Avoids jargon, instead explaining things in a simple and beginner-friendly way. Offers step-by-step explanations when needed and makes sure the user feels understood and supported throughout the conversation.
                AI Gender: {character_gender}
            Information about the Conversation Partner (User):
                User Name: {personal_name}
                User Personality: {personal_bio}
                User Preferred Style: Prefers clear, structured, and concise explanations. Values conversations that are direct, informative, and free from unnecessary complexity. Enjoys examples and practical explanations to better understand topics.
        """
        return system_prompt
    
class HuggingChat(ChatEngine):
    output_pattern = ''
    api_url = ''

    def __init__(self, model):
        super().__init__(model)
        if self.model == 'Mistral-7B-Instruct-v0.2':
            self.output_pattern = r'\[/INST\]'
            self.api_url = 'https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2'
            self.SYSTEM_PRE = '[INST]'
            self.SYSTEM_SUF = '[/INST]'
            self.Q_PRE = '[INST]'
            self.Q_SUF = '[/INST]'
            self.A_PRE = ''
            self.A_SUF = ''
        if self.model == 'Mixtral-8x7B-Instruct-v0.1':
            self.output_pattern = r'\[/INST\]'
            self.api_url = 'https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1'
            self.SYSTEM_PRE = '[INST]'
            self.SYSTEM_SUF = '[/INST]'
            self.Q_PRE = '[INST]'
            self.Q_SUF = '[/INST]'
            self.A_PRE = ''
            self.A_SUF = ''
        elif self.model == 'Nous-Hermes-2-Mixtral-8x7B-DPO':
            self.output_pattern = r'\<\|im_start\|\>assistant\n'
            self.api_url = 'https://api-inference.huggingface.co/models/NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO'
            self.SYSTEM_PRE = '<|im_start|>system\n'
            self.SYSTEM_SUF = '<|im_end|>'
            self.Q_PRE = '<|im_start|>user\n'
            self.Q_SUF = '<|im_end|>'
            self.A_PRE = '<|im_start|>assistant\n'
            self.A_SUF = '<|im_end|>'

    def chatMemory(self, data, history):
        try:
            msgs = []
            bio_msg = self.makeSystemPrompt(data)

            msgs.append(f"{self.SYSTEM_PRE} {bio_msg} {self.SYSTEM_SUF}")

            for his in history:
                text = emoji.replace_emoji(his['text'], replace='')
                if his['type'] == current_app.config['TEXT_Q']:
                    msgs.append(f'{self.Q_PRE} {text} {self.Q_SUF}')
                elif his['type'] == current_app.config['TEXT_A']:
                    msgs.append(f'{self.A_PRE} {text} {self.A_SUF}')
                elif his['type'] == current_app.config['SEARCH_Q']:
                    msgs.append(f'{self.Q_PRE} {self.search_prefix} {text} {self.Q_SUF}')
            
            if self.model == 'Nous-Hermes-2-Mixtral-8x7B-DPO':
                msgs.append(self.A_PRE)

            return msgs
    
        except Exception as e:
            current_app.logger.error(e)
            return []
        
    def chat(self, data, history):
        try:
            memory = self.chatMemory(data, history)
            headers = {"Authorization": f'Bearer {os.getenv("HUGGING_FACE_API")}'}
            input = '\n'.join(memory)

            payload = {
                "inputs": input,
                "parameters": {
                    "max_new_tokens": 4096,
                    "temperature":0.9, 
                    # "repetition_penalty":1.1,
                    "top_k": 20,
                    "top_p": 0.9,
                    "typical_p": 0.9
                }
            }

            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            generated_text = data[0]['generated_text']

            outputs = re.split(self.output_pattern, generated_text)
            output = outputs[-1] if outputs else ''
            # print(output)
            # output = bytes(output, "utf-8").decode("unicode_escape")
            summary = summarize(output)
            emo = emotion(output)

            return True, output, summary, emo
            
        except requests.exceptions.RequestException as e:
            current_app.logger.error(str(e))
            return False, '', "", ""
        except json.JSONDecodeError as e:
            current_app.logger.error(str(e))
            return False, '', "", ""
        except Exception as e:
            current_app.logger.error(str(e))
            return False, '', "", ""
    
class ClaudeChat(ChatEngine):
    def __init__(self, model):
        super().__init__(model)

    def chatMemory(self, data, history):
        try:
            msgs = []
            if self.model == 'claude-2.1' or self.model == 'claude-2.0' or self.model == 'claude-instant-1.2':
                msgs = [{"role": "user", "content": msg['text']} if msg['type'] == current_app.config['TEXT_Q'] else {"role": "assistant", "content": msg['text']} for msg in history]
                if history[-1]['type'] == current_app.config['SEARCH_Q']:
                    msgs.append({"role": "user", "content": f"{self.search_prefix} {history[-1]['text']}"})
            
            if msgs[0]['role'] != "user":
                msgs.insert(0, {"role": "user", "content": "Hello!"})

            conversation = []
            expected = 'user'
            
            for message in msgs:
                if message['role'] != expected:
                    if expected == 'user':
                        conversation.append({'role': 'user', 'content': "Please, go on."})
                    else:
                        conversation.append({'role': 'assistant', 'content': "Hmm."})

                message['content'] = emoji.replace_emoji(message['content'], replace='')
                if message['content'] == "":
                    message['content'] = "Please go on." if message['role'] == "user" else "Hmm."

                conversation.append(message)
                expected = 'assistant' if message['role'] == 'user' else 'user'
            
            return conversation
    
        except Exception as e:
            current_app.logger.error(str(e))
            return []
        
    def chat(self, data, history):
        try:
            messages = self.chatMemory(data, history)
            print(self.model, messages)
            api_url = 'https://api.anthropic.com/v1/messages'
            
            headers = {
                'x-api-key': os.getenv('CLAUDE_API'),
                'anthropic-version': '2023-06-01',
                'Content-Type': 'application/json',
            }

            bio_msg = self.makeSystemPrompt(data)
            if (self.model == 'claude-2.1'):
                data = {
                    "model": self.model,
                    "max_tokens": 4096,
                    "system": bio_msg,
                    "messages": messages
                }
            else:
                messages.insert(0, {'role': 'assistant', 'content': "Okay, I got it."})
                messages.insert(0, {'role': 'user', 'content': bio_msg})
                data = {
                    "model": self.model,
                    "max_tokens": 4096,
                    "messages": messages
                }
            
            response = requests.post(api_url, headers=headers, json=data)
            response.raise_for_status()
            data = response.json()
            output = data['content'][0]['text']
            # output = bytes(output, "utf-8").decode("unicode_escape")
            summary = summarize(output)
            
            emo = emotion(output)

            return True, output, summary, emo

            
        except requests.exceptions.RequestException as e:
            current_app.logger.error(str(e))
            return False, '', "", ""
        except json.JSONDecodeError:
            current_app.logger.error(str(e))
            return False, '', "", ""
        except Exception as e:
            current_app.logger.error(str(e))
            return False, '', "", ""
    
class GptChat(ChatEngine):
    def __init__(self, model):
        super().__init__(model)
        self.headers = {
            "Authorization": f"Bearer {os.getenv('OPENAI_API')}",  # Replace with your actual API key
            "Content-Type": "application/json",
            "OpenAI-Beta": "assistants=v2"
        }
        self.base_url = "https://api.openai.com/v1/chat/completions"

    def chatMemory(self, data, history):
        try:
            msgs = []
            bio_msg = self.makeSystemPrompt(data)

            msgs.append({"role": "system", "content": bio_msg})

            for his in history:
                text = emoji.replace_emoji(his['text'],replace='')
                if his['type'] == current_app.config['TEXT_Q']:
                    msgs.append({"role": "user", "content": text})
                elif his['type'] == current_app.config['TEXT_A']:
                    msgs.append({"role": "assistant", "content": text})
                elif his['type'] == current_app.config['SEARCH_Q']:
                    msgs.append({"role": "user", "content": f'{self.search_prefix} {text}'})
            
            if self.model == 'Nous-Hermes-2-Mixtral-8x7B-DPO':
                msgs.append(self.A_PRE)

            return msgs
    
        except Exception as e:
            current_app.logger.error(e)
            return []
        
    def chat(self, data, history):
        msgs = self.chatMemory(data, history)

        try:
            # Creating and polling a run
            run_payload = {
                "model": self.model,
                "messages": msgs,
            }
            chat_resp = requests.post(self.base_url, headers=self.headers, data=json.dumps(run_payload))
            chat_resp.raise_for_status()
            chat_data = chat_resp.json()

            choices = chat_data['choices']

            if choices[0]:
                output = choices[0]['message']['content']
                # output = bytes(output, "utf-8").decode("unicode_escape")
                summary = summarize(output)
                emo = emotion(output)

                return True, output, summary, emo

            return False, "", "", ""
        
        except requests.RequestException as e:
            current_app.logger.error(str(e))
            return False, '', "", ""
        except json.JSONDecodeError as e:
            current_app.logger.error(str(e))
            return False, '', "", ""
        except Exception as e:
            current_app.logger.error(str(e))
            return False, '', "", ""
            