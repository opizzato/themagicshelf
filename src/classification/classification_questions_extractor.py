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
from llama_index.core.schema import BaseNode, TextNode, MetadataMode
from llama_index.core.settings import Settings
from llama_index.core.types import BasePydanticProgram

logger = logging.getLogger(__name__)


DEFAULT_CLASSIFICATION_GEN_TMPL = """\
Here is the context:
{context_str}

Provide a title and a list of 10 possible hiearchical classifications for the document.

Generate an short answer. Do not introduce the answer or the questions.

Answer:
"""


class ClassificationQuestionsExtractor(BaseExtractor):
    """
    Classification questions extractor. Node-level extractor.
    Extracts `classification_information` metadata field.
    """

    llm: SerializeAsAny[LLM] = Field(description="The LLM to use for classification.")
    # questions: int = Field(
    #     default=5,
    #     description="The number of questions to generate.",
    #     gt=0,
    # )
    prompt_template: str = Field(
        default=DEFAULT_CLASSIFICATION_GEN_TMPL,
        description="Prompt template to use when generating questions.",
    )
    embedding_only: bool = Field(
        default=True, description="Whether to use metadata for emebddings only."
    )

    def __init__(
        self,
        llm: Optional[LLM] = None,
        # TODO: llm_predictor arg is deprecated
        llm_predictor: Optional[LLM] = None,
        # questions: int = 5,
        prompt_template: str = DEFAULT_CLASSIFICATION_GEN_TMPL,
        embedding_only: bool = True,
        num_workers: int = DEFAULT_NUM_WORKERS,
        **kwargs: Any,
    ) -> None:
        """Init params."""
        # if questions < 1:
        #     raise ValueError("questions must be >= 1")

        super().__init__(
            llm=llm or llm_predictor or Settings.llm,
            # questions=questions,
            prompt_template=prompt_template,
            embedding_only=embedding_only,
            num_workers=num_workers,
            **kwargs,
        )

    @classmethod
    def class_name(cls) -> str:
        return "ClassificationExtractor"

    async def _aextract_questions_from_node(self, node: BaseNode) -> Dict[str, str]:
        """Extract questions from a node and return it's metadata dict."""
        if self.is_text_node_only and not isinstance(node, TextNode):
            return {}

        context_str = node.get_content(metadata_mode=MetadataMode.LLM)
        prompt = PromptTemplate(template=self.prompt_template)
        questions = await self.llm.apredict(
            prompt, context_str=context_str
        )

        return {"classification_information": questions.strip()}

    async def aextract(self, nodes: Sequence[BaseNode]) -> List[Dict]:
        questions_jobs = []
        for node in nodes:
            questions_jobs.append(self._aextract_questions_from_node(node))

        metadata_list: List[Dict] = await run_jobs(
            questions_jobs, show_progress=self.show_progress, workers=self.num_workers
        )

        return metadata_list


