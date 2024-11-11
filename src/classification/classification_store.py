import json
import os
import yaml
import logging
import re
from llama_index.core.schema import (
    BaseNode,
    TextNode,
    NodeRelationship
)
from typing import Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)

NodeId = str

class ClassificationIndexStore:

    def __init__(
        self,
        persist_path: str=None,
    ) -> None:
        """Initialize params."""
        self._tree: Dict[str, List[NodeId]] = {}
        self._tree_schema: List[str] = []
        self._tree_summary: Dict[str, NodeId] = {}
        self._tree_path_summary: Dict[str, NodeId] = {}
        self._tags: Dict[str, List[NodeId]] = {}
        self._tags_list: List[str] = []
        self._types: List[str] = []
        self._types_prompt: Dict[str, str] = {}
        self._nodes: Sequence[BaseNode] = []
        self._persist_path = persist_path
    

    def insert_node(self, node: BaseNode) -> bool:

        metadata = 'classification_location_and_tags'
        classification_metadata = node.metadata.get(metadata, None)
        classification = self._parse_classification_metadata(classification_metadata, log_prefix=f"{node.id_=}: ")
        if classification is None:
            logger.error(f"can not parse classifcation for node {metadata=} {node=}")
            classification = ("unknown", ["unknown"])
        tree_location, tags = classification
        self._update_tree(tree_location, node)
        self._update_tags(tags, node)

        node.metadata["classification_tree_location"] = tree_location
        node.metadata["classification_tags"] = tags

        self._nodes.append(node)
        return True

    def update_path_summary_nodes(self, nodes: Sequence[BaseNode]):

        for node in nodes:
            location = node.metadata["summary_for_tree_location"]
            self._tree_path_summary[location] = node.id_
            self._nodes.append(node)

    def update_summary_nodes(self, nodes: Sequence[BaseNode]):

        for node in nodes:
            location = node.metadata["summary_for_tree_location"]
            self._tree_summary[location] = node.id_
            self._nodes.append(node)
    
    def update_text_node(self, node: BaseNode):
        for self_node in self._nodes:
            if self_node.id_ == node.id_:
                self_node.text = node.text


    def _update_tree(self, tree_location: List[str], node: BaseNode):

        tree_location_str = ' - '.join(tree_location)
        self._tree[tree_location_str] = self._tree.get(tree_location_str, []) + [node.id_]

        self._tree_schema = list(sorted(self._tree.keys()))

    def _update_tags(self, tags: List[str], node: BaseNode):

        for tag in tags:
            self._tags[tag] = self._tags.get(tag, []) + [node.id_]

        self._tags_list = list(sorted(set(self._tags.keys())))

    def _parse_classification_metadata(self, data: Optional[str], log_prefix:str=""):
        
        if data is None:
            return None

        data_dict = yaml.safe_load(data)
        tree = data_dict['hierarchical_classification']
        if not isinstance(tree, list):
            logger.error(f"{log_prefix}error parsing metadata {data=}, {tree=} is not a string")
            return None
        if len(tree) != 1:
            logger.error(f"{log_prefix}error parsing metadata {data=}, {tree=} is not a list of 1, taking the first element of the list")

        tree_parsed = tree[0].split(' - ')
        tags_parsed = [str(tag) for tag in data_dict['tags']]
        return tree_parsed, tags_parsed

    def persist(self):

        if self._persist_path is not None:
            data = {
                'tree_schema': self._tree_schema, 
                'tag_list': self._tags_list,
                'tree_summary': self._tree_summary,
                'tree_path_summary': self._tree_path_summary,
                'tree': self._tree, 
                'tags': self._tags,
                'types': self._types,
                'types_prompt': self._types_prompt,
                'nodes': [n.to_dict() for n in self._nodes],
            }
            with open(self._persist_path, "w") as f:
                json.dump(data, f, indent=4)

    def from_store_path(persist_path: str):

        if not os.path.exists(persist_path):
            logger.error(f"store path {persist_path} does not exist")
            return None

        data = None
        with open(persist_path, "r") as f:
            data = json.load(f)

        self = ClassificationIndexStore()
        self._tree_schema = data['tree_schema']
        self._tags_list = data['tag_list']
        self._tree_summary = data.get('tree_summary', {})
        self._tree_path_summary = data.get('tree_path_summary', {})
        self._tree = data['tree']
        self._tags = data['tags']
        self._types = data.get('types', [])
        self._types_prompt = data.get('types_prompt', {})
        self._nodes = [TextNode.from_dict(n) for n in data['nodes']]
        self._persist_path = persist_path

        return self

    def get_nodes(
        self,
        ids: Optional[List[NodeId]] = None,
    ) -> List[TextNode]:
        """Get nodes with matching values."""
        if ids is None:
            return []
        return [n for n in self._nodes if n.id_ in ids]

    def get_tree_digraph_nodes_and_edges(self) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]:
        """
        Get nodes and edges for a digraph with unique identifiers.
        
        Returns:
            Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]: A tuple containing:
                - A list of nodes, each represented as (node_id, node_label)
                - A list of edges, each represented as (source_id, target_id)
        """

        nodes: List[Tuple[str, str]] = [("root", "root")]
        edges: List[Tuple[str, str]] = []
        for branch, text_nodes in self._tree.items():
            branch_parts = branch.split(' - ')
            for part_index, part in enumerate(branch_parts):
                node_id = ' - '.join(branch_parts[:part_index+1])
                node_label = part
                if node_id not in [node[0] for node in nodes]:
                    nodes.append((node_id, node_label))
                if part_index == 0:
                    # Connect first-level nodes to the root
                    edge = ("root", node_id)
                    if edge not in edges:
                        edges.append(edge)
                if part_index > 0:
                    prev_node_id = ' - '.join(branch_parts[:part_index])
                    edge = (prev_node_id, node_id)
                    if edge not in edges:
                        edges.append(edge)
            last_node_id = branch
            for text_node_id in text_nodes:
                if text_node_id in [node[0] for node in nodes]:
                    nodes.append((text_node_id, text_node_id))
                edges.append((last_node_id, text_node_id))
                
        return nodes, edges

    def get_tags_digraph_nodes_and_edges(self) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]:
        """
        Get nodes and edges for a digraph with unique identifiers.
        
        Returns:
            Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]: A tuple containing:
                - A list of nodes, each represented as (node_id, node_label)
                - A list of edges, each represented as (source_id, target_id)
        """

        nodes: List[Tuple[str, str]] = []
        edges: List[Tuple[str, str]] = []
        for tag, text_nodes in self._tags.items():
            node_id = tag
            node_label = tag
            nodes.append((node_id, node_label))
            for text_node_id in text_nodes:
                nodes.append((text_node_id, text_node_id))
                edges.append((node_id, text_node_id))
                
        return nodes, edges

    def get_node_id_summary(self, node_id: NodeId):
        """Get the summary for a node_id."""
        if node_id in self._tree_summary:
            return self._tree_summary[node_id]
        if node_id in self._tree_path_summary:
            return self._tree_path_summary[node_id]
        if node_id == "root":
            return self._tree_path_summary.get("")
        return None
    
    def get_path_summary_id(self, path: str):
        """Get the path summary for a path."""
        if path in self._tree_path_summary:
            return self._tree_path_summary[path]
        if path in self._tree_summary:
            return self._tree_summary[path]
        return None

    def get_node_text(self, node_id: NodeId):
        """Get the text for a node_id."""
        node = next((node for node in self._nodes if node.id_ == node_id), None)
        if node:
            return node.text
        return None

    def get_nodes_id_from_tree_location(self, tree_location: str):
        """Get the nodes_id for a tree_location."""
        return self._tree.get(tree_location, [])

    def get_tags(self):
        return self._tags_list

    def get_nodes_id_from_tag(self, tag: str):
        return self._tags.get(tag, [])

    def get_similar_nodes_id(self, node_id: NodeId):
        node = next((node for node in self._nodes if node.id_ == node_id), None)
        if node:
            return node.metadata.get("similar_ids", [])
        return []

    def get_node_filename(self, node_id: NodeId):
        node = next((node for node in self._nodes if node.id_ == node_id), None)
        if node:
            return node.metadata.get("file_name", "")
        return ""

    def get_node_url(self, node_id: NodeId):
        node = next((node for node in self._nodes if node.id_ == node_id), None)
        if node:
            return node.metadata.get("url", "")
        return ""
    
    def get_urls_from_run(self):
        return [node.metadata.get("url", "") for node in self._nodes]

    def get_all_tree_paths(self, add_empty_root: bool=False) -> List[str]:
        branches = self._tree.keys()
        paths = []
        for branch in branches:
            parts = branch.split(' - ')
            for i in range(len(parts)):
                paths.append(' - '.join(parts[:i+1]))
        paths = list(set(paths))
        if add_empty_root:
            paths.insert(0, "")
        return paths

    def get_sub_category_tree(self, category: str, category_full_path: str):
        category_full_path_noroot = category_full_path.replace("root - ", "") if category_full_path != "root" else ""
        prefix = category_full_path_noroot + " - " if category_full_path_noroot != "" else ""
        sub_branches = [
            branch[len(prefix):].split(' - ')[0]
            for branch in self._tree_schema 
            if branch.startswith(prefix) and branch != prefix
        ]
        sub_branches = list(set(sub_branches))
        sub_categories = [
            self.get_sub_category_tree(sub_branch, category_full_path + ' - ' + sub_branch)
            for sub_branch in sub_branches
        ]
        document_ids = self.get_nodes_id_from_tree_location(category_full_path_noroot)

        documents = [
            {
                "id": node.id_,
                "title": node.metadata.get("title", ""),
                "summary": node.text,
                "tags": node.metadata.get("classification_tags", []),
                "relatedDocuments": node.metadata.get("similar_ids", []),
                "source_node_id": node.relationships[NodeRelationship.SOURCE].node_id
            }
            for node in self._nodes if node.id_ in document_ids
        ]
        documents = list(sorted(documents, key=lambda x: x["id"]))
        sub_categories = list(sorted(sub_categories, key=lambda x: x["id"]))
        category_summary_id = self.get_path_summary_id(category_full_path_noroot)
        category_summary = self.get_node_text(category_summary_id) if category_summary_id else ""
        return {
            "id": category_full_path,
            "name": category,
            "introduction": category_summary,
            "subcategories": sub_categories,
            "documents": documents
        }

    def get_category_tree(self):

        res = self.get_sub_category_tree("root", "root")
        return res
