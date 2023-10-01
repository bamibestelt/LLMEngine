import glob
import os
from typing import List

import chromadb
from dotenv import load_dotenv
from langchain.docstore.document import Document
from langchain.document_loaders import AsyncHtmlLoader
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma

from constants import PERSIST_DIRECTORY, CHROMA_SETTINGS, EMBEDDINGS_MODEL_NAME
from privateGPT import PrivateGPT

load_dotenv()


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


def persist_coda_data(texts: List[Document]):
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
        db.add_documents(texts)
    else:
        # Create and store locally vectorstore
        print("Creating new vectorstore")
        print(f"Creating embeddings. May take some minutes...")
        db = Chroma.from_documents(texts, embeddings, persist_directory=PERSIST_DIRECTORY,
                                   client_settings=CHROMA_SETTINGS, client=chroma_client)
    db.persist()
    db = None

    # try to initialize llm
    # if already active, restart
    PrivateGPT().init_llm_qa()

    print(f"Ingestion complete! You can now run GPT to query your documents")
