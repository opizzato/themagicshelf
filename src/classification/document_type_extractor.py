import os
import logging
from typing import Any, Callable, Dict, List, Optional, Sequence, cast

from llama_index.core.async_utils import DEFAULT_NUM_WORKERS, run_jobs
from llama_index.core.bridge.pydantic import (
    Field,
    PrivateAttr,
    SerializeAsAny,
)
from llama_index.core.extractors.interface import BaseExtractor
from llama_index.core.llms.llm import LLM
from llama_index.core.prompts import PromptTemplate
from llama_index.core.schema import BaseNode, TextNode
from llama_index.core.settings import Settings
from llama_index.core.types import BasePydanticProgram

logger = logging.getLogger(__name__)

DEFAULT_TYPE_EXTRACTION_PROMPT = """\
Here is a list of information about the content of a document:

{context_str}

Define the document type as a tag that best describes the type of content of the document.
A type can be for exemple "encyclopedic-article", "scientific-paper", "biography", "financial-report", "news", "story", etc.
 
Do not use general types like "book", "article", "document", etc. 
Be as specific as possible about the content of the document.
 
Return the type. Multiple types are not possible. \
Do not add explanation or comments, only the type.
 
Example of answer:
biography

Answer:
"""

class DocumentTypeExtractor(BaseExtractor):
    """
    Document type extractor. Node-level extractor.
    Extracts `types` metadata field.
    """

    llm: SerializeAsAny[LLM] = Field(description="The LLM to use for classification.")
    type_extraction_prompt_template: str = Field(
        default=DEFAULT_TYPE_EXTRACTION_PROMPT,
        description="Prompt template to use for creating the types system.",
    )
    use_fake_node_assignment: bool = Field(
        default=False,
        description="Use fake document type assignment.",
    )
    log_dir: str = Field(
        default="logs",
        description="Directory to store logs.",
    )

    def __init__(
        self,
        llm: Optional[LLM] = None,
        type_extraction_prompt_template: str = DEFAULT_TYPE_EXTRACTION_PROMPT,
        num_workers: int = DEFAULT_NUM_WORKERS,
        use_fake_node_assignment: bool = False,
        log_dir: str = "logs",
        **kwargs: Any,
    ) -> None:
        """Init params."""
        super().__init__(
            llm=llm or Settings.llm,
            type_extraction_prompt_template=type_extraction_prompt_template,
            num_workers=num_workers,
            use_fake_node_assignment=use_fake_node_assignment,
            log_dir=log_dir,
            **kwargs,
        )

    @classmethod
    def class_name(cls) -> str:
        return "TypeExtractor"

    async def _aassign_type_to_node(self, node: BaseNode) -> Dict:
        if self.use_fake_node_assignment:
            return {"classification_location_and_tags": "fake_type"}
        type_str = await self.llm.apredict(
            PromptTemplate(template=self.type_extraction_prompt_template),
            context_str=node.metadata.get("classification_information", ""),
            timeout=10,
        )
        logger.info(f"type: {type_str}")
        return {"type": type_str}

    def group_nodes_by_groups_of_size(self, nodes: Sequence[BaseNode], group_size: int) -> List[List[BaseNode]]:
        # todo: use iter_batch
        return [nodes[i:i+group_size] for i in range(0, len(nodes), group_size)]

    async def aextract(self, nodes: Sequence[BaseNode]) -> List[Dict]:

        questions_jobs = []
        for node in nodes:
            questions_jobs.append(self._aassign_type_to_node(node))

        metadata_list: List[Dict] = await run_jobs(
            questions_jobs, show_progress=self.show_progress, workers=self.num_workers
        )

        return metadata_list



