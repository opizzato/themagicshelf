import logging
import pandas as pd
from llama_index.core import Document

logger = logging.getLogger(__name__)


def read_news(size=100):
    news = pd.read_csv("data/news_articles/news_articles.csv")
    logger.info(f"Read {len(news)} news articles")
    return news[:size]

def news_to_documents(news):
    return [Document(text=f"{row['title']}: {row['text']}") for i, row in news.iterrows()]

def get_news(size=100):
    news = read_news(size)
    documents = news_to_documents(news)
    return documents
