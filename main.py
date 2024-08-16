import json
import time

import requests
import base64


import speech_recognition as sr
from transformers import AutoTokenizer
from transformers import AutoModelForSequenceClassification
from huggingface_hub import InferenceClient

import torch

import os
from elevenlabs.client import ElevenLabs

from dotenv import load_dotenv
from transformers import pipeline, set_seed
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler
neg_prompt = "ugly, blurry, poor quality"
torch.backends.cuda.matmul.allow_tf32 = True

generator = pipeline('text-generation', model='distilgpt2')

# Use the DPMSolverMultistepScheduler (DPM-Solver++) scheduler here instead
model_id = "prompthero/openjourney-v4"

# Use the DPMSolverMultistepScheduler (DPM-Solver++) scheduler here instead
pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16)
pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
pipe = pipe.to("cuda")



soft = torch.nn.Softmax(dim=1)
load_dotenv()
ELEVENLABS_API_KEY = 'sk_c19869959a2d82c45c76205ddcce0a7dedf6cf3a7e34a2bd'
elevenlabs = ElevenLabs(api_key=ELEVENLABS_API_KEY)

client = InferenceClient(headers={"Authorization": "Bearer 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"})

tokenizer = AutoTokenizer.from_pretrained("google-bert/bert-base-uncased")

model = AutoModelForSequenceClassification.from_pretrained("mishkashishka/dnd_en")



# Инициализация распознавателя
recognizer = sr.Recognizer()

def read(mic_name):
    mic_index = sr.Microphone.list_microphone_names().index(mic_name)
    with sr.Microphone(device_index=mic_index) as source:
        print("Говорите")
        #recognizer.pause_threshold = 1
        recognizer.dynamic_energy_threshold = False
        recognizer.energy_threshold = 500 
        
        #recognizer.adjust_for_ambient_noise(source, duration=1)
        
        audio = recognizer.listen(source)
    try:
        text = recognizer.recognize_google(audio, language="ru-RU")
        print(text)
        return text
    except sr.UnknownValueError:
        print("Не удалось распознать речь")
        return False
    except sr.RequestError as e:
        print(f"Ошибка сервиса; {e}")
        return False
    

def chesk(text):
    inputs = tokenizer(text, return_tensors="pt")
    with torch.no_grad():
        logits = model(**inputs).logits
    predicted_class_id = soft(logits)[0][1].item()
    print(predicted_class_id)
    return predicted_class_id

def generation(text):

    image = pipe(prompt=text,
                 height=512,
                 width=512,
                 guidance_scale=3.5,
                 neg_prompt=neg_prompt,
                 num_images_per_prompt=1,
                 num_inference_steps=10).images[0]
    image.save('img.jpg')
    return 'img.jpg'

def generate_sound_effect(text: str, output_path: str):
    print("Generating sound effects...")

    result = elevenlabs.text_to_sound_effects.convert(
        text=text,
        duration_seconds=3,  
        prompt_influence=0.3,  
    )
    with open(output_path, "wb") as f:
        for chunk in result:
            f.write(chunk)
        print(f"Audio saved to {output_path}")



tokenizert = AutoTokenizer.from_pretrained("Helsinki-NLP/opus-mt-ru-en")
modelt = AutoModelForSeq2SeqLM.from_pretrained("Helsinki-NLP/opus-mt-ru-en")
def translation(text):
    input_ids = tokenizert.encode(text, return_tensors="pt")
    outputs = modelt.generate(input_ids)
    decoded = tokenizert.decode(outputs[0], skip_special_tokens=True)
    return decoded