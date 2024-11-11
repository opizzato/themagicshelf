import os
import logging
import re
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

CLASSIFICATION_SYSTEM_EXTRACTION_PROMPT = """\
Here is a list of categorisation information, each related to one document:
{context_str}

Define the most user-friendly and well balanced hierarchical classification system for these documents \
and define the most user-friendly tag system that groups these documents in another way than the hierarchical classification.

The tags should be different from the leaves of the hierarchical classification.
Do not repeat leaves in the hierarchical classification.
Avoid general categories like "General Information", prefer specific categories.

Return the hierarchical classification and the tags in a yaml format.
For each classification and tag, add in parenthesis the number of documents in the document set that belong to this classification/tag.
Do not add introduction, explanation or comments, only answer with the hierarchical classification and the tags.

Example of answer:

hierarchical_classification:
- Science (3)
  - Physics (2)
  - Chemistry (1)
- History (2)
  - Ancient History (1)
  - Modern History (1)
tags:
- Essay (1)
- Report (3)
- Poem (1)

Answer:
"""

CLASSIFICATION_SYSTEM_EXTRACTION_PROMPT_WITH_PREVIOUS_TYPE = """
Here is a list of categorisation information each about a new document:
{context_str}

Here is the previous hierarchical classification system and the tags:
{previous_type_str}

If the new documents can be classified in the previous system, \
do not change the classification and tags system and answer with the previous one.

If the new documents cannot be classified in the previous system, \
update the classification and tags system to include the new documents.

The hierarchical classification system should stay balanced and well spread.
The tag system should be different from the leaves of the hierarchical classification.
Do not repeat leaves in the hierarchical classification.
Avoid general categories like "General Information", prefer specific categories.

Return the hierarchical classification and the tags in a yaml format.
For each classification and tag, add in parenthesis the number of documents in the document set that belong to this classification/tag.
Do not add introduction, explanation or comments, only answer with the hierarchical classification and the tags.

Example of answer:

hierarchical_classification:
- Science (3)
  - Physics (2)
  - Chemistry (1)
- History (2)
  - Ancient History (1)
  - Modern History (1)
tags:
- Essay (1)
- Report (3)
- Poem (1)

Answer:
"""


DEFAULT_TYPE_ASSIGN_PROMPT = """\
Here is a list of categorisation information related to a document:
{context_str}

Here is a classification system and tag system in yaml format that can be used to classify this document:
{category_tree_str}

Assign the most relevant location in the classification and the most relevant tags to the document. \
Do not assign to a classification branch that is not a leaf of the classification. \
Return the location in the classification and the tags in yaml format. \
Do not add explanation or comments.

Example of answer:
hierarchical_classification:
- Science
  - Physics
tags:
- Essay
- 2022
- Draft

Answer:
"""

