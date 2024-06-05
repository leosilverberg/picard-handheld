from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import SQLiteVSS
from langchain.document_loaders import TextLoader

loader = TextLoader("./apollo11.txt")

documents = loader.load()

text_splitter = CharacterTextSplitter (chunk_size=1000, chunk_overlap=0)
docs = text_splitter.split_documents(documents)
texts = [doc.page_content for doc in docs]

embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")


db = SQLiteVSS.from_texts(
    texts = texts,
    embedding = embedding_function,
    table = "state_union",
    db_file = "/tmp/vss.db"
)

question = "What did armtstrong say at tranquility base?"
data = db.similarity_search(question)

print(data[0].page_content)