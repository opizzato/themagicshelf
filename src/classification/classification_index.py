import logging
from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.llms import LLM
from llama_index.core.schema import (
    BaseNode,
)
from typing import Sequence

from src.classification.classification_retriever import ClassificationRetriever
from src.classification.classification_store import ClassificationIndexStore

logger = logging.getLogger(__name__)


class ClassificationIndex:

    def __init__(
        self,
        nodes: Sequence[BaseNode],
        store: ClassificationIndexStore,
        llm: LLM,
        log_dir: str=None,
    ) -> None:
        """Initialize params."""
        self._nodes = nodes
        self._store = store
        self._llm = llm
        self._log_dir = log_dir

        if self._store._tree == {}:
            self._build_index_from_nodes()

    def _build_index_from_nodes(self):
        for node in self._nodes:
            self._store.insert_node(node)

    def persist(self):
        self._store.persist()
        logger.info(f"Classification index persisted in {self._store._persist_path}")

    def as_retriever(
        self,
        top_k: int=5,
    ) -> BaseRetriever:
        
        return ClassificationRetriever(store=self._store, llm=self._llm, log_dir=self._log_dir, similarity_top_k=top_k)

    def from_store(llm: LLM, store: ClassificationIndexStore, log_dir: str=None):

        self = ClassificationIndex(nodes=[], store=store, llm=llm, log_dir=log_dir)
        return self
    