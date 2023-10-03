import glob
import os
from typing import List

import chromadb
from chromadb.api.segment import API
from dotenv import load_dotenv
from langchain.docstore.document import Document
from langchain.document_loaders import AsyncHtmlLoader
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma

from constants import PERSIST_DIRECTORY, CHROMA_SETTINGS, EMBEDDINGS_MODEL_NAME
from privateGPT import PrivateGPT

load_dotenv()

chunk_size = 500
chunk_overlap = 50


def parse_blog_document(links: List[str]) -> List[Document]:
    loader = AsyncHtmlLoader(links)
    docs = loader.load()
    print("decoding blog rss success")
    return docs


def does_vectorstore_exist() -> bool:
    if os.path.exists(os.path.join(PERSIST_DIRECTORY, 'index')):
        if (os.path.exists(os.path.join(PERSIST_DIRECTORY, 'chroma-collections.parquet')) and
                os.path.exists(os.path.join(PERSIST_DIRECTORY, 'chroma-embeddings.parquet'))):
            list_index_files = glob.glob(os.path.join(PERSIST_DIRECTORY, 'index/*.bin'))
            list_index_files += glob.glob(os.path.join(PERSIST_DIRECTORY, 'index/*.pkl'))
            # At least 3 documents are needed in a working vectorstore
            if len(list_index_files) > 3:
                return True
    return False


def process_documents(documents: List[Document], ignored_files: List[str] = []) -> List[Document]:
    """
    Load documents and split in chunks
    """
    for doc in documents:
        print(f"source: {doc.metadata['source']}")

    # documents = [file_path for file_path in all_files if file_path not in ignored_files]
    if not documents:
        print("No new documents to load")
        exit(0)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    documents = text_splitter.split_documents(documents)
    print(f"Split into {len(documents)} chunks of text (max. {chunk_size} tokens each)")
    return documents


def batch_chromadb_insertions(chroma_client: API, documents: List[Document]) -> List[Document]:
    """
    Split the total documents to be inserted into batches of documents that the local chroma client can process
    """
    # Get max batch size.
    max_batch_size = chroma_client.max_batch_size
    for i in range(0, len(documents), max_batch_size):
        yield documents[i:i + max_batch_size]


def persist_blog_data(texts: List[Document]):
    # Create embeddings
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDINGS_MODEL_NAME)
    # Chroma client
    chroma_client = chromadb.PersistentClient(settings=CHROMA_SETTINGS, path=PERSIST_DIRECTORY)

    if does_vectorstore_exist():
        # Update and store locally vectorstore
        print(f"Appending to existing vectorstore at {PERSIST_DIRECTORY}")
        db = Chroma(persist_directory=PERSIST_DIRECTORY, embedding_function=embeddings,
                    client_settings=CHROMA_SETTINGS, client=chroma_client)
        print(f"Creating embeddings. May take some minutes...")
        collection = db.get()
        documents = process_documents(texts, [metadata['source'] for metadata in collection['metadatas']])
        print(f"Creating embeddings. May take some minutes...")
        for batched_chromadb_insertion in batch_chromadb_insertions(chroma_client, documents):
            db.add_documents(batched_chromadb_insertion)
    else:
        # Create and store locally vectorstore
        print("Creating new vectorstore")
        documents = process_documents(texts)
        print(f"Creating embeddings. May take some minutes...")
        batched_chromadb_insertions = batch_chromadb_insertions(chroma_client, documents)
        first_insertion = next(batched_chromadb_insertions)
        db = Chroma.from_documents(first_insertion, embeddings, persist_directory=PERSIST_DIRECTORY,
                                   client_settings=CHROMA_SETTINGS, client=chroma_client)
        # Add the rest of batches of documents
        for batched_chromadb_insertion in batched_chromadb_insertions:
            db.add_documents(batched_chromadb_insertion)

    # try to initialize llm
    # if already active, restart
    PrivateGPT().init_llm_qa()

    print(f"Ingestion complete! You can now run GPT to query your documents")
