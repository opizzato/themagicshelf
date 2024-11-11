import json
import os
import logging
from llama_index.core.prompts import PromptTemplate
from llama_index.core.callbacks.base import CallbackManager
from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.llms import LLM
from llama_index.core.schema import (
    NodeWithScore,
    QueryBundle,
)
from typing import Optional, List

from src.classification.classification_store import ClassificationIndexStore

logger = logging.getLogger(__name__)

RETRIEVE_LEAVES_AND_TAGS_PROMPT = """\
Here is a hierarchical classification system:

{tree_schema}

Here is a classification tags system:

{tags_list}

Here is a query:
{query_str}

Define where to retrieve information to answer the query in the hierarchical classification and whare are the relevant tags.
Only answer with one of the provided hierarchical classification locations and tags.
If multiple locations or tags are possible, assign a score between 0 to 100 to each them.
Answer in a yaml format.
Do not add explanation or comments. Only answer with hierarchical classification location and tags. 

Example of answer:
hierarchical_classification_locations:
- xxx - xxx, score:80
- xxx - xxx, score:60
tags:
- xxx, score:90
- xxx, score:80

Answer:
"""


class ClassificationRetriever(BaseRetriever):

    def __init__(
        self,
        store: ClassificationIndexStore,
        llm: LLM,
        similarity_top_k: Optional[int] = 1,
        callback_manager: Optional[CallbackManager] = None,
        verbose: bool = False,
        log_dir: str=None,
    ) -> None:
        self._store = store
        self._llm = llm
        self._similarity_top_k = similarity_top_k
        self._log_dir = log_dir
        super().__init__(
            callback_manager=callback_manager, verbose=verbose
        )

    def _parse_locations_and_tags(self, input_str):
        if not input_str.strip():
            return None

        result = {'locations': [], 'tags': []}
        lines = input_str.strip().split('\n')
        current_section = None

        for line in lines:
            line = line.strip()
            if line.startswith('hierarchical_classification_locations:'):
                current_section = 'locations'
            elif line.startswith('tags:'):
                current_section = 'tags'
            elif line and current_section:
                if current_section == 'locations':
                    location, score = line.split(', score:')
                    result['locations'].append({'location': location.strip('- '), 'score': int(score)})
                elif current_section == 'tags':
                    tag, score = line.split(', score:')
                    result['tags'].append({'tag': tag.strip('- '), 'score': int(score)})

        if not result['locations'] or not result['tags']:
            return None

        return result


    def _retrieve(
        self,
        query_bundle: QueryBundle,
    ) -> List[NodeWithScore]:
        """Retrieve nodes."""

        prompt = PromptTemplate(template=RETRIEVE_LEAVES_AND_TAGS_PROMPT)

        tree_summary_node_ids = [self._store._tree_summary[location] for location in self._store._tree_schema]
        logger.info(f"tree_summary_node_ids: {tree_summary_node_ids=}")
        tree_summary_nodes = self._store.get_nodes(tree_summary_node_ids)
        tree_str = "\n".join(
            [
                f"{node.metadata['summary_for_tree_location']}\nLocation summary: {node.text}\n"
                for node in tree_summary_nodes
            ]
        )

        # save prompt to file
        if self._log_dir is not None:
            with open(os.path.join(self._log_dir, "classification_retriever_locations_prompt.txt"), "w") as f:
                f.write(prompt.format(
                    tree_schema=tree_str,
                    tags_list=self._store._tags_list,
                    query_str=query_bundle.query_str,
                ))

        locations_and_tags = self._llm.predict(
            prompt,
            tree_schema=tree_str,
            tags_list=self._store._tags_list,
            query_str=query_bundle.query_str,
            timeout=10,
        )
        logger.info(f"retrived locations and tags: \n{locations_and_tags}")

        # save response
        if self._log_dir is not None:
            query_and_locations_and_tags = f"query: {query_bundle.query_str}\n\n{locations_and_tags}"
            with open(os.path.join(self._log_dir, "classification_retriever_locations_result.txt"), "w") as f:
                f.write(query_and_locations_and_tags)

        # parse response
        locations_and_tags_parsed = self._parse_locations_and_tags(locations_and_tags)

        # save parsed response
        if self._log_dir is not None:
            with open(os.path.join(self._log_dir, "classification_retriever_locations_parsed.txt"), "w") as f:
                f.write(str(locations_and_tags_parsed))

        # take top k locations and tags
        top_k_locations = sorted(locations_and_tags_parsed['locations'], key=lambda x: x['score'], reverse=True)[:self._similarity_top_k]
        top_k_tags = sorted(locations_and_tags_parsed['tags'], key=lambda x: x['score'], reverse=True)[:self._similarity_top_k]

        # filter "not found" or invalid locations
        invalid_locations = list(filter(lambda x: x['location'] not in self._store._tree_schema, top_k_locations))
        if len(invalid_locations) > 0:
            logger.error(f"Classification retriever: {invalid_locations=}")
        top_k_locations = list(filter(lambda x: x['location'] in self._store._tree_schema, top_k_locations))
        top_k_tags = list(filter(lambda x: x['tag'] in self._store._tags_list, top_k_tags))
        
        # possibly augment partial locations with full locations
        top_k_locations = [{'location': full_location, 'score': l['score']}
                           for l in top_k_locations 
                           for full_location in [fl for fl in self._store._tree_schema if fl.startswith(l['location'])]]

        # todo: keep scores
        locations_ids = [id for location in top_k_locations for id in self._store._tree[location['location']]]
        tags_ids = [id for tag in top_k_tags for id in self._store._tags[tag['tag']]]

        locations_nodes = self._store.get_nodes(locations_ids)
        tags_nodes = self._store.get_nodes(tags_ids)

        # save top k locations and tags ids
        if self._log_dir is not None:
            with open(os.path.join(self._log_dir, "classification_retriever_locations_top_k_nodes.json"), "w") as f:
                data = {
                    'locations': [{'id': n.id_, 'text': n.text} for n in locations_nodes],
                    'tags': [{'id': n.id_, 'text': n.text} for n in tags_nodes]
                }
                json.dump(data, f, indent=4)

        retrieved_ids = list(set([id for id in locations_ids if id in tags_ids]))
        nodes = self._store.get_nodes(retrieved_ids)

        return [NodeWithScore(node=node) for node in nodes]
