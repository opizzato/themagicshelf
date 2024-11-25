import sys
from dotenv import load_dotenv
import logging
import argparse
import os
import shutil
import json
from typing import List
from llama_index.core.prompts.default_prompts import (
    DEFAULT_TREE_SUMMARIZE_PROMPT,
)
from llama_index.core.vector_stores.types import VectorStoreQuery
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import Settings
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core import get_response_synthesizer
from llama_index.core import DocumentSummaryIndex
from llama_index.core.storage.storage_context import StorageContext
from llama_index.core.prompts import PromptTemplate
from llama_index.core.utils import get_tqdm_iterable
from llama_index.core.storage.index_store.utils import (
    json_to_index_struct,
)
from llama_index.core.callbacks import (
    CallbackManager,
    LlamaDebugHandler,
)
from llama_index.core.schema import (
    MetadataMode,
)
from llama_index.core.schema import (
    Document,
    TextNode, 
    NodeRelationship,
    RelatedNodeInfo
)

from src.classification.cascade_summary_index import CascadeSummaryIndex
from src.classification.cascade_summarize import CascadeSummarize
from src.cache.wrapper import (
    LLMWrapper, 
    EmbeddingWrapper, 
    wrapper_stats_str
)
from src.classification.classification_questions_extractor import ClassificationQuestionsExtractor
from src.classification.classification_index import ClassificationIndex
from src.classification.classification_store import ClassificationIndexStore
from src.classification.classification_assignment_extractor import ClassificationAssignementExtractor
from src.classification.document_type_extractor import DocumentTypeExtractor
from src.document.document import join_document_nodes, load_samples_documents, load_uploaded_files, load_urls, load_web_pages
from src.run.utils import add_custom_metadata, base_dir_for_run, copy_metadata_from_node, create_folders_for_filepath, exclude_metadata_keys, load_nodes, save_nodes
from src.trace.trace import save_llama_debug
from src.vector.vector import embed_nodes, get_vector_index, get_vector_retriever
from src.compose.compose_retriever import ComposeRetriever

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)


# load_dotenv()
# NVIDIA_API_KEY = os.getenv('NVIDIA_API_KEY')


def set_api_key(api_key: str):
    os.environ["NVIDIA_API_KEY"] = api_key
    Settings.llm = LLMWrapper(
        # model="meta/llama-3.1-70b-instruct", 
        model="meta/llama3-70b-instruct", 
        # model="meta/llama-3.2-3b-instruct", # timeout
        # model="nvidia/llama-3.1-nemotron-70b-instruct", 
        # model="meta/llama-3.2-3b-instruct",
        max_nb_calls=800, 
        # max_nb_calls_cache_miss=0,
        kwargs={"temperature": 0}
    )
    Settings.embed_model = EmbeddingWrapper(
        model="NV-Embed-QA", 
        max_nb_calls=800,
        # max_nb_calls_cache_miss=0,
    )



def load_documents(run_id: str, base_dir: str, args=None):

    if args.samples is not None:
        load_samples_documents(run_id, base_dir, args.samples, args.shuffle, args.max_document_size)
    if args.urls is not None:
        load_urls(run_id, args.urls.split(","), base_dir, args.max_document_size)
    if args.pdfs_upload_dir is not None:
        load_uploaded_files(run_id, args.pdfs_upload_dir, base_dir, args.max_document_size)
    if args.web_search is not None:
        load_web_pages(run_id, args.web_search, base_dir, args.max_web_pages, args.max_document_size, args.web_body_only)


def compose_documents_clutter(run_id: str, base_dir: str, args=None):
    join_document_nodes(run_id, base_dir)


DOCUMENT_SUMMARY = (
    "Create a concise and comprehensive summary with a title, in strict CommonMark format. "
    "Rely strictly on the provided text, without including external information. "
    "Do not introduce the summary, just output the summary. "
    "Summary with title:"
)

SUB_CLASSIFICATION_SUMMARY = (
    "Create an introduction in strict CommonMark format for all the provided content."
    "Do not introduce this introduction, just output the text."
)

