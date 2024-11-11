import json
import logging
import os
from llama_index.core.prompts import PromptTemplate
from llama_index.core.callbacks.base import CallbackManager
from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.llms import LLM
from llama_index.core.schema import (
    NodeWithScore,
    QueryBundle,
)
from typing import Optional, List
 
logger = logging.getLogger(__name__)


class ComposeRetriever(BaseRetriever):
 
    def __init__(
        self,
        embeddings_retriever: BaseRetriever,
        classification_retriever: BaseRetriever,
        callback_manager: Optional[CallbackManager] = None,
        verbose: bool = False,
        log_dir: str=None,
    ) -> None:
        self._embeddings_retriever = embeddings_retriever
        self._classification_retriever = classification_retriever
        self._log_dir = log_dir
        super().__init__(
            callback_manager=callback_manager, verbose=verbose
        )
 
    def _retrieve(
        self,
        query_bundle: QueryBundle,
    ) -> List[NodeWithScore]:
        """Retrieve nodes."""
 
        def log_retrieved_nodes(retriever_name: str, retrieved_nodes: List[NodeWithScore]):
            logger.info(f"{retriever_name}: nb nodes: {len(retrieved_nodes)}")
            logger.info(f"{retriever_name}: nodes ids: {[node.id_ for node in retrieved_nodes]}")
            logger.info(f"{retriever_name}: nodes text: {[node.text for node in retrieved_nodes]}")

        embeddings_retrieved_nodes = self._embeddings_retriever._retrieve(query_bundle=query_bundle)
        log_retrieved_nodes("embeddings_retriever", embeddings_retrieved_nodes)

        classification_retrieved_nodes = self._classification_retriever._retrieve(query_bundle=query_bundle)
        log_retrieved_nodes("classification_retriever", classification_retrieved_nodes)

        # save retrieved nodes
        if self._log_dir is not None:
            with open(os.path.join(self._log_dir, "compose_retriever_retrieved_nodes.json"), "w", encoding="utf-8") as f:
                data = {
                    'embeddings': [{'id': n.id_, 'text': n.text} for n in embeddings_retrieved_nodes],
                    'classification': [{'id': n.id_, 'text': n.text} for n in classification_retrieved_nodes]
                }
                json.dump(data, f, indent=4)

        nodes = embeddings_retrieved_nodes + classification_retrieved_nodes
        return nodes