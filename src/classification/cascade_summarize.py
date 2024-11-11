import asyncio
import logging
import random
from typing import Any, List, Optional, Sequence

from llama_index.core.async_utils import run_async_tasks
from llama_index.core.callbacks.base import CallbackManager
from llama_index.core.indices.prompt_helper import PromptHelper
from llama_index.core.llms import LLM
from llama_index.core.prompts import BasePromptTemplate
from llama_index.core.prompts.default_prompt_selectors import (
    DEFAULT_TREE_SUMMARIZE_PROMPT_SEL,
)
from llama_index.core.bridge.pydantic import (
    Field,
    PrivateAttr,
    SerializeAsAny,
)
from llama_index.core.prompts.mixin import PromptDictType
from llama_index.core.response_synthesizers import TreeSummarize
from llama_index.core.response_synthesizers.base import empty_response_generator
from llama_index.core.types import RESPONSE_TEXT_TYPE, BaseModel
from llama_index.core.callbacks.schema import CBEventType, EventPayload
from llama_index.core.base.response.schema import (
    RESPONSE_TYPE,
    PydanticResponse,
    Response,
    StreamingResponse,
    AsyncStreamingResponse,
)
from llama_index.core.instrumentation.events.synthesis import (
    SynthesizeStartEvent,
    SynthesizeEndEvent,
)
from llama_index.core.schema import (
    NodeRelationship,
    RelatedNodeInfo,
    TextNode,
    MetadataMode,
    NodeWithScore,
    QueryBundle,
    QueryType,
)
import llama_index.core.instrumentation as instrument

dispatcher = instrument.get_dispatcher(__name__)

logger = logging.getLogger(__name__)

def take_random_max_chunks(node_chunks: Sequence[NodeWithScore], use_max_chunks: Optional[int]):
    if use_max_chunks is not None:
        return random.sample(node_chunks, min(use_max_chunks, len(node_chunks)))
    return node_chunks