CLEAN_TYPES = """\
Here is a list of document types:

{types_str}

Clean this list of types from too much detailed types to have a list of distinct types.

For exemple if there is "scientific-astronomy-report" and "scientific-paper", merge them into "scientific-paper", "short-story" and "story" into "story", etc.

Return the cleaned types and mapping into JSON format.  
Do not add explanation or comments, only the JSON

Example of answer:
{{
    "cleaned_types": ["scientific-paper", "story"],
    "mapping": {{
        "scientific-paper": ["scientific-astronomy-report", "scientific-paper"],
        "story": ["short-story", "story"]
    }}
}}

Answer:
"""

GENERATE_SUMMARY_PROMPT_BY_TYPE = """
You are an expert in creating prompts for document summarization. 
Your task is to generate a prompt that will be used to summarize a document based on its type. 
The prompt you create should guide an AI to produce a concise, informative summary that captures the key points of the document while considering its specific type and characteristics.

Document Type: {document_type}

Please generate a prompt that addresses the following:

1. Specific aspects or sections to focus on for this document type
2. Key information that should be included in the summary
3. Appropriate length or format for the summary
4. Any special considerations or guidelines for summarizing this type of document

Your generated prompt should be clear, specific, and tailored to the given document type. Begin your response with "Summarize this type of {document_type} by:"
Do not add explanation or comments, only the prompt.

Generated Prompt:

"""

GENERATE_SUMMARY_PROMPT_BY_TYPE_2 = """

What is the best prompt for creating a summary of a {document_type} document in strict CommonMark format with all facts specific to this type?

The summary should be concise and comprehensive text in strict CommonMark markdown format, it should include a title and no introduction to the summary or explanation about the summary.

Do not introduce the prompt, just output the prompt.

Prompt:
"""


def create_chunks_and_summaries(run_id: str, base_dir: str, args=None):

    nodes = load_nodes(os.path.join(base_dir_for_run(run_id, base_dir), "nodes_0.json"))

    response_synthesizer = CascadeSummarize(
        llm=Settings.llm,
        callback_manager=CallbackManager([]),
        use_max_chunks=10,
    )
    index = CascadeSummaryIndex.from_documents(
        nodes,
        llm=Settings.llm,
        transformations=[
            SentenceSplitter( chunk_size=350, chunk_overlap=50),
        ],
        response_synthesizer=response_synthesizer,
        embed_model=Settings.embed_model,
        show_progress=True,
        summary_query=DOCUMENT_SUMMARY,
        embed_summaries=False,        
    )
    index.storage_context.persist(persist_dir=base_dir_for_run(run_id, base_dir) + "/summary_index")
    logger.info(f"created summary index, {len(index.index_struct.summary_id_to_node_ids)} summaries, {len(index.index_struct.node_id_to_summary_id)} chunks")


def get_summary_index(run_id: str=None, base_dir: str="output"):

    persist_file = os.path.join(base_dir_for_run(run_id, base_dir), "summary_index")
    logger.info(f"get summary index from {persist_file=}")
    storage_context = StorageContext.from_defaults(persist_dir=persist_file)
    stores_data = storage_context.index_store._kvstore._data["index_store/data"]
    store_data = stores_data[list(stores_data.keys())[0]]
    index_struct = json_to_index_struct(store_data)
    index = DocumentSummaryIndex(
        storage_context=storage_context, 
        llm=Settings.llm,
        embed_model=Settings.embed_model,
        index_struct=index_struct,
        embed_summaries=False,
    )
    logger.info(f"success getting summary index from {persist_file=}")
    return index


def embed_chunks(run_id: str, base_dir: str, args=None):

    # get the documents chunks from the summary index
    summary_index = get_summary_index(run_id, base_dir)
    index_struct = summary_index.index_struct
    chunk_ids = index_struct.node_id_to_summary_id.keys()
    chunks = summary_index.docstore.get_nodes(chunk_ids)

    embed_nodes(chunks, run_id, base_dir)


