import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
import os

documents = SimpleDirectoryReader("data").load_data()


Settings.embed_model = OllamaEmbedding(model_name="all-minilm")

# ollama
Settings.llm = Ollama(model="mistral", request_timeout=360.0)


index = VectorStoreIndex.from_documents(
    documents,
    show_progress=True
)

chat_engine = index.as_chat_engine(verbose=True)
# query_engine = index.as_query_engine(verbose=True)
response = chat_engine.chat("what did armstrong say at tranquility base?")
print(response)