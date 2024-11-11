import random
import logging
import os
import shutil
from typing import List, Optional
from llama_index.readers.web import SimpleWebPageReader
from llama_index.core.schema import BaseNode, Document
from duckduckgo_search import DDGS

from src.document.news import get_news
from src.document.papers import read_all_pdf_content, read_first_page_of_pdf, read_papers
from src.run.utils import base_dir_for_run, load_nodes, save_nodes
from src.document.stories import get_stories


logger = logging.getLogger(__name__)


def resize_documents(documents: List[BaseNode], max_document_size: Optional[int]=None):
    for document in documents:
        if max_document_size is not None and len(document.text) > max_document_size:
            document.text = document.text[:max_document_size]


def load_samples_documents(run_id: str, base_dir: str, counts: str, shuffle: bool=True, max_document_size: Optional[int]=None):

    def parse_count(count_str):
        parts = count_str.split(':')
        if len(parts) != 2:
            raise ValueError(f"Invalid count format: {count_str}")
        return parts[0], int(parts[1])

    data_sources = {}
    for count in counts.split():
        source, size = parse_count(count)
        data_sources[source] = size

    documents = []
    for source, size in data_sources.items():
        if source == 'news':
            documents.extend(get_news(size=size))
        elif source == 'papers':
            documents.extend(read_papers(size=size))
        elif source == 'stories':
            documents.extend(get_stories(size=size))
        else:
            logger.error(f"Unknown data source: {source}")

    if shuffle:
        random.shuffle(documents)

    resize_documents(documents, max_document_size)
    
    nodes = documents
    save_nodes(nodes, os.path.join(base_dir_for_run(run_id, base_dir), "nodes_0_samples.json"))
    return "nodes_0_samples.json"


def load_urls(run_id: str, urls: List[str], base_dir: str, max_document_size: Optional[int]=None):
    documents = []
    documents = SimpleWebPageReader(html_to_text=True).load_data(
        urls
    )
    
    for document in documents:
        logger.info(f"Loaded document: {document.id_}")
        document.metadata["url"] = document.id_

    resize_documents(documents, max_document_size)

    save_nodes(documents, os.path.join(base_dir_for_run(run_id, base_dir), "nodes_0_urls.json"))
    return True


def load_uploaded_files(run_id: str, upload_dir: str, base_dir: str, max_document_size: Optional[int]=None):
    files = os.listdir(upload_dir)
    documents = []

    for file in files:
        logger.info(f"Loading {file}...")
        extension = file.split(".")[-1]
        if extension == "pdf":
            documents.append(read_all_pdf_content(os.path.join(upload_dir, file)))
        else:
            logger.error(f"can not handle uploaded file {file}: extension is not supported: {extension}")
        
    resize_documents(documents, max_document_size)
    nodes = documents
    save_nodes(nodes, os.path.join(base_dir_for_run(run_id, base_dir), "nodes_0_uploads.json"))

    return True

def remove_uploaded_file(run_id: str, file_name: str, base_dir: str, upload_dir: str):
    file_path = os.path.join(base_dir_for_run(run_id, base_dir), upload_dir, file_name)
    logger.info(f"Removing file {file_path}")
    if os.path.exists(file_path):
        os.remove(file_path)
        logger.info(f"Removed file {file_path}")
        upload_path = os.path.join(base_dir_for_run(run_id, base_dir), upload_dir)
        load_uploaded_files(run_id, upload_path, base_dir)
        return True
    return False


def join_document_nodes(run_id: str, base_dir: str):

    nodes = []
    node_files = [
        "nodes_0_samples.json", 
        "nodes_0_uploads.json", 
        "nodes_0_urls.json"
    ]
    for node_file in node_files:
        if os.path.exists(os.path.join(base_dir_for_run(run_id, base_dir), node_file)):
            nodes.extend(load_nodes(os.path.join(base_dir_for_run(run_id, base_dir), node_file)))

    save_nodes(nodes, os.path.join(base_dir_for_run(run_id, base_dir), "nodes_0.json"))


def get_source_nodes(run_id: str, base_dir: str):
    file_nodes = load_nodes(os.path.join(base_dir_for_run(run_id, base_dir), "nodes_0_uploads.json"))
    url_nodes = load_nodes(os.path.join(base_dir_for_run(run_id, base_dir), "nodes_0_urls.json"))
    samples_nodes = load_nodes(os.path.join(base_dir_for_run(run_id, base_dir), "nodes_0_samples.json"))
    all_nodes = file_nodes + url_nodes + samples_nodes
    return all_nodes


def get_source_node(run_id: str, node_id: str, base_dir: str):
    nodes = get_source_nodes(run_id, base_dir)
    node = next((node for node in nodes if node.id_ == node_id), None)
    return node


def load_web_pages(run_id: str, search_query: str, base_dir: str, max_web_pages: int, max_document_size: Optional[int]=None, web_body_only: bool=False):

    results = DDGS().text(search_query, max_results=max_web_pages)
    logger.info(f"duckduckgo search results: {len(results)=}")
    for result in results:
        logger.info(f"{result=}")
    hrefs = [
        result.get("href")
        for result in results
    ]

    print(f"web_body_only: {web_body_only}")
    if web_body_only:
        documents = [Document(
            id_=result.get("href"),
            text=f"Title: {result.get('title')}\n\n{result.get('body')}",
            metadata={
                "url": result.get("href")
            }
        ) for result in results]
        print(f"documents: {documents}")

        resize_documents(documents, max_document_size)
        save_nodes(documents, os.path.join(base_dir_for_run(run_id, base_dir), "nodes_0_urls.json"))
        return True

    return load_urls(run_id, hrefs, base_dir, max_document_size)
