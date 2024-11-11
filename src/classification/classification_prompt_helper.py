"""Classification prompt helper that repack chunks while keeping link to original chunks.
"""

import logging
from typing import Callable, List, Optional, Sequence

from llama_index.core.constants import DEFAULT_CONTEXT_WINDOW, DEFAULT_NUM_OUTPUTS
from llama_index.core.llms.llm import LLM
from llama_index.core.prompts import BasePromptTemplate
from llama_index.core.schema import BaseNode
from llama_index.core.indices.prompt_helper import PromptHelper

DEFAULT_PADDING = 5
DEFAULT_CHUNK_OVERLAP_RATIO = 0.1

logger = logging.getLogger(__name__)


class ClassificationPromptHelper(PromptHelper):
    """Classification prompt helper.

    This prompt helper repacks chunks while keeping link to original chunks.

    Args:
        same as PromptHelper
    """

    def __init__(
        self,
        context_window: int = DEFAULT_CONTEXT_WINDOW,
        num_output: int = DEFAULT_NUM_OUTPUTS,
        chunk_overlap_ratio: float = DEFAULT_CHUNK_OVERLAP_RATIO,
        chunk_size_limit: Optional[int] = None,
        tokenizer: Optional[Callable[[str], List]] = None,
        separator: str = " ",
    ) -> None:
        """Init params."""
        super().__init__(
            context_window=context_window,
            num_output=num_output,
            chunk_overlap_ratio=chunk_overlap_ratio,
            chunk_size_limit=chunk_size_limit,
            tokenizer=tokenizer,
            separator=separator,
        )

    @classmethod
    def class_name(cls) -> str:
        return "ClassificationPromptHelper"

    def repack_nodes(
        self,
        prompt: BasePromptTemplate,
        text_chunks: Sequence[BaseNode],
        padding: int = DEFAULT_PADDING,
        llm: Optional[LLM] = None,
    ) -> List[BaseNode]:
        """Repack text chunks to fit available context window.

        This will combine text chunks into consolidated chunks
        that more fully "pack" the prompt template given the context_window.

        Creates new nodes with relationships to the original nodes.
        """
        text_splitter = self.get_text_splitter_given_prompt(
            prompt, padding=padding, llm=llm
        )
        combined_str = "\n\n".join([c.strip() for c in text_chunks if c.strip()])
        return text_splitter.split_text(combined_str)
