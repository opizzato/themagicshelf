import logging
import os
import requests

from llama_index.core import SimpleDirectoryReader
from llama_index.readers.file import PDFReader

logger = logging.getLogger(__name__)


urls = [
    "https://openreview.net/pdf?id=VtmBAGCN7o",
    "https://openreview.net/pdf?id=6PmJoRfdaK",
    "https://openreview.net/pdf?id=LzPWWPAdY4",
    "https://openreview.net/pdf?id=VTF8yNQM66",
    "https://openreview.net/pdf?id=hSyW5go0v8",
    "https://openreview.net/pdf?id=9WD9KwssyT",
    "https://openreview.net/pdf?id=yV6fD7LYkF",
    "https://openreview.net/pdf?id=hnrB5YHoYu",
    "https://openreview.net/pdf?id=WbWtOYIzIK",
    "https://openreview.net/pdf?id=c5pwL0Soay",
    "https://openreview.net/pdf?id=TpD2aG1h0D",
]

papers = [
    "metagpt.pdf",
    "longlora.pdf",
    "loftq.pdf",
    "swebench.pdf",
    "selfrag.pdf",
    "zipformer.pdf",
    "values.pdf",
    "finetune_fair_diffusion.pdf",
    "knowledge_card.pdf",
    "metra.pdf",
    "vr_mcl.pdf",
]

def download_file(url, file_path, base_dir=""):
    """Downloads a file from a given URL and saves it to the specified file path.

    Args:
        url: The URL of the file to download.
        file_path: The path to save the downloaded file.
        base_dir: The base directory to save the file in. Defaults to current directory.
    """

    full_path = os.path.join(base_dir, file_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    response = requests.get(url, stream=True)
    response.raise_for_status()  # Raise an exception for non-200 status codes

    with open(full_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:  # Filter out keep-alive new chunks
                f.write(chunk)

    logger.info(f"Downloaded file from {url} to {full_path}")


def download_papers():
    for url, paper in zip(urls, papers):
        download_file(url, paper, base_dir="data/papers")

def list_files_in_dir(dir_path):
    return os.listdir(dir_path)

def read_first_page_of_pdf(file_path):
    reader = PDFReader(return_full_document=False)
    documents = reader.load_data(file_path)
    return documents[0]


def read_all_pdf_content(file_path):
    reader = PDFReader(return_full_document=True)
    documents = reader.load_data(file_path)
    return documents[0]


def read_first_page_of_pdfs_in_dir(dir_path, size=100):
    files = list_files_in_dir(dir_path)
    res = []
    for file in files:
        if file.endswith(".pdf"):
            logger.info(f"reading first page of {file=}")
            res.append(read_first_page_of_pdf(os.path.join(dir_path, file)))
            if len(res) >= size:
                break
    return res


def read_papers(size=100):
    # reader = SimpleDirectoryReader(input_files=["data/papers/metagpt.pdf"], file_extractor={"pdf": PDFReader(return_full_document=True)})
    # documents = reader.load_data()
    documents = read_first_page_of_pdfs_in_dir("data/papers", size)
    logger.info(f"Read {len(documents)} papers")

    return documents[0:size]


if __name__ == "__main__":
    download_papers()