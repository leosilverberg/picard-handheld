import ollama
import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
load_dotenv()
import chromadb

message_history = [{
    'role': 'system',
    'content': 'You are PiCard, a witty Raspbery Pi Voice Assistant. Please help by answering questions in only a sentence or two.',
}]

sentence_stoppers = ['. ', '.\n', '? ', '! ', '?\n', '!\n', '.\n']

client = chromadb.Client()
    
collection = client.create_collection(name="docs")

def read_documents_from_folder(folder_path):
    documents = []
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path) and filename.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                documents.append(content)
    return documents

def chunk_document(document, chunk_size=50):
    words = document.split()
    chunks = [' '.join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
    return chunks


def make_embeddings(folder_path="data"):
    documents = read_documents_from_folder(folder_path)

    
    for doc_id, document in enumerate(documents):
        chunks = chunk_document(document)
        for chunk_id, chunk in enumerate(chunks):
            response = ollama.embeddings(model="all-minilm", prompt=chunk)
            embedding = response["embedding"]
            collection.add(
                ids=[f"{doc_id}_{chunk_id}"],
                embeddings=[embedding],
                documents=[chunk]
            )
            
    print("created vector embeddings")

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

def get_llm_response_with_docs(transcription, model_name='llama3:instruct'):
    print("asking llm with docs")
    
    response = ollama.embeddings(
        prompt=transcription,
        model="all-minilm"
    )
    
    results = collection.query(
        query_embeddings=[response["embedding"]],
        n_results=1
    )
    
    data = results['documents'][0][0]
    
    response = ollama.generate(
        model=model_name,
        prompt=f"Using this data:# {data} # Respond to this prompt in one or two sentences: {transcription}",
        stream=False
    )
    
    return response