def generate_classification_information_from_summaries(run_id: str=None, base_dir: str="output", args=None):

    document_nodes = load_nodes(os.path.join(base_dir_for_run(run_id, base_dir), "nodes_0.json"))

    storage_context = StorageContext.from_defaults(persist_dir=base_dir_for_run(run_id, base_dir) + "/summary_index")
    stores_data = storage_context.index_store._kvstore._data["index_store/data"]
    store_data = stores_data[list(stores_data.keys())[0]]
    index_struct = json_to_index_struct(store_data)
    summary_ids = [index_struct.doc_id_to_summary_id[doc.id_] for doc in document_nodes]
    summary_nodes = storage_context.docstore.get_nodes(summary_ids)

    nodes = IngestionPipeline(transformations=[ClassificationQuestionsExtractor(llm=Settings.llm)]).run(documents=summary_nodes)

    # remove the new metadata "classification_information" from the node text used in embeddings and llm
    for node in nodes:
        node.excluded_embed_metadata_keys = node.excluded_embed_metadata_keys + ["classification_information"]
        node.excluded_llm_metadata_keys = node.excluded_llm_metadata_keys + ["classification_information"]

    save_nodes(nodes, os.path.join(base_dir_for_run(run_id), "nodes_1.json"))
    return "nodes_1.json"


def generate_classification_system(run_id: str=None, base_dir: str="output", args=None):

    nodes = load_nodes(os.path.join(base_dir_for_run(run_id), "nodes_1.json"))

    nodes = IngestionPipeline(transformations=[
        ClassificationAssignementExtractor(
            llm=Settings.llm, 
            use_fake_node_assignment=False,
            predefined_tree_and_tags="",
            log_dir=base_dir_for_run(run_id)
        ),
    ]).run(documents=nodes)

    # remove the new metadata "classification_location_and_tags" from the node text used in embeddings and llm
    for node in nodes:
        node.excluded_embed_metadata_keys = node.excluded_embed_metadata_keys + ["classification_location_and_tags"]
        node.excluded_llm_metadata_keys = node.excluded_llm_metadata_keys + ["classification_location_and_tags"]

    save_nodes(nodes, os.path.join(base_dir_for_run(run_id), "nodes_2.json"))

    store_path = os.path.join(base_dir_for_run(run_id), "store_0.json")
    index = ClassificationIndex(
        nodes=nodes,
        store=ClassificationIndexStore(persist_path=store_path),
        llm=Settings.llm,
    )
    index.persist()
    return "store_0.json"

def generate_document_types_information(run_id: str=None, base_dir: str="output", args=None):
    nodes = load_nodes(os.path.join(base_dir_for_run(run_id), "nodes_2.json"))
    nodes = IngestionPipeline(transformations=[
        DocumentTypeExtractor(
            llm=Settings.llm, 
            use_fake_node_assignment=False,
            log_dir=base_dir_for_run(run_id)
        ),
    ]).run(documents=nodes)

    # remove the new metadata "type" from the node text used in embeddings and llm
    for node in nodes:
        node.excluded_embed_metadata_keys = node.excluded_embed_metadata_keys + ["type"]
        node.excluded_llm_metadata_keys = node.excluded_llm_metadata_keys + ["type"]

    save_nodes(nodes, os.path.join(base_dir_for_run(run_id), "nodes_3.json"))
    

def _reassign_type(node, mapping):
    # Parcourir chaque clé/valeur dans le mapping
    for new_type, type_list in mapping.items():
        if node.metadata["type"] in type_list:
            # Si on trouve une correspondance, réassigner le type
            node.metadata["type"] = new_type
            break
    return node

