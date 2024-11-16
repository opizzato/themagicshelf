import logging
from typing import Any, Dict
import flask
import os
import threading
import datetime
from flask_cors import CORS
import json
from werkzeug.utils import secure_filename

from src.run.utils import base_dir_for_run
from src.classification.classification_store import ClassificationIndexStore

from cli import (
    pipeline_steps,
    compose_documents_clutter,
    embed_chunks, 
    generate_classification_information_from_summaries, 
    generate_classification_system, 
    join_document_nodes, 
    create_chunks_and_summaries, 
    clean_and_regroup_document_types,
    generate_sub_classification_summaries, 
    generate_typed_summaries, 
    generate_document_types_information, 
    generate_classification_summaries, 
    generate_links_between_documents,
    query_with_composed_retriever
)

from src.document.document import (
    get_source_node,
    get_source_nodes,
    join_document_nodes, 
    load_urls, 
    load_uploaded_files,
    load_samples_documents,
    load_web_pages,
    remove_uploaded_file
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

results = {
    "status": "Not started",
    "step": "",
    "step_index": 0,
    "logs": []
}

app = flask.Flask(__name__)
CORS(app)

def add_log(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    results["logs"].append(f"[{timestamp}] {message}")

class Args:
    def __init__(self, run_id, query=None):
        self.run_id = run_id
        self.query = query

def run_pipeline(run_id):
    try:
        args = Args(run_id)

        results["status"] = "running"
        results["logs"] = []

        for step_id in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]:
            step_id = str(step_id)
            pipeline_function, description = pipeline_steps[step_id]
            step = f"{step_id} - {description}"
            results["step"] = step
            results["step_index"] = step_id
            logger.info(step)
            add_log(f"{step}")
            globals()[pipeline_function](run_id, 'output', args)

        results["status"] = "completed"
        add_log("Pipeline completed")

    except Exception as e:
        results["status"] = "error"
        logger.error(f"Pipeline error: {e}")
        add_log(f"Pipeline error: {e}")

def get_run_number(run):
    return int(run.split('_')[1])

def get_store(run_id) -> ClassificationIndexStore:
    return ClassificationIndexStore.from_store_path(persist_path=f"output/run_{run_id}/store_5.json")

def get_run_folders():
    run_folders = [folder for folder in os.listdir("./output") if folder.startswith("run_")]
    run_folders = sorted(run_folders, key=get_run_number)
    return run_folders

def get_tree_nodes_and_edges(run_id):
    store = get_store(run_id)
    return store.get_tree_digraph_nodes_and_edges()

def get_node_summary(run_id, node_id):
    store = get_store(run_id)
    node_id_summary = store.get_node_id_summary(node_id)
    text_summary = store.get_node_text(node_id_summary)
    return text_summary

def get_similar_nodes_id(run_id, node_id):
    store = get_store(run_id)
    return store.get_similar_nodes_id(node_id)

def load_store(run_id):
    with open(f"./output/run_{run_id}/store_5.json", "r") as f:
        return json.load(f)

def ensure_upload_folder(run_id):
    folder = os.path.join(base_dir_for_run(run_id, "output"), "files")
    os.makedirs(folder, exist_ok=True)
    return folder

@app.route("/")
def index():
    return "Hello, World!"

@app.route("/processing_logs")
def get_processing_logs():
    return flask.jsonify(results)

@app.route("/runs")
def get_runs():
    return flask.jsonify({
        "run_folders": get_run_folders()
    })

@app.route("/store")
def get_final_store():
    run_id = flask.request.args.get("run_id")
    return flask.jsonify({
        "store": load_store(run_id)
    })

@app.route("/tree")
def get_tree():
    run_id = flask.request.args.get("run_id")
    nodes, edges = get_tree_nodes_and_edges(run_id)
    return flask.jsonify({
        "nodes": nodes,
        "edges": edges
    })

def document_source_info(node):
    type = "pdf" if node.metadata.get("file_name") else "url" if node.metadata.get("url") else "preprocessed"
    title = node.metadata.get("file_name", node.metadata.get("url", "unknown"))
    return {
        "type": type,
        "title": title,
        "file": None,
        "url": node.metadata.get("url", None),
        "preprocessedType": "unknown",
    }

@app.route("/document_sources")
def document_sources():
    run_id = flask.request.args.get("run_id")
    source_nodes = get_source_nodes(run_id, 'output')

    processed = os.path.exists(os.path.join(base_dir_for_run(run_id, 'output'), "store_5.json"))

    sources = [
        {
            "id": node.id_,
            **document_source_info(node),
            "processed": processed,
        }
        for node in source_nodes
    ]
    return flask.jsonify({
        "document_sources": sources
    })

@app.route("/source_node_info")
def source_node_info():
    run_id = flask.request.args.get("run_id")
    node_id = flask.request.args.get("node_id")
    node = get_source_node(run_id, node_id, 'output')
    MAX_TEXT_LENGTH = 2000
    return flask.jsonify({
        "source_node_info": {
            "url": node.metadata.get("url", None),
            "file_name": node.metadata.get("file_name", None),
            "text": node.text[:MAX_TEXT_LENGTH],
            "text_is_truncated": len(node.text) > MAX_TEXT_LENGTH
        }
    })

def get_node_text(run_id, node_id):
    store = get_store(run_id)
    return store.get_node_text(node_id)

@app.route("/node_text")
def node_text():
    run_id = flask.request.args.get("run_id")
    node_id = flask.request.args.get("node_id")
    return flask.jsonify({
        "text": get_node_text(run_id, node_id)
    })

@app.route("/node_summary")
def node_summary():
    run_id = flask.request.args.get("run_id")
    node_id = flask.request.args.get("node_id")
    print("node_id :", node_id)
    return flask.jsonify({
        "summary": get_node_summary(run_id, node_id)
    })

@app.route("/similar_nodes")
def similar_nodes():
    run_id = flask.request.args.get("run_id")
    node_id = flask.request.args.get("node_id")
    return flask.jsonify({
        "similar_nodes": get_similar_nodes_id(run_id, node_id)
    })

@app.route("/category_tree")
def category_tree():
    run_id = flask.request.args.get("run_id")
    store = get_store(run_id)
    return flask.jsonify({
        "category_tree": store.get_category_tree()
    })

@app.route("/ask_query")
def ask_query():
    print("ask query")
    run_id = flask.request.args.get("run_id")
    query = flask.request.args.get("query")
    args = Args(run_id, query)
    print("query :", query) 
    response = query_with_composed_retriever(run_id, 'output', args)
    print("response for run_id :", run_id, "and query :", query, " with args :", args, " is :", response)
    return flask.jsonify({
        "answer": response.response
    })

@app.route("/launch_run")
def launch_run():
    run_id = flask.request.args.get("run_id")
    start = threading.Thread(target=run_pipeline, args=(run_id))
    start.start()
    return flask.jsonify({
        "status": "ok"
    })

@app.route("/remove_uploaded_file", methods=['POST'])
def remove_upload():
    run_id = flask.request.args.get("run_id")
    file_name = flask.request.args.get("file_name")
    logger.info(f"Removing file {file_name} from run_id {run_id}")
    remove_uploaded_file(run_id, file_name, 'output', "files")
    return flask.jsonify({
        "status": "ok"
    })

@app.route('/upload-files', methods=['POST'])
def upload_files():
    logger.info("/upload-files")
    run_id = flask.request.args.get("run_id")

    upload_folder = ensure_upload_folder(run_id)

    files = flask.request.files.getlist("files")    
    for file in files:
        file_path = os.path.join(upload_folder, file.filename)
        print("saving file_path:", file_path)
        file.save(file_path)

    load_uploaded_files(run_id, upload_folder, 'output')

    return flask.jsonify({
        "message": f"{len(files)} files uploaded successfully"
    }), 200

@app.route('/add-samples', methods=['POST'])
def add_samples():
    logger.info("/add-samples")
    run_id = flask.request.args.get("run_id")
    samples = flask.request.args.get("samples")
    shuffle = flask.request.args.get("shuffle") == "true"
    max_document_size = flask.request.args.get("max_document_size")
    max_document_size = int(max_document_size)

    samples = samples.replace("tiny_stories", "stories").replace("scientific_papers", "papers")

    load_samples_documents(run_id, "output", samples, shuffle, max_document_size)
    logger.info(f"Samples {samples} added successfully")
    
    return flask.jsonify({
        "message": f"{samples=} added successfully"
    }), 200

@app.route("/add-urls", methods=['POST'])
def add_urls():
    logger.info("/add-urls")
    run_id = flask.request.args.get("run_id")
    urls = [url for url in flask.request.form.get("urls").split(",") if url != '']
    max_document_size = flask.request.form.get("max_document_size")
    max_document_size = int(max_document_size)
    logger.info(f"Adding {len(urls)} urls to run_id {run_id} with max_document_size {max_document_size}")
    load_urls(run_id, urls, 'output', max_document_size)
    return flask.jsonify({
        "message": f"{len(urls)} urls added successfully"
    }), 200

@app.route("/add-search-results", methods=['POST'])
def add_search_results():
    logger.info("/add-search-results")
    run_id = flask.request.args.get("run_id")
    query = flask.request.form.get("query")
    nb_pages = flask.request.form.get("nb_pages")
    nb_pages = int(nb_pages)
    max_document_size = flask.request.form.get("max_document_size")
    max_document_size = int(max_document_size)
    load_web_pages(run_id, query, 'output', nb_pages, max_document_size)
    return flask.jsonify({
        "message": "Search results added successfully"
    }), 200

@app.route("/login", methods=['POST'])
def login():
    return flask.jsonify({
        "data": {
            "user": {
                "id": 1,
                "name": "John Doe"
            },
            "token": "1234567890"
        }
    }), 200

@app.route("/logout", methods=['POST'])
def logout():
    return flask.jsonify({
        "status": "ok"
    }), 200