class ClassificationAssignementExtractor(BaseExtractor):
    """
    Classification assignement extractor. Node-level extractor.
    Extracts `classification_location_and_tags` metadata field.
    """

    llm: SerializeAsAny[LLM] = Field(description="The LLM to use for classification.")
    type_extraction_prompt_template: str = Field(
        default=CLASSIFICATION_SYSTEM_EXTRACTION_PROMPT,
        description="Prompt template to use for creating the classification and tags system.",
    )
    type_extraction_prompt_template_with_previous_type: str = Field(
        default=CLASSIFICATION_SYSTEM_EXTRACTION_PROMPT_WITH_PREVIOUS_TYPE,
        description="Prompt template to use for creating the classification and tags system not far from a previosu one.",
    )
    type_assign_prompt_template: str = Field(
        default=DEFAULT_TYPE_ASSIGN_PROMPT,
        description="Prompt template to use when assigning types to nodes.",
    )
    use_fake_node_assignment: bool = Field(
        default=False,
        description="Use fake node assignment.",
    )
    predefined_tree_and_tags: str = Field(
        default="",
        description="Use predefined tree and tags.",
    )
    log_dir: Optional[str] = Field(
        default="logs",
        description="Directory to store logs.",
    )

    def __init__(
        self,
        llm: Optional[LLM] = None,
        type_extraction_prompt_template: str = CLASSIFICATION_SYSTEM_EXTRACTION_PROMPT,
        type_assign_prompt_template: str = DEFAULT_TYPE_ASSIGN_PROMPT,
        num_workers: int = DEFAULT_NUM_WORKERS,
        use_fake_node_assignment: bool = False,
        predefined_tree_and_tags: str = "",
        log_dir: str = "logs",
        **kwargs: Any,
    ) -> None:
        """Init params."""
        super().__init__(
            llm=llm or Settings.llm,
            type_extraction_prompt_template=type_extraction_prompt_template,
            type_assign_prompt_template=type_assign_prompt_template,
            num_workers=num_workers,
            use_fake_node_assignment=use_fake_node_assignment,
            predefined_tree_and_tags=predefined_tree_and_tags,
            log_dir=log_dir,
            **kwargs,
        )

    @classmethod
    def class_name(cls) -> str:
        return "TypeExtractor"

    async def _aassign_type_to_node(self, node: BaseNode, category_tree_str: str) -> Dict:
        if self.use_fake_node_assignment:
            return {"classification_location_and_tags": "fake_type"}
        classification_location_and_tags = await self.llm.apredict(
            PromptTemplate(template=self.type_assign_prompt_template),
            context_str=node.metadata.get("classification_information", ""),
            category_tree_str=category_tree_str,
            timeout=10,
        )
        logger.info(f"classification_location_and_tags: {classification_location_and_tags}")
        return {"classification_location_and_tags": classification_location_and_tags}

    def group_nodes_by_groups_of_size(self, nodes: Sequence[BaseNode], group_size: int) -> List[List[BaseNode]]:
        # todo: use iter_batch
        return [nodes[i:i+group_size] for i in range(0, len(nodes), group_size)]

    def extract_tree_and_tags(self, nodes: Sequence[BaseNode]) -> str:

        if self.predefined_tree_and_tags != "":
            logger.info(f"use predefined category_tree_str: {self.predefined_tree_and_tags}")
            category_tree_str = self.predefined_tree_and_tags

            # save classification and tags system
            if self.log_dir is not None:
                with open(os.path.join(self.log_dir, "classification_extraction_result.txt"), "w") as f:
                    f.write(category_tree_str)

            return category_tree_str

        category_tree_str = None
        node_groups = self.group_nodes_by_groups_of_size(nodes, 20)
        for i, node_group in enumerate(node_groups):

            log_flags = f"{i}_{len(node_group)}"

            # collect classification_information metadata from nodes
            classification_information = [node.metadata.get("classification_information", "") for node in node_group]

            # prompt to ask llm to define a category tree and tags
            if category_tree_str is None:
                prompt = PromptTemplate(template=self.type_extraction_prompt_template)
                prompt_params = {'context_str': classification_information}
            else:
                prompt = PromptTemplate(template=self.type_extraction_prompt_template_with_previous_type)
                prompt_params = {'context_str': classification_information, 'previous_type_str': category_tree_str}

            # save prompt to file
            if self.log_dir is not None:
                with open(os.path.join(self.log_dir, f"classification_extraction_prompt_{log_flags}.txt"), "w") as f:
                    f.write(prompt.format(**prompt_params))

            category_tree_str = self.llm.predict(
                prompt,
                **prompt_params,
                timeout=10,
            )
            logger.info(f"extracted category_tree_str at group {i}: {category_tree_str}")

            # save result at group i
            if self.log_dir is not None:
                with open(os.path.join(self.log_dir, f"classification_extraction_result_{log_flags}.txt"), "w") as f:
                    f.write(category_tree_str)

        # save classification and tags system
        if self.log_dir is not None:
            with open(os.path.join(self.log_dir, "classification_extraction_result.txt"), "w") as f:
                f.write(category_tree_str)

        # exit(1)

        return category_tree_str


    def parse_tree_and_tags(self, category_tree_str: str) -> str:
        
        # remove all between parenthesis
        category_tree_str = re.sub(r'\([^)]*\)', '', category_tree_str)
        return category_tree_str

    def fill_intermediate_branches(self, category_tree_str: str) -> str:
        category_tree = category_tree_str.split("\n")
        new_category_tree = []
        for i, line in enumerate(category_tree):
            other_lines = category_tree[:i] + category_tree[i+1:]
            if any(other_line.startswith(line) for other_line in other_lines):
                new_category_tree.append(line + " - Other")
            else:
                new_category_tree.append(line)
        return "\n".join(new_category_tree)

    async def aextract(self, nodes: Sequence[BaseNode]) -> List[Dict]:

        category_tree_str = self.extract_tree_and_tags(nodes)
        category_tree_str = self.parse_tree_and_tags(category_tree_str)
        category_tree_str = self.fill_intermediate_branches(category_tree_str)
        
        questions_jobs = []
        for node in nodes:
            questions_jobs.append(self._aassign_type_to_node(node, category_tree_str))

        metadata_list: List[Dict] = await run_jobs(
            questions_jobs, show_progress=self.show_progress, workers=self.num_workers
        )

        return metadata_list



