from flask import current_app

import os
import requests
import json

from time import sleep


class Txt2Img():
    output_pattern = ''
    api_base_url = ''
    model = ''

    def __init__(self, model):
        self.model = model
        if os.getenv('IMAGE_ENGINE') == 'stable':
            self.api_base_url = 'https://stablediffusionapi.com/api/v3/text2img'
        else:
            self.api_base_url = 'https://modelslab.com/api/v6/images/text2img'

    def createImage(self, image_data):
        try:
            model_id = self.model
            if model_id is None or model_id == '':
                model_id = 'anything-v5'

            prompt = image_data.get('prompt')
            history = image_data.get('history', [])
            if history:
                his_prompt = 'This is our conversation.\n'
                for his in history:
                    if his['type'] == current_app.config['TEXT_Q']:
                        his_prompt += f'user: {his["text"]}\n'
                    elif his['type'] == current_app.config['TEXT_A']:
                        his_prompt += f'assistant: {his["text"]}\n'
                if history[-1]['type'] == current_app.config['IMAGE_Q']:
                    his_prompt += '\nBased on out conversation, you should create an image that satisfies the following prompts.\n'
                    his_prompt += f'prompt: {history[-1]["text"]}'
                prompt = his_prompt

            n_prompt = image_data.get('negative-prompt', "")
            if n_prompt is None:
                n_prompt = ''

            width = image_data.get('width', "512")
            if width is None or width == '':
                width = '512'

            height = image_data.get('height', "512")
            if height is None or height == '':
                height = '512'

            samples = image_data.get('samples', "1")    # count of image
            if samples is None or samples == '':
                samples = '1'

            api_key = ''
            if os.getenv('IMAGE_ENGINE') == 'stable':
                api_key = os.getenv('STABLE_DIFFUSION_API')
            else:
                api_key = os.getenv('MODELSLAB_API')

            payload = json.dumps({
                "key": api_key,
                "model_id": model_id,
                "prompt": prompt,
                "negative_prompt": n_prompt,
                "width": width,
                "height": height,
                "samples": samples,
                # "num_inference_steps": "30",
                # "safety_checker": "no",
                # "seed": None,
                "guidance_scale": 10,
                # "enhance_prompt": "yes",
                # "multi_lingual": "no",
                # "panorama": "no",
                "self_attention": "yes",
                "upscale": "yes",
                # "embeddings_model": None,
                # "lora_model": None,
                # "tomesd": "yes",
                # "use_karras_sigmas": "yes",
                # "vae": None,
                # "lora_strength": None,
                # "scheduler": "UniPCMultistepScheduler",
                # "webhook": None,
                # "track_id": None
            })

            headers = {
                'Content-Type': 'application/json'
            }

            response = requests.post(self.api_base_url, headers=headers, data=payload)
            if response.status_code == 200:
                output = response.json()
                if output['status'] == "success":
                    return True, {
                        "status": "success",
                        "id": output['id'],
                        "img_links": output['output']
                    }
                elif output['status'] == "processing":
                    return True, {
                        "status": "processing",
                        "id": output['id'],
                        "img_links": output['future_links']
                    }
                elif output['status'] == "error":
                    message = output.get('messege', "Error in processing")
                    print(message)
                    return False, message
                else:
                    return False, "Unknown error"
            else:
                return False, "Failed to communicate with the API"
        
        except Exception as e:
            current_app.logger.error(e)
            return False, ''
        
    def fetchImage(self, image_data):
        try:
            id = image_data.get('id', 0)
            if id == 0:
                return False, output.get('message', "invalid fetch id")

            if os.getenv('IMAGE_ENGINE') == 'stable':
                api_key = os.getenv('STABLE_DIFFUSION_API')
                url = f'https://stablediffusionapi.com/api/v3/fetch/{id}'
                payload = json.dumps({
                    "key": api_key
                })
            else:
                api_key = os.getenv('MODELSLAB_API')
                url = "https://modelslab.com/api/v6/images/fetch"
                payload = json.dumps({
                    "key": api_key,
                    "request_id": id,
                })
            
            headers = {
                'Content-Type': 'application/json'
            }

            response = requests.post(url, headers=headers, data=payload)
            if response.status_code == 200:
                output = response.json()
                print(output)
                if output['status'] == "success":
                    return True, {
                        "status": "success",
                        "id": output['id'],
                        "img_links": output['output']
                    }
                elif output['status'] == "processing":
                    return True, {
                        "status": "processing",
                        "id": id,
                        "img_links": []
                    }
                else:
                    return True, {
                        "status": "error",
                        "id": id,
                        "img_links": []
                    }
            else:
                return False, "Failed to communicate with the API"
                
        except Exception as e:
            current_app.logger.error(e)
            return False, ''

class Image3D():
    model = ''

    def __init__(self, model):
        self.model = model

    def createImage(self, session_id):
        print('create image')