def clean_and_regroup_document_types(run_id: str=None, base_dir: str="output", args=None):
    
    nodes = load_nodes(os.path.join(base_dir_for_run(run_id, base_dir), "nodes_3.json"))
    nodes_types = [node.metadata["type"] for node in nodes]
    nodes_types = list(sorted(set(nodes_types)))
    logger.info(f"raw nodes_types: {nodes_types}")

    response = Settings.llm.predict(
        PromptTemplate(template=CLEAN_TYPES),
        types_str=nodes_types,
        timeout=10,
    )

    response = json.loads(response)
    cleaned_types = response["cleaned_types"]
    mapping = response["mapping"]
    logger.info(f"cleaned types: {len(nodes_types)=} -> {len(cleaned_types)=}")
    logger.info(f"cleaned types: {cleaned_types=}")

    with open(os.path.join(base_dir_for_run(run_id, base_dir), "regrouped_document_types.json"), "w") as f:
        data = {
            'raw_types': nodes_types,
            'cleaned_types_response': response,
        }
        json.dump(data, f, indent=4)

    updated_nodes = [_reassign_type(node, mapping) for node in nodes]

    save_nodes(updated_nodes, os.path.join(base_dir_for_run(run_id), "nodes_4.json"))

    # create a store_1 that have type per nodes and all types information

    classification_index = get_classification_index(run_id, base_dir, persist_name="store_0.json")
    nodes_classification = classification_index._store._nodes

    for node_classification in nodes_classification:
        for node in updated_nodes:
            if node_classification.id_ == node.id_:
                node_classification.metadata["type"] = node.metadata["type"]
                node_classification.excluded_embed_metadata_keys = node.excluded_embed_metadata_keys
                node_classification.excluded_llm_metadata_keys = node.excluded_llm_metadata_keys
    
    classification_index._store._types = cleaned_types

    types_prompt = {}

    iterable_with_progress = get_tqdm_iterable(
        cleaned_types, show_progress=True, desc="Summary prompt for each type"
    )

    for cleaned_type in iterable_with_progress:
        prompt = Settings.llm.predict(
            PromptTemplate(template=GENERATE_SUMMARY_PROMPT_BY_TYPE_2),
            document_type=cleaned_type,
            timeout=10,
        )

        # append instruct to output the summary without introduction
        prompt = f"{prompt}\n\nOutput the summary without introduction, just the summary.\n\nSummary:\n"

        types_prompt[cleaned_type] = prompt
        logger.info(f"{cleaned_type=} - {prompt=}")

    classification_index._store._types_prompt = types_prompt

    classification_index._store._persist_path = os.path.join(base_dir_for_run(run_id), "store_1.json")
    classification_index.persist()

def generate_typed_summaries(run_id: str=None, base_dir: str="output", args=None):

    persist_file = os.path.join(base_dir_for_run(run_id, base_dir), "summary_index")
    storage_context = StorageContext.from_defaults(persist_dir=persist_file)
    stores_data = storage_context.index_store._kvstore._data["index_store/data"]
    store_data = stores_data[list(stores_data.keys())[0]]
    index_struct = json_to_index_struct(store_data)
    summary_index = DocumentSummaryIndex(
        storage_context=storage_context, 
        llm=Settings.llm,
        embed_model=Settings.embed_model,
        index_struct=index_struct,
        embed_summaries=False,
    )

    summaries_ids_chunks = summary_index.index_struct.summary_id_to_node_ids

    classification_index = get_classification_index(run_id, base_dir, persist_name="store_1.json")
    all_types = classification_index._store._types
    branch_nodes = classification_index._store._nodes

    iterable_with_progress = get_tqdm_iterable(
        all_types, show_progress=True, desc="Typed summaries for each type"
    )

    for doc_type in iterable_with_progress:
        prompt = classification_index._store._types_prompt[doc_type]
        
        for node in classification_index._store._nodes:
            if node.metadata["type"] == doc_type:

                response_synthesizer = CascadeSummarize(
                    llm=Settings.llm,
                    callback_manager=CallbackManager([]),
                )
                summary_index_typed = CascadeSummaryIndex(
                    storage_context.docstore.get_nodes(summaries_ids_chunks[node.id_]),
                    llm=Settings.llm,
                    response_synthesizer=response_synthesizer,
                    embed_model=Settings.embed_model,
                    show_progress=False,
                    summary_query=prompt,
                    embed_summaries=False,
                )

                summary_ids = summary_index_typed.index_struct.summary_id_to_node_ids.keys()

                summary_nodes = summary_index_typed.docstore.get_nodes(summary_ids)
                for summary_node in summary_nodes:
                    general_node = summary_node.relationships[NodeRelationship.SOURCE]

                    for branch_node in branch_nodes:
                        related = branch_node.relationships[NodeRelationship.SOURCE]
                        if related.node_id == general_node.node_id:

                            branch_node.text = summary_node.text
                            add_custom_metadata(branch_node, {'title': summary_node.metadata['title']})
                            
                            classification_index._store.update_text_node(branch_node)
    
    # add summaries to classification index
    #classification_index._store.update_text_nodes(branch_nodes)
    classification_index._store._persist_path = os.path.join(base_dir_for_run(run_id, base_dir), "store_2.json")
    classification_index.persist()