class CascadeSummarize(TreeSummarize):
    """
    Cascade summarize response builder.

    This response builder recursively merges text chunks and summarizes them
    as TreeSummarize does, but it also saves each intermediate summary in the index.

    More concretely, Response is composed of:
    - response: a string response containing the final summary
    - source_nodes: the list of nodes used to generate the summary from the input chunks nodes

    These source nodes are organized in a tree structure, with parent/child/next/previous relationships.
    The final summary is one of the nodes in the tree, with no parent.
    Leafs nodes refers to the original text chunks as children.

    Parent/child/next/previous relationships are stored as 'relationships' in the Node object.
    """
    use_max_chunks: Optional[int] = Field(
        default=None, description="The maximum number of chunks to use for the summary. All if None."
    )

    def __init__(
        self,
        llm: Optional[LLM] = None,
        callback_manager: Optional[CallbackManager] = None,
        prompt_helper: Optional[PromptHelper] = None,
        summary_template: Optional[BasePromptTemplate] = None,
        output_cls: Optional[BaseModel] = None,
        streaming: bool = False,
        use_async: bool = False,
        verbose: bool = False,
        use_max_chunks: int = None,
    ) -> None:
        super().__init__(
            llm=llm,
            callback_manager=callback_manager,
            prompt_helper=prompt_helper,
            summary_template=summary_template,
            output_cls=output_cls,
            streaming=streaming,
            use_async=use_async,
            verbose=verbose,
        )
        self.use_max_chunks = use_max_chunks

    def get_response_for_nodes(
        self,
        query_str: str,
        node_chunks: Sequence[NodeWithScore],
        additional_source_nodes: Optional[Sequence[NodeWithScore]] = None,
        **response_kwargs: Any,
    ) -> RESPONSE_TEXT_TYPE:
        """Get tree summarize response."""
        summary_template = self._summary_template.partial_format(query_str=query_str)

        # repack text_chunks so that each chunk fills the context window
        text_chunks=[
            n.node.get_content(metadata_mode=MetadataMode.LLM) 
            for n in take_random_max_chunks(node_chunks, self.use_max_chunks)
        ]
        logger.info(f"repacking {len(text_chunks)} chunks")
        text_chunks = self._prompt_helper.repack(
            summary_template, text_chunks=text_chunks
        )
        logger.info(f"repacked {len(text_chunks)} chunks")

        # if no additional source nodes from previous recursive calls, no need to keep track of the children
        summary_children = [n.id_ for n in node_chunks] if additional_source_nodes is not None else []

        # create new nodes with relationships to the original nodes
        summary_node_chunks = [
            NodeWithScore(
                node=TextNode(
                    text="", 
                    metadata={
                        'summary_children': summary_children,
                    },
                    excluded_llm_metadata_keys=['summary_children'],
                    excluded_embed_metadata_keys=['summary_children'],
                ),
                score=1.0
            ) for text_chunk in text_chunks
        ]

        if additional_source_nodes is None:
            additional_source_nodes = []
        else:
            additional_source_nodes.extend(node_chunks)

        if self._verbose:
            logger.info(f"{len(text_chunks)} text chunks after repacking")

        # give final response if there is only one chunk
        if len(text_chunks) == 1:
            response: RESPONSE_TEXT_TYPE
            if self._streaming:
                response_str = self._llm.stream(
                    summary_template, context_str=text_chunks[0], **response_kwargs
                )
            else:
                if self._output_cls is None:
                    response_str = self._llm.predict(
                        summary_template,
                        context_str=text_chunks[0],
                        **response_kwargs,
                    )
                else:
                    response_str = self._llm.structured_predict(  # type: ignore
                        self._output_cls,
                        summary_template,
                        context_str=text_chunks[0],
                        **response_kwargs,
                    )

            summary_node_chunks[0].node.text = response_str 
            source_nodes = summary_node_chunks + additional_source_nodes
            response = self._prepare_response_output(response_str, source_nodes)
            return response

        else:
            # summarize each chunk
            if self._use_async:
                if self._output_cls is None:
                    tasks = [
                        self._llm.apredict(
                            summary_template,
                            context_str=text_chunk,
                            **response_kwargs,
                        )
                        for text_chunk in text_chunks
                    ]
                else:
                    tasks = [
                        self._llm.astructured_predict(  # type: ignore
                            self._output_cls,
                            summary_template,
                            context_str=text_chunk,
                            **response_kwargs,
                        )
                        for text_chunk in text_chunks
                    ]

                summary_responses = run_async_tasks(tasks)

                if self._output_cls is not None:
                    summaries = [
                        summary.model_dump_json() for summary in summary_responses
                    ]
                else:
                    summaries = summary_responses
            else:
                if self._output_cls is None:
                    summaries = [
                        self._llm.predict(
                            summary_template,
                            context_str=text_chunk,
                            **response_kwargs,
                        )
                        for text_chunk in text_chunks
                    ]
                else:
                    summaries = [
                        self._llm.structured_predict(  # type: ignore
                            self._output_cls,
                            summary_template,
                            context_str=text_chunk,
                            **response_kwargs,
                        )
                        for text_chunk in text_chunks
                    ]
                    summaries = [summary.model_dump_json() for summary in summaries]

            for i, summary in enumerate(summaries):
                summary_node_chunks[i].node.text = summary
                if i > 0:
                    prev_node = RelatedNodeInfo(node_id=summary_node_chunks[i-1].node.id_)
                    summary_node_chunks[i].node.relationships[NodeRelationship.PREVIOUS] = prev_node
                if i < len(summaries) - 1:
                    next_node = RelatedNodeInfo(node_id=summary_node_chunks[i+1].node.id_)
                    summary_node_chunks[i].node.relationships[NodeRelationship.NEXT] = next_node

            # recursively summarize the summaries
            return self.get_response_for_nodes(
                query_str=query_str, node_chunks=summary_node_chunks, additional_source_nodes=additional_source_nodes, **response_kwargs
            )


    def synthesize(
        self,
        query: QueryType,
        nodes: List[NodeWithScore],
        additional_source_nodes: Optional[Sequence[NodeWithScore]] = None,
        **response_kwargs: Any,
    ) -> RESPONSE_TYPE:
        dispatcher.event(
            SynthesizeStartEvent(
                query=query,
            )
        )

        if len(nodes) == 0:
            if self._streaming:
                empty_response_stream = StreamingResponse(
                    response_gen=empty_response_generator()
                )
                dispatcher.event(
                    SynthesizeEndEvent(
                        query=query,
                        response=empty_response_stream,
                    )
                )
                return empty_response_stream
            else:
                empty_response = Response("Empty Response")
                dispatcher.event(
                    SynthesizeEndEvent(
                        query=query,
                        response=empty_response,
                    )
                )
                return empty_response

        if isinstance(query, str):
            query = QueryBundle(query_str=query)

        with self._callback_manager.event(
            CBEventType.SYNTHESIZE,
            payload={EventPayload.QUERY_STR: query.query_str},
        ) as event:
            response = self.get_response_for_nodes(
                query_str=query.query_str,
                node_chunks=nodes,
                **response_kwargs,
            )

            # additional_source_nodes = additional_source_nodes or []
            # source_nodes = list(nodes) + list(additional_source_nodes)
            # response = self._prepare_response_output(response_str, source_nodes)

            event.on_end(payload={EventPayload.RESPONSE: response})

        dispatcher.event(
            SynthesizeEndEvent(
                query=query,
                response=response,
            )
        )

        

        return response
