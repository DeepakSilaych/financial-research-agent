# ------------------------ IMPORTS ------------------------
from langchain.embeddings.openai import OpenAIEmbeddings
import faiss
import numpy as np
import os
from dotenv import load_dotenv
import time
import json
from PyPDF2 import PdfReader  # assuming you are using this
from langchain.text_splitter import RecursiveCharacterTextSplitter

# ------------------------ LOAD .env ------------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OpenAI API Key not found. Please set it in the .env file.")

# Initialize OpenAI embeddings
embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

# ------------------------ FAISS FUNCTIONS ------------------------
def save_index(index, documents, ids, index_file_path, doc_map_file_path):
    faiss.write_index(index, index_file_path)
    print(f"Index saved to {index_file_path}")

    doc_map = {ids[i]: documents[i] for i in range(len(documents))}
    with open(doc_map_file_path, 'w') as doc_map_file:
        json.dump(doc_map, doc_map_file)
    print(f"Document mapping saved to {doc_map_file_path}")

def load_index(index_file_path, doc_map_file_path):
    index = faiss.read_index(index_file_path)
    print(f"Index loaded from {index_file_path}")

    with open(doc_map_file_path, 'r') as doc_map_file:
        doc_map = json.load(doc_map_file)
    print(f"Document mapping loaded from {doc_map_file_path}")

    ids = list(doc_map.keys())
    documents = list(doc_map.values())

    return index, documents, ids

def calculate_embedding(chunks, chunk_ids, BATCH_SIZE=20, persist_path="faiss_index.index", doc_map_path="doc_map.json"):

    if os.path.exists(persist_path):
        print("Loading existing FAISS index and document mapping...")
        index, documents, ids = load_index(persist_path, doc_map_path)
    else:
        print("Creating new FAISS index and document mapping...")
        embedding_dim = len(embeddings.embed_documents(["test"])[0])
        index = faiss.IndexFlatL2(embedding_dim)
        documents = []
        ids = []

    for i in range(0, len(chunks), BATCH_SIZE):
        batch_chunks = chunks[i:i + BATCH_SIZE]
        batch_ids = chunk_ids[i:i + BATCH_SIZE]
        batch_embeddings = embeddings.embed_documents(batch_chunks)

        batch_embeddings = np.array(batch_embeddings).astype('float32')
        index.add(batch_embeddings)

        documents.extend(batch_chunks)  # Add new documents
        ids.extend(batch_ids)           # Add new IDs
    

    save_index(index, documents, ids, persist_path, doc_map_path)

    return index, documents, ids

def query_embeddings(index, query_text, documents, ids, top_k=3):
    query_embedding = np.array([embeddings.embed_query(query_text)]).astype('float32')
    distances, indices = index.search(query_embedding, top_k)

    results = []
    for i in range(top_k):
        index_id = indices[0][i]
        if index_id < len(ids):
            doc_id = ids[index_id]
            document = documents[index_id]
            distance = distances[0][i]
            results.append((document, doc_id, distance))
        else:
            results.append((None, None, None))

    return results

def print_query_results(results):
    for idx, (document, doc_id, distance) in enumerate(results):
        print(f"\nResult {idx + 1}:")
        if document:
            print(f"Document ID: {doc_id}")
            print(f"Distance: {distance:.4f}")
            print(f"Content: {document[:300]}...")  # Print only first 300 chars
        else:
            print("No document found.")

# ------------------------ PDF LOADING AND CHUNKING ------------------------
def load_pdfs_and_chunk(pdf_folder_path):
    text = ""
    for filename in os.listdir(pdf_folder_path):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(pdf_folder_path, filename)
            print(f"Reading {filename}...")
            reader = PdfReader(pdf_path)
            for page in reader.pages:
                text += page.extract_text() + "\n"

    if not text.strip():
        raise ValueError("No text found in PDFs.")

    # Chunk the text
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = text_splitter.split_text(text)

    print(f"Total chunks created: {len(chunks)}")

    # Create simple chunk IDs
    chunk_ids = [f"chunk_{i}" for i in range(len(chunks))]

    return chunks, chunk_ids

# ------------------------ MAIN ------------------------
if __name__ == "__main__":
    pdf_folder = r"data\input"  # <-- Change this if your PDFs are in a different folder
    persist_path = r"data\output\faiss_index.index"
    doc_map_path = r"data\output\doc_map.json"

    chunks, chunk_ids = load_pdfs_and_chunk(pdf_folder)

    print("Starting embedding and indexing...")
    index, documents, ids = calculate_embedding(chunks, chunk_ids, persist_path=persist_path, doc_map_path=doc_map_path)

    print("\n✅ All done! FAISS index and document mapping saved.")
