import json
import os
import logging
from typing import Dict, List
from llama_index.core.schema import (
    Document,
    BaseNode,
)

logger = logging.getLogger(__name__)


def add_custom_metadata(node, metadata: Dict[str, str]):
    node.metadata = {**node.metadata, **metadata}
    exclude_metadata_keys(node, list(metadata.keys()))


def copy_metadata_from_node(node, other_node: BaseNode):
    node.metadata = {**node.metadata, **other_node.metadata}
    node.excluded_llm_metadata_keys = node.excluded_llm_metadata_keys + other_node.excluded_llm_metadata_keys
    node.excluded_embed_metadata_keys = node.excluded_embed_metadata_keys + other_node.excluded_embed_metadata_keys


def exclude_metadata_keys(node, keys):
    node.excluded_embed_metadata_keys = node.excluded_embed_metadata_keys + keys
    node.excluded_llm_metadata_keys = node.excluded_llm_metadata_keys + keys


def base_dir_for_run(run_id: str, base_dir: str="output"):
    return os.path.join(base_dir, f"run_{run_id}")


def load_nodes(filename: str):
    nodes = []
    if not os.path.exists(filename):
        return nodes
    with open(filename, "r") as f:
        nodes = [Document.from_dict(n) for n in json.load(f)]
    logger.info(f"Loaded {len(nodes)} nodes")
    return nodes


def create_folders_for_filepath(filepath):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    logger.info(f"Created folders for {filepath}")


def save_nodes(nodes, filename: str):
    create_folders_for_filepath(filename)
    with open(filename, "w") as f:
        json.dump([n.to_dict() for n in nodes], f, indent=4)
    logger.info(f"Saved {len(nodes)} nodes to {filename}")



