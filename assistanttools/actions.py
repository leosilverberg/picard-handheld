import ollama
import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
load_dotenv()

message_history = [{
    'role': 'system',
    'content': 'You are PiCard, a witty Raspbery Pi Voice Assistant. Please help by answering questions in only a sentence.',
}]

sentence_stoppers = ['. ', '.\n', '? ', '! ', '?\n', '!\n', '.\n']


def preload_model(model_name="llama3:instruct"):
    print("Preparing model...")
    os.system(
        f"curl http://localhost:11434/api/chat -d '{{\"model\": \"{model_name}\"}}'")

    print("Model preloaded.")
    return


def get_llm_response(transcription, message_history, streaming=True, model_name='llama3:instruct', max_spoken_tokens=300, use_rag=True, condense_messages=True):
    print("asking llm")
    
    message_history.append({
                'role': 'user',
                'content': transcription,
            })

    print("Message history: "+ ''.join(str(m) for m in message_history))
    response = ollama.chat(model=model_name,
                               stream=False, messages=message_history)
    response = response['message']['content']

   

    

    message_history.append({
        'role': 'assistant',
        'content': response,
    })

    return response, message_history



