"""Cascade summary index.

A data structure where LlamaIndex stores the summary per document, 
with all intermediate summaries and maps
the summary to the underlying Nodes.
This summary can be used for retrieval.

"""

import logging
from collections import defaultdict
from enum import Enum
import re
from typing import Any, Dict, List, Optional, Sequence, Union, cast

from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.base.response.schema import Response
from llama_index.core.data_structs.document_summary import IndexDocumentSummary
from llama_index.core.indices.document_summary.base import DocumentSummaryIndex
from llama_index.core.indices.utils import embed_nodes
from llama_index.core.llms.llm import LLM
from llama_index.core.response_synthesizers import (
    BaseSynthesizer,
    ResponseMode,
    get_response_synthesizer,
)
from llama_index.core.schema import (
    BaseNode,
    IndexNode,
    NodeRelationship,
    NodeWithScore,
    RelatedNodeInfo,
    TextNode,
)
from llama_index.core.settings import Settings
from llama_index.core.storage.docstore.types import RefDocInfo
from llama_index.core.storage.storage_context import StorageContext
from llama_index.core.utils import get_tqdm_iterable
from llama_index.core.vector_stores.types import BasePydanticVectorStore

from src.run.utils import add_custom_metadata, copy_metadata_from_node

logger = logging.getLogger(__name__)


DEFAULT_SUMMARY_QUERY = (
    "Describe what the provided text is about. "
    "Also describe some of the questions that this text can answer. "
)


def parse_markdown_title(text: str) -> str:

    # get the first line
    first_line = text.split('\n')[0]

    # look for a markdown title
    match = re.search(r'^# (.*)', first_line)
    if match:
        return match.group(0).replace('#', '').strip()

    # look for a bolded first group of words
    match = re.search(r'^(.*?)(\*\*.*)', first_line)
    if match:
        return match.group(0).replace('**', '').strip()
    
    # otherwise take the first 5 words
    return " ".join(first_line.split()[:5]) + "..."


class CascadeSummaryIndex(DocumentSummaryIndex):
    """Cascade Summary Index.

    Args:
        same as DocumentSummaryIndex

    """

    def __init__(
        self,
        nodes: Optional[Sequence[BaseNode]] = None,
        objects: Optional[Sequence[IndexNode]] = None,
        index_struct: Optional[IndexDocumentSummary] = None,
        llm: Optional[LLM] = None,
        embed_model: Optional[BaseEmbedding] = None,
        storage_context: Optional[StorageContext] = None,
        response_synthesizer: Optional[BaseSynthesizer] = None,
        summary_query: str = DEFAULT_SUMMARY_QUERY,
        show_progress: bool = False,
        embed_summaries: bool = True,
        **kwargs: Any,
    ) -> None:
        """Initialize params."""
        super().__init__(
            nodes=nodes,
            objects=objects,
            index_struct=index_struct,
            llm=llm,
            embed_model=embed_model,
            storage_context=storage_context,
            response_synthesizer=response_synthesizer,
            summary_query=summary_query,
            show_progress=show_progress,
            embed_summaries=embed_summaries,
            **kwargs,
        )

    def _add_nodes_to_index(
        self,
        index_struct: IndexDocumentSummary,
        nodes: Sequence[BaseNode],
        show_progress: bool = False,
    ) -> None:
        """Add nodes to index."""
        doc_id_to_nodes = defaultdict(list)
        for node in nodes:
            if node.ref_doc_id is None:
                raise ValueError(
                    "ref_doc_id of node cannot be None when building a document "
                    "summary index"
                )
            doc_id_to_nodes[node.ref_doc_id].append(node)

        summary_node_dict = {}
        items = doc_id_to_nodes.items()
        iterable_with_progress = get_tqdm_iterable(
            items, show_progress, "Summarizing documents"
        )

        for doc_id, nodes in iterable_with_progress:
            nodes_with_scores = [NodeWithScore(node=n) for n in nodes]
            # get the summary for each doc_id
            summary_response = self._response_synthesizer.synthesize(
                query=self._summary_query,
                nodes=nodes_with_scores,
            )
            summary_response = cast(Response, summary_response)
            docid_first_node = doc_id_to_nodes.get(doc_id, [TextNode()])[0]

            # the root summary node is the first node in the source_nodes,
            # set the relationship and metadata for the root summary node
            root_node = summary_response.source_nodes[0].node
            root_node.relationships[NodeRelationship.SOURCE] = RelatedNodeInfo(node_id=doc_id)

            # update metadata
            copy_metadata_from_node(root_node, docid_first_node)
            add_custom_metadata(root_node, {
                "size_in_chunks": len(nodes),
                "title": parse_markdown_title(root_node.text),
            })

            summary_node_dict[doc_id] = root_node

            source_nodes = [n.node for n in summary_response.source_nodes]
            self.docstore.add_documents(source_nodes)
            logger.info(f"> Generated root summary for doc {doc_id}: " f"{summary_response.response}")
            logger.info(f"> Generated {len(summary_response.source_nodes)-1} intermediate summaries for doc {doc_id}")

        for doc_id, nodes in doc_id_to_nodes.items():
            index_struct.add_summary_and_nodes(summary_node_dict[doc_id], nodes)

        if self._embed_summaries:
            summary_nodes = list(summary_node_dict.values())
            id_to_embed_map = embed_nodes(
                summary_nodes, self._embed_model, show_progress=show_progress
            )

            summary_nodes_with_embedding = []
            for node in summary_nodes:
                node_with_embedding = node.model_copy()
                node_with_embedding.embedding = id_to_embed_map[node.node_id]
                summary_nodes_with_embedding.append(node_with_embedding)
            self._vector_store.add(summary_nodes_with_embedding)