def get_classification_index(run_id: str=None, base_dir: str="output", persist_name: str="store.json"):
    persist_file = os.path.join(base_dir_for_run(run_id, base_dir), persist_name)   
    logger.info(f"get classification index from {persist_file=}")
    store = ClassificationIndexStore.from_store_path(persist_path=persist_file)
    index = ClassificationIndex.from_store(llm=Settings.llm, store=store, log_dir=base_dir_for_run(run_id))
    logger.info(f"success getting classification index from {persist_file=}")
    return index


def generate_classification_summaries(run_id: str=None, base_dir: str="output", args=None):
    classification_index = get_classification_index(run_id, base_dir, persist_name="store_2.json")

    # create nodes for each classification tree
    branch_nodes = []
    child_nodes = []
    for branch in classification_index._store._tree_schema:

        branch_node = Document(
            text="",
            metadata={
                "summary_for_tree_location": branch,
            }
        )
        branch_nodes.append(branch_node)

        nodes_ids = classification_index._store._tree[branch]
        nodes = [node for node in classification_index._store._nodes if node.id_ in nodes_ids]
        summary_child_nodes = [TextNode(**node.dict()) for node in nodes]
        logger.info(f"tree: {branch} - {len(summary_child_nodes)} nodes")

        # change parent relationship to assign the branch node as parent to all child nodes
        # this relation is used by DocumentSummaryIndex for summary
        for node in summary_child_nodes:
            related_node_info  = RelatedNodeInfo.from_dict({
                "node_id": branch_node.id_,
                "class_name": "RelatedNodeInfo",
            })

            node.relationships[NodeRelationship.SOURCE] = related_node_info
        
        child_nodes.extend(summary_child_nodes)

    # create summary for each branch node
    response_synthesizer = CascadeSummarize(
        llm=Settings.llm,
        callback_manager=CallbackManager([]),
    )
    summary_index = CascadeSummaryIndex(
        child_nodes,
        response_synthesizer=response_synthesizer,
        show_progress=True,
        summary_query=DOCUMENT_SUMMARY,
        embed_summaries=False,
    )

    # get summaries for all branches
    summary_ids = [summary_index.index_struct.doc_id_to_summary_id[doc.id_] for doc in branch_nodes]
    summary_nodes = summary_index.docstore.get_nodes(summary_ids)

    # for each summary retrieve the branch node and add the summary
    for summary_node in summary_nodes:
        branch_node_id = summary_node.relationships[NodeRelationship.SOURCE].node_id
        branch_node = [node for node in branch_nodes if node.id_ == branch_node_id][0]
        branch_node.text = summary_node.text

    # add summaries to classification index
    classification_index._store.update_summary_nodes(branch_nodes)
    classification_index._store._persist_path = os.path.join(base_dir_for_run(run_id, base_dir), "store_3.json")
    classification_index.persist()


