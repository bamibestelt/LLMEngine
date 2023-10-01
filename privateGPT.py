import os
import time

import chromadb
from dotenv import load_dotenv
from langchain.chains import RetrievalQA
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.llms import GPT4All, LlamaCpp
from langchain.vectorstores import Chroma

from constants import CHROMA_SETTINGS

if not load_dotenv():
    print("Could not load .env file or it is empty. Please check if it exists and is readable.")
    exit(1)

embeddings_model_name = os.environ.get("EMBEDDINGS_MODEL_NAME")
persist_directory = os.environ.get('PERSIST_DIRECTORY')

model_type = os.environ.get('MODEL_TYPE')
model_path = os.environ.get('MODEL_PATH')
model_n_ctx = os.environ.get('MODEL_N_CTX')
model_n_batch = int(os.environ.get('MODEL_N_BATCH', 8))
target_source_chunks = int(os.environ.get('TARGET_SOURCE_CHUNKS', 4))


class LLMAnswerModel:
    def __init__(self, seconds, a):
        self.time = seconds
        self.answer = a


class PrivateGPT:
    _instance = None
    _retrievalQA = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(PrivateGPT, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def init_llm_qa(self):
        if self._retrievalQA is not None:
            return

        print('RetrievalQA is null. LLM initialization started...')

        embeddings = HuggingFaceEmbeddings(model_name=embeddings_model_name)
        print('embeddings initialized...')

        chroma_client = chromadb.PersistentClient(settings=CHROMA_SETTINGS, path=persist_directory)
        print('chromadb client initialized...')

        db = Chroma(persist_directory=persist_directory,
                    embedding_function=embeddings,
                    client_settings=CHROMA_SETTINGS,
                    client=chroma_client)
        retriever = db.as_retriever(search_kwargs={"k": target_source_chunks})
        print('vector store retriever obtained...')

        # activate/deactivate the streaming StdOut callback for LLMs
        callbacks = []  # if args.mute_stream else [StreamingStdOutCallbackHandler()]
        # Prepare the LLM
        match model_type:
            case "LlamaCpp":
                llm = LlamaCpp(model_path=model_path,
                               max_tokens=model_n_ctx,
                               n_batch=model_n_batch,
                               callbacks=callbacks,
                               verbose=False)
            case "GPT4All":
                llm = GPT4All(model=model_path,
                              max_tokens=model_n_ctx,
                              backend='gptj',
                              n_batch=model_n_batch,
                              callbacks=callbacks,
                              verbose=False)
            case _default:
                # raise exception if model_type is not supported
                raise Exception(f"Model type {model_type} is not supported."
                                f"Please choose one of the following: LlamaCpp, GPT4All")

        self._retrievalQA = RetrievalQA.from_chain_type(llm=llm,
                                                        chain_type="stuff",
                                                        retriever=retriever,
                                                        return_source_documents=False)
        print('LLM ready!')

    def qa_prompt(self, prompt: str) -> LLMAnswerModel:
        # Check for RetrievalQA state
        if self._retrievalQA is None:
            # need to restart init_llm_qa and post init process to client
            self.init_llm_qa()

        print('Query prompt...')
        # Get the answer from the chain
        start = time.time()
        res = self._retrievalQA(prompt)
        answer, docs = res['result'], []  # if args.hide_source else res['source_documents']
        end = time.time()

        time_seconds = round(end - start, 2)
        print('LLM reply available')
        return LLMAnswerModel(time_seconds, answer)
