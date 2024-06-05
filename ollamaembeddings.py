import ollama
import chromadb
import os

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

folder_path = 'data'

documents = read_documents_from_folder(folder_path)

client = chromadb.Client()
collection = client.create_collection(name="docs")

# store each document in a vector embedding database
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
  # an example prompt
prompt = "What day was the moon landing?"

# generate an embedding for the prompt and retrieve the most relevant doc
response = ollama.embeddings(
  prompt=prompt,
  model="all-minilm"
)

print("generated response")
results = collection.query(
  query_embeddings=[response["embedding"]],
  n_results=1
)
data = results['documents'][0][0]

print("asking:")
print(prompt)

print("using data:")
print(data)
# generate a response combining the prompt and data we retrieved in step 2
output = ollama.generate(
  model="phi3:mini",
  prompt=f"Using this data: {data}. Respond to this prompt in one short sentence: {prompt}",
  stream=False
)

print(output['response'])