def generate_sub_classification_summaries(run_id: str=None, base_dir: str="output", args=None):
    classification_index = get_classification_index(run_id, base_dir, persist_name="store_3.json")

    paths = classification_index._store.get_all_tree_paths(add_empty_root=True)

    paths_with_text_for_summary = classification_index._store._tree_summary
    paths_without_summary = [path for path in paths if path not in paths_with_text_for_summary.keys()]
    logger.info(f"paths without summary: {len(paths_without_summary)=}")

    new_path_summary_nodes = []

    # get the node from existing or new ones
    def get_node_for_node_id(node_id: str):
        if node_id in [n.id_ for n in new_path_summary_nodes]:
            return [n for n in new_path_summary_nodes if n.id_ == node_id][0]
        return classification_index._store.get_nodes([node_id])[0]

    while len(paths_without_summary) > 0:
        for path in paths_without_summary:

            children_with_text_for_summary = [
                child_path 
                for child_path in paths_with_text_for_summary.keys()
                if child_path.startswith(path)
            ]
            children_without_text = [
                child_path 
                for child_path in paths_without_summary
                if child_path.startswith(path) and child_path != path
            ]
            if len(children_without_text) > 0:
                logger.info(f"{path=} has children without summary, bypassed: {children_without_text=}")
                continue

            # get all text nodes for the path
            node_chunks = [
                get_node_for_node_id(paths_with_text_for_summary[child_path])
                for child_path in children_with_text_for_summary
            ]

            # join text_chunks text
            text_chunks=[
                n.get_content(metadata_mode=MetadataMode.LLM) for n in node_chunks
            ]
            context_str = "\n\n".join(text_chunks)

            # summarize the path
            response = Settings.llm.predict(
                DEFAULT_TREE_SUMMARIZE_PROMPT,
                context_str=context_str,
                query_str=SUB_CLASSIFICATION_SUMMARY,
            )

            # create the new node with the summary
            new_node = TextNode(
                text=response,
                metadata={"summary_for_tree_location": path},
            )
            new_path_summary_nodes.append(new_node)

            # remove children paths from paths_with_summary so that they are not processed again
            paths_with_text_for_summary = {
                p: paths_with_text_for_summary[p] 
                for p in paths_with_text_for_summary 
                if p not in children_with_text_for_summary
            }

            # add the new node to paths_with_text_for_summary
            paths_with_text_for_summary[path] = new_node.id_
            
            # remove the path from paths_without_summary
            paths_without_summary = [p for p in paths_without_summary if p != path]

            logger.info(f"added summary for {path=}: {response=}")


    # add summaries to classification index
    classification_index._store.update_path_summary_nodes(new_path_summary_nodes)
    classification_index._store._persist_path = os.path.join(base_dir_for_run(run_id, base_dir), "store_4.json")
    classification_index.persist()



def generate_links_between_documents(run_id: str=None, base_dir: str="output", args=None):

    vector_index = get_vector_index(run_id, base_dir)
    classification_index = get_classification_index(run_id, base_dir, persist_name="store_4.json")
    summary_index = get_summary_index(run_id, base_dir)

    similarity_top_k = 3
    for summary_id, node_ids in summary_index.index_struct.summary_id_to_node_ids.items():

        # for each chunk get the k similar other chunks
        # then get the summaries for the similar chunks
        similar_summary_ids = []
        for node_id in node_ids:

            # get the chunk embedding
            embeddings_collection = vector_index.vector_store._collection.get(node_id, include=["embeddings"])
            embedding = embeddings_collection["embeddings"][0]
            embedding = list(embedding)

            query = VectorStoreQuery(
                query_embedding=embedding,
                similarity_top_k=similarity_top_k,
            )
            query_result = vector_index._vector_store.query(query)

            top_k_ids: List[str]
            if query_result.ids is not None:
                top_k_ids = query_result.ids
            elif query_result.nodes is not None:
                top_k_ids = [n.node_id for n in query_result.nodes]
            else:
                raise ValueError(
                    "Vector store query result should return "
                    "at least one of nodes or ids."
                )
            
            # get the summaries for the top k similar chunks
            summary_ids = [summary_index.index_struct.node_id_to_summary_id.get(id) for id in top_k_ids]
            summary_ids = list(set([id for id in summary_ids if id is not None]))
 
            similar_summary_ids.extend(summary_ids)

        # get the summary node in the classification index
        summary_node = classification_index._store.get_nodes([summary_id])[0]
        
        # remove duplicates; several chunks of the same document may match
        similar_summary_ids = list(set(similar_summary_ids))

        # remove the summary id itself, its chunks may be similar to each other
        similar_summary_ids = [id for id in similar_summary_ids if id != summary_id]

        summary_node.metadata["similar_ids"] = similar_summary_ids

    classification_index._store._persist_path = os.path.join(base_dir_for_run(run_id, base_dir), "store_5.json")
    classification_index._store.persist()


