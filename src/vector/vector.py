import os
import shutil
import logging
from typing import List
import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import VectorStoreIndex
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.storage.storage_context import StorageContext

from llama_index.core.schema import BaseNode
from src.run.utils import base_dir_for_run


logger = logging.getLogger(__name__)

# https://github.com/langchain-ai/langchain/issues/26884
chromadb.api.client.SharedSystemClient.clear_system_cache()


def get_vector_index(run_id: str=None, base_dir: str="output"):

    chromadb.api.client.SharedSystemClient.clear_system_cache()

    persist_dir = base_dir_for_run(run_id, base_dir) + "/vector_index"
    logger.info(f"get vector index from {persist_dir=}")

    db = chromadb.PersistentClient(path=persist_dir)
    chroma_collection = db.get_or_create_collection("frag")

    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    index = VectorStoreIndex.from_vector_store(vector_store)

    logger.info(f"success getting vector index from {persist_dir=}")
    return index


def get_vector_retriever(run_id: str=None, base_dir: str="output"):

    index = get_vector_index(run_id, base_dir)
    return index.as_retriever()


def query_with_vector_retriever(run_id: str=None, base_dir: str="output", args=None):

    query_str = args.query
    if query_str is None:
        logger.error("no query")
        return

    retriever = get_vector_retriever(run_id, base_dir)

    query_engine = RetrieverQueryEngine(
        retriever=retriever
    )

    response = query_engine.query(query_str)

    logger.info(f"{response.response}")
    return response


def embed_nodes(nodes: List[BaseNode], run_id: str, base_dir: str, args=None):

    chromadb.api.client.SharedSystemClient.clear_system_cache()

    vector_index_dir = base_dir_for_run(run_id, base_dir) + "/vector_index"
    # clear previous index
    if os.path.exists(vector_index_dir):
        shutil.rmtree(vector_index_dir)

    os.makedirs(vector_index_dir, exist_ok=True)

    logger.info(f"embedding nodes into {vector_index_dir}")
    try:
        db = chromadb.PersistentClient(path=vector_index_dir)
        chroma_collection = db.get_or_create_collection("frag")
    except Exception as e:
        logger.error(f"error getting chroma collection: {e}")
        return False

    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    VectorStoreIndex(nodes, storage_context=storage_context)

    return True

