# The Magic Shelf

The Magic Shelf is a summarization and classification system for humans and a Retrieval-Augmented Generation system for LLM.

Documents are prepared the same way for human browsing and for AI assistant retrieval.

* embeddings provides links between docs for human easy browsing
* summary nodes provide summary of documents for human easy understanding
* and a classification retrieval system allows to navigate through the documents hierarchy

This project was created for the [NVIDIA and LlamaIndex Developer Contest](https://developer.nvidia.com/llamaindex-developer-contest).


## Setup

### Backend

Create a virtual environment and install the dependencies:

```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file with the environment variables, see [.env_sample](.env_sample) file:

```bash
cp .env_sample .env
```

Then run the backend:

```bash
flask --app api.py run
```

Or use the CLI to run the pipeline:

```bash
python3.12 cli.py -r 1 -s 0,1,2,3,4,5,6,7,8,9,10
```

### Frontend

```bash
cd front2
cd themagicshelf
npm install --force
```

Then run the frontend:

```bash
npm run dev
```

## Files and directories

### Run data

Run data is organised in projects, each project is a `run_<name_of_the_project>` directory containing all the data and results of the project under the `output` directory.

```
output/run_1/
```

The frontend project is `run_0`, but you can create other projects using the CLI.

### File cache

A file cache records all LLM calls to avoid recomputing the same thing.

Cache for precomputed documents are in the directory:

```
file_cache/
```

# Technologies used

* [NVIDIA NIM](https://build.nvidia.com/explore/discover) serves the LLM models used by The Magic Shelf
  * LLM [llama3-70b-instruct](https://build.nvidia.com/meta/llama3-70b) for LLM calls
  * LLM [NV-Embed-QA](https://build.nvidia.com/nvidia/nv-embed-v1) for embeddings
* [llama-index](https://www.llamaindex.ai/) as retrieval augmented generation framework
* [Next.js](https://nextjs.org/) as user interface 


## Data augmentation workflow

See the [data augmentation workflow diagram](doc/workflow.png). Created with [Claude](https://claude.ai/) and [Edotor](https://edotor.net/).

### 0. Load documents
  * inputs
    * urls
    * pdfs
    * a selection of sample documents, from `tiny stories`, `scientific papers` and `news articles`
  * output
    * `nodes_0.json` file with the loaded documents as text nodes

### 1. Create chunks and summaries
  * input
    * `nodes_0.json` file with the loaded documents as text nodes
  * process
    * using `SentenceSplitter` to split the documents into chunks
    * and `DocumentSummaryIndex` to generate a summary node for each document recursively from its chunks
    * with `meta/llama3-70b-instruct` model via `NVIDIA NIM`
  * output
    * `summary_index` directory with the chunks and summaries

### 2. Embed chunks
  * input
    * `summary_index` directory
  * process
    * get all the chunks from `DocumentSummaryIndex`
    * embed them with `VectorStoreIndex` using `NV-Embed-QA` model via `NVIDIA NIM`
    * save the chunks embeddings in a `ChromaDB` database
  * output
    * `vector_index` directory with the `ChromaDB` database

### 3. Generate classification information from summaries
  * input
    * `summary_index` directory
    * `nodes_0.json` file with the loaded documents as text nodes
  * process
    * for all document summary node, create metadata `classification_information`:
        1. What is the main topic or subject of the document?
        2. What is the document's purpose (e.g., inform, persuade, entertain)?
        3. Who is the intended audience?
        4. ...
    * using `meta/llama3-70b-instruct` model via `NVIDIA NIM`
  * output
    * `nodes_1.json` file with `classification_information` metadata

### 4. Generate classification system
  * input
    * `nodes_1.json` file with `classification_information` metadata
  * process
    * Create the classification tree and tags system
      * Iterate on groups of documents, using `classification_information` metadata
      * create a classification tree and tags suitable for these documents
      * and not far from the previous iteration tree and tags
    * Apply the classification tree and tags system to the each document
      * for all document, on its summary node, create metadata `classification_location_and_tags`:
        * the classification location of the document
        * the tags of the document
    * using `meta/llama3-70b-instruct` model via `NVIDIA NIM`
  * output
    * `nodes_2.json` file with `classification_location_and_tags` metadata
    * `store_0.json` file with the classification tree and tags system and nodes with `classification_location_and_tags` metadata

### 5. Generate document types information
  * input
    * `nodes_2.json` file with `classification_location_and_tags` metadata
  * process
    * for each node ask LLM to assign a document type
    * using `meta/llama3-70b-instruct` model via `NVIDIA NIM`
    * from metadata `classification_information`
  * output
    * `nodes_3.json` file with `document_type` metadata

### 6. Clean and regroup document types
  * input
    * `nodes_3.json` file with `document_type` metadata
    * `store_0.json` file with the type tree and tags system
  * process
    * clean and regroup the document types
    * for each document type, generate a PROMPT to generate a summary of the document
    * using `meta/llama3-70b-instruct` model via `NVIDIA NIM`
  * output
    * `nodes_4.json` file with `document_type` metadata
    * `store_1.json` file with the document type prompts

### 7. Generate typed summaries
  * input
    * `summary_index` directory with the `DocumentSummaryIndex`
    * `store_1.json` file with the document type tree and tags system
  * process
    * Group documents by document type
    * For each document type:
      * generate a summary from its chunks 
      * using a `DocumentSummaryIndex` with the prompt of the document type
      * replace the document summary generated at step 1 by this new summary
    * using `meta/llama3-70b-instruct` model via `NVIDIA NIM`
  * output
    * `store_2.json` file with the typed summaries

### 8. Generate classification summaries
  * input
    * `store_2.json` file with the typed summaries
  * process
    * for all final branches of the classification tree
      * create a summary node of all documents of this branch
    * using `meta/llama3-70b-instruct` model via `NVIDIA NIM`
    * with `DocumentSummaryIndex` 
  * output
    * `store_3.json` file with the classification summaries

### 9. Generate sub classification summaries
  * input
    * `store_3.json` file with the classification summaries
  * process
    * for each sub branches of the classification tree
      * create a summary from all its children
      * using `meta/llama3-70b-instruct` model via `NVIDIA NIM`
      * with `DocumentSummaryIndex`
  * output
    * `store_4.json` file with the sub classification summaries

### 10. Generate links between documents
  * input
    * `summary_index` directory with the `DocumentSummaryIndex`
    * `vector_index` directory with the `VectorStoreIndex`
    * `store_4.json` file with the sub classification summaries
  * process
    * for all document, on its summary node, create metadata `similar_ids`:
      * get all its chunks from `DocumentSummaryIndex`
      * get the chunk embeddings from `VectorStoreIndex`
      * retrieve similar chunks using a `VectorStoreQuery`
      * get the documents of the similar chunks using `DocumentSummaryIndex`
  * output
    * `store_5.json` file with `similar_ids` metadata

### 11. Query the composed retrievers
  * input
    * `store_5.json` file with the classification store
    * `vector_index` directory with the `ChromaDB` database of chunks embeddings
  * process
    * from a query:
      * find the chunks similar to the query using `VectorStoreIndex`
      * ask LLM `meta/llama3-70b-instruct` which branches of the classification tree and which tags may have candidate documents to answer the query
      * retrieve the candidate documents summary of the branches having at least one of the candidate tags
  * output
    * the final retreival context: `the similar chunks` and `the candidate documents summary`


## CLI

```bash
python3.12 cli.py -r 1 -s 0,1,2,3,4,5,6,7,8,9,10
```

Creates a project directory `output/run_1` and run the pipeline with the following steps:
* `0,1,2,3,4,5,6,7,8,9,10`


```bash
usage: cli.py [-h] [-r RUN_ID] [-b BASE_DIR] -s STEPS [-q QUERY] [-k TOP_K] [--counts COUNTS] [-n]

Run the pipeline.

options:
  -h, --help            show this help message and exit
  -r RUN_ID, --run_id RUN_ID
  -b BASE_DIR, --base_dir BASE_DIR
  -s STEPS, --steps STEPS
                        comma separated list of step ids, ex: 0,1,2,3,4,5
  -q QUERY, --query QUERY
                        query to search for; required for query steps
  --samples SAMPLES     Numbers of sample documents to load, in the format: news:30 papers:10 stories:100
  --urls URLS           comma separated list of urls to load
  --pdfs_upload_dir PDFS_UPLOAD_DIR
                        directory containing the pdfs to load
  --web_search WEB_SEARCH
                        a web search string to load web pages
  --max_web_pages MAX_WEB_PAGES
                        max number of web pages to load
  -n, --noshuffle       do not shuffle the data

Steps:
0: load_documents 
1: create_chunks_and_summaries 
2: embed_chunks 
3: generate_classification_information_from_summaries 
4: generate_classification_system 
5: generate_document_types_information 
6: clean_and_regroup_document_types 
7: generate_typed_summaries 
8: generate_classification_summaries 
9: generate_sub_classification_summaries 
10: generate_links_between_documents 
11: query_with_composed_retriever 
```


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