def query_with_composed_retriever(run_id: str=None, base_dir: str="output", args=None):

    query_str = args.query
    if query_str is None:
        logger.error("no query")
        return

    store_path = os.path.join(base_dir_for_run(run_id), "store_5.json")
    store = ClassificationIndexStore.from_store_path(persist_path=store_path)
    index = ClassificationIndex.from_store(llm=Settings.llm, store=store, log_dir=base_dir_for_run(run_id))

    classification_retriever = index.as_retriever()

    embedding_retriever = get_vector_retriever(run_id, base_dir)

    compose_retriever = ComposeRetriever(
        embeddings_retriever=embedding_retriever,
        classification_retriever=classification_retriever,
        log_dir=base_dir_for_run(run_id)
    )

    query_engine = RetrieverQueryEngine(
        retriever=compose_retriever
    )

    response = query_engine.query(query_str)

    logger.info(f"response for run_id : {run_id} and query : {query_str} is : {response.response}")

    return response

def load_url_documents(run_id: str, base_dir: str, args=None):
    urls = args.urls.split(",")
    load_urls(run_id, urls, base_dir)


pipeline_steps = {
    # format: (function_name, description)
    "0": ("load_documents", "load documents"),
    "1": ("compose_documents_clutter", "compose documents clutter"),
    "2": ("create_chunks_and_summaries", "create chunks and summaries"),
    "3": ("embed_chunks", "embed chunks"),
    "4": ("generate_classification_information_from_summaries", "generate classification information from summaries"),
    "5": ("generate_classification_system", "generate classification system"),
    "6": ("generate_document_types_information", "generate document types information"),
    "7": ("clean_and_regroup_document_types", "clean and regroup document types"),
    "8": ("generate_typed_summaries", "generate typed summaries"),
    "9": ("generate_classification_summaries", "generate classification summaries"),
    "10": ("generate_sub_classification_summaries", "generate sub classification summaries"),
    "11": ("generate_links_between_documents", "generate links between documents"),
    "12": ("query_with_composed_retriever", "query with composed retriever"),
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run the pipeline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="\nSteps:\n" + "\n".join([f"{k}: {v[0]} {v[1]}" for k, v in pipeline_steps.items()])
    )
    parser.add_argument("-r", "--run_id", type=str, default=None)
    parser.add_argument("-b", "--base_dir", type=str, default="output")
    parser.add_argument("-s", "--steps", type=str, required=True, help="comma separated list of step ids, ex: 0,1,2,3,4,5")
    parser.add_argument("-q", "--query", type=str, default=None, help="query to search for; required for query steps")
    parser.add_argument("--samples", type=str, help="Numbers of sample documents to load, in the format: news:30 papers:10 stories:100")
    parser.add_argument("--urls", type=str, default=None, help="comma separated list of urls to load")
    parser.add_argument("--pdfs_upload_dir", type=str, default=None, help="directory containing the pdfs to load")
    parser.add_argument("--web_search", type=str, default=None, help="a web search string to load web pages")
    parser.add_argument("--web_body_only", action="store_true", help="only load the body of the web pages")
    parser.add_argument("--max_web_pages", type=int, default=5, help="max number of web pages to load")
    parser.add_argument("--max_document_size", type=int, help="optional max number of characters to load for a document")
    parser.add_argument("-n", "--noshuffle", action="store_false", dest="shuffle", help="do not shuffle the data")
    return parser.parse_args()


def explode_int_range_with_minus_char_and_join(range_str: str):
    if "-" not in range_str:
        return range_str
    range_parts = range_str.split("-")
    return ",".join([str(i) for i in list(range(int(range_parts[0]), int(range_parts[1]) + 1))])


def run_pipeline(run_id: str, base_dir: str, steps: str, args=None):
    args_steps = explode_int_range_with_minus_char_and_join(steps).split(",")
    for step_id in args_steps:
        pipeline_function, _ = pipeline_steps[step_id]
        logger.info(f"-------------------- {step_id=} - {pipeline_function=} --------------------")
        globals()[pipeline_function](run_id, base_dir, args)


if __name__ == "__main__":
    args = parse_args()
    logger.info(f"{args=}")

    llama_debug = LlamaDebugHandler(print_trace_on_end=True)
    callback_manager = CallbackManager([llama_debug])
    Settings.callback_manager = callback_manager

    run_pipeline(args.run_id, args.base_dir, args.steps, args=args)

    save_llama_debug(llama_debug, args.run_id, args.base_dir, args=args)

    logger.info(f"Wrapper stats: {wrapper_stats_str()}")
