import os
from llama_index.core import Document, VectorStoreIndex, Settings
from llama_index.llms.openai import OpenAI


def load_text_files(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.readlines()


def load_tiny_stories():
    return load_text_files("data/tiny_stories/TinyStoriesV2-GPT4-valid.txt")


def group_lines_by_separator(lines, separator):
    groups = []
    current_group = []
    for line in lines:
        if line.strip() == separator:
            groups.append(current_group)
            current_group = []
        else:
            current_group.append(line.strip())
    return groups


def join_story_lines(lines):
    return "\n".join(lines)


def story_to_document(story):
    return Document(text=join_story_lines(story))

def stories_to_documents(stories):
    return [story_to_document(story) for story in stories]


def get_stories(size=100):
    stories = group_lines_by_separator(load_tiny_stories(), "<|endoftext|>")[0:size]
    documents = stories_to_documents(stories)
    return documents
