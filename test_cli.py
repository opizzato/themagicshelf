import logging
import argparse

from llama_index.core.schema import (
    TextNode, 
)
from llama_index.core.prompts import PromptTemplate
from llama_index.core.prompts.default_prompts import (
    DEFAULT_TREE_SUMMARIZE_PROMPT,
)
from llama_index.readers.web import SimpleWebPageReader
from llama_index.core.schema import (
    Document,
)
from llama_index.core.node_parser import SentenceSplitter

from src.classification.classification_assignment_extractor import DEFAULT_TYPE_ASSIGN_PROMPT, CLASSIFICATION_SYSTEM_EXTRACTION_PROMPT, CLASSIFICATION_SYSTEM_EXTRACTION_PROMPT_WITH_PREVIOUS_TYPE
from src.classification.classification_questions_extractor import DEFAULT_CLASSIFICATION_GEN_TMPL
from src.classification.cascade_summarize import CascadeSummarize
from src.classification.cascade_summary_index import CascadeSummaryIndex
from src.cache.wrapper import EmbeddingWrapper, LLMWrapper, wrapper_stats_str
from cli import CLEAN_TYPES, DOCUMENT_SUMMARY, GENERATE_SUMMARY_PROMPT_BY_TYPE_2, SUB_CLASSIFICATION_SUMMARY
from src.document.stories import get_stories

logger = logging.getLogger(__name__)

prompt_ids = {
    '1': 'document_summary',
    '2': 'document_summary_with_cascade',
    '3': 'sub_classification_summary',
    '4': 'clean_types',
    '5': 'generate_summary_prompt_by_type',
    '6': 'classification_information',
    '7': 'classification_tree_and_tags_extraction',
    '8': 'classification_tree_and_tags_extraction_with_previous_type',
    '9': 'classification_assign',
}

def parse_args():
    parser = argparse.ArgumentParser(
        description="This CLI provides a tool for manual testing of all the RAG prompts. ",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="\nPrompts:\n" + "\n".join([f"{k}: {v}" for k, v in prompt_ids.items()])
    )
    parser.add_argument('-p', '--prompt_test_id', type=str, help='id of the prompt test to run', required=True)
    return parser.parse_args()


def test_classification_assign():

    category_tree_str = """
hierarchical_classification:
- Literature
  - Children's Literature
    - Fables
- Education
  - Children's Education
    - Moral Lessons

tags:
- Storytelling
- Moral Values
- Youth Audience
- Unknown Author
- Conflict Resolution
"""
    classification_information = """
1. The main topic is a king's bath time experience.
2. The purpose is to entertain.
3. The intended audience is likely children.
4. The document's format is a short story or fairy tale.
5. The document's creation or publication date is unknown.
6. The author or source is unknown.
7. The key themes are relaxation, responsibility, and self-care.
8. The document relates to literature or children's fiction.
"""
    llm = LLMWrapper(
        model="meta/llama3-70b-instruct", 
    )
    type_str = llm.predict(
        PromptTemplate(template=DEFAULT_TYPE_ASSIGN_PROMPT),
        context_str=classification_information,
        category_tree_str=category_tree_str,
        timeout=10,
    )
    print(f"\ntype_str:\n{type_str}\n")


def test_classification_tree_and_tags_extraction_with_previous_type():

    previous_type = """
hierarchical_classification:
- Literature (2)
  - Children's Literature (2)
    - Fables (2)
- Education (2)
  - Children's Education (2)
    - Moral Lessons (2)

tags:
- Storytelling (2)
- Moral Values (2)
- Youth Audience (2)
- Unknown Author (2)
- Conflict Resolution (2)
"""

    llm = LLMWrapper(
        model="meta/llama3-70b-instruct", 
    )

    classification_information = [
        """
1. The main topic is a story about a little girl named Lucy.
2. The document's purpose is to entertain and teach a moral lesson.
3. The intended audience is likely children or parents reading to children.
4. The document's format is a short story or fable.
5. The document's creation or publication date is unknown.
6. The author or source is unknown.
7. The key themes are kindness, understanding, and conflict resolution.
8. The document relates to literature or children's education.
""",
        """,
1. The main topic is a king's bath time experience.
2. The purpose is to entertain.
3. The intended audience is likely children.
4. The document's format is a short story or fairy tale.
5. The document's creation or publication date is unknown.
6. The author or source is unknown.
7. The key themes are relaxation, responsibility, and self-care.
8. The document relates to literature or children's fiction.
"""
    ]
    classification_information = "\n\n".join(classification_information)
    prompt_params = {'context_str': classification_information, 'previous_type_str': previous_type}

    prompt = PromptTemplate(template=CLASSIFICATION_SYSTEM_EXTRACTION_PROMPT_WITH_PREVIOUS_TYPE)

    category_tree_str = llm.predict(
        prompt,
        **prompt_params,
        timeout=10,
    )
    print(f"\ncategory_tree_str:\n{category_tree_str}\n")
    



def test_classification_tree_and_tags_extraction():

    llm = LLMWrapper(
        model="meta/llama3-70b-instruct", 
    )

    classification_information = [
        """
1. The main topic is a story about a little girl named Lucy.
2. The document's purpose is to entertain and teach a moral lesson.
3. The intended audience is likely children or parents reading to children.
4. The document's format is a short story or fable.
5. The document's creation or publication date is unknown.
6. The author or source is unknown.
7. The key themes are kindness, understanding, and conflict resolution.
8. The document relates to literature or children's education.
""",
        """
1. The main topic is a king's bath time experience.
2. The purpose is to entertain.
3. The intended audience is likely children.
4. The document's format is a short story or fairy tale.
5. The document's creation or publication date is unknown.
6. The author or source is unknown.
7. The key themes are relaxation, responsibility, and self-care.
8. The document relates to literature or children's fiction.
"""
    ]
    classification_information = "\n\n".join(classification_information)
    prompt_params = {'context_str': classification_information}

    prompt = PromptTemplate(template=CLASSIFICATION_SYSTEM_EXTRACTION_PROMPT)

    category_tree_str = llm.predict(
        prompt,
        **prompt_params,
        timeout=10,
    )
    print(f"\ncategory_tree_str:\n{category_tree_str}\n")
    
    

def test_classification_information():

    llm = LLMWrapper(
        model="meta/llama3-70b-instruct", 
    )
    context_str = '''
Once upon a time there was a little girl named Lucy. She loved to go to the store to buy sweets with her mom and dad. On this special day, Lucy entered the store with her mom and dad, feeling so excited.
As they were looking around, Lucy noticed a little girl playing with a toy in the corner of the store. She gasped in excitement and ran towards her. Lucy asked if she could play too but the little girl said no. She was rather grumpy and was not in the mood to play.
Lucy's mom saw what was going on and told Lucy, "Let's try to be peaceful and kind to her. Have patience and understanding. Together, you can both be happy!"
So, Lucy smiled at the girl and said, "Can we play together?" The little girl softened and smiled back. She agreed to share the toy and even let Lucy have a turn first.
Lucy and the little girl played together happily. In the end, they both learnt an important lesson: be peaceful, kind, and understanding when faced with a conflict. And that is why Lucy and the little girl became great friends.
'''

    context_str = '''
Once upon a time, there was a king. He was a big and strong king who ruled over his kingdom. One day, he wanted to take a nice and long bath, so he filled up his big bathtub with warm water. He wanted to feel relaxed and so he soaked in the tub for a really long time.
When he had finished soaking and stepped out of the bathtub, the king noticed that the water had spilled out of the tub and all over the floor. He felt guilty that he had made such a mess, so he quickly grabbed a cloth and began to clean it up.
The king got so hot from cleaning up the mess that he decided to take another soak in the bathtub. He put a lot of bubbles in the water to make it nice and bubbly. He relaxed again and felt all the worries wash away.
The king was so happy that he had been able to clean up the mess he had made and enjoy a nice soak. He dried off and wrapped himself up in a big towel. Then, the king went back to ruling his kingdom and enjoying his lovely baths.
'''
    prompt = PromptTemplate(template=DEFAULT_CLASSIFICATION_GEN_TMPL)
    response = llm.predict(
        prompt, context_str=context_str
    )
    print(f"\response:\n{response}\n")


def test_generate_summary_prompt_by_type_for_type_on_url(type: str, url: str):

    llm = LLMWrapper(
        model="meta/llama3-70b-instruct", 
    )
    cleaned_type = type
    prompt = llm.predict(
        PromptTemplate(template=GENERATE_SUMMARY_PROMPT_BY_TYPE_2),
        document_type=cleaned_type,
        timeout=10,
    )
    print(f"type: {cleaned_type}\n")
    print(f"\nprompt:\n{prompt}\n")

    nodes = SimpleWebPageReader(html_to_text=True).load_data([url])
    
    response_synthesizer = CascadeSummarize(
        llm=llm,
        use_max_chunks=10,
    )
    embed_model = EmbeddingWrapper(
        model="NV-Embed-QA", 
        max_nb_calls=800,
        # max_nb_calls_cache_miss=0,
    )
    index = CascadeSummaryIndex.from_documents(
        nodes,
        llm=llm,
        transformations=[
            SentenceSplitter( chunk_size=350, chunk_overlap=50),
        ],
        response_synthesizer=response_synthesizer,
        embed_model=embed_model,
        show_progress=True,
        summary_query=prompt,
        embed_summaries=False,        
    )
    summary_id = index.index_struct.doc_id_to_summary_id[nodes[0].id_]
    nodes = index.storage_context.docstore.get_nodes([summary_id])
    summary_node = nodes[0]
    print(f"biography web page: {url}\n")
    print(f"\nsummary:\n{summary_node.text}\n")


def test_generate_summary_prompt_by_type():

    test_generate_summary_prompt_by_type_for_type_on_url("biography", "https://fr.wikipedia.org/wiki/Isaac_Asimov")
    test_generate_summary_prompt_by_type_for_type_on_url("definition", "https://en.wikipedia.org/wiki/Three_Laws_of_Robotics")


def test_clean_types():

    llm = LLMWrapper(
        model="meta/llama3-70b-instruct", 
    )
    nodes_types = [
        "anecdotal-short-story",
        "biographical-sketch",
        "childrens-fable",
        "childrens-picture-book",
        "childrens-short-story",
        "childrens-story",
        "fable",
        "folk-tale",
        "humorous-anecdote",
        "scientific-paper"
    ]
    response = llm.predict(
        PromptTemplate(template=CLEAN_TYPES),
        types_str=nodes_types,
        timeout=10,
    )
    print("types:")
    for type in nodes_types:
        print(f"{type}")
    print(f"\nresponse:\n{response}\n")

    expected_response = '''
{
    "cleaned_types": ["biographical-sketch", "fable", "paper", "story"],
    "mapping": {
        "biographical-sketch": ["biographical-sketch"],
        "fable": ["childrens-fable", "fable", "folk-tale"],
        "paper": ["scientific-paper"],
        "story": ["anecdotal-short-story", "childrens-picture-book", "childrens-short-story", "childrens-story", "humorous-anecdote", "short-story"]
    }
}
'''
    print("expected response:")
    print(expected_response)


def test_sub_classification_summary():

    llm = LLMWrapper(
        model="meta/llama3-70b-instruct", 
        # model="nvidia/llama-3.1-nemotron-70b-instruct", 
        # model="meta/llama-3.2-3b-instruct",
    )

    text_chunks = [node.text for node in get_stories(size=3)]
    context_str = "\n\n".join(text_chunks)

    # summarize the path
    response = llm.predict(
        DEFAULT_TREE_SUMMARIZE_PROMPT,
        context_str=context_str,
        query_str=SUB_CLASSIFICATION_SUMMARY,
    )

    print("texts:\n")
    for text in text_chunks:
        print(f"\n{text}\n")
    print(f"\nresponse:\n{response}\n")



def test_document_summary_with_cascade():

    llm = LLMWrapper(
        model="meta/llama3-70b-instruct", 
        # model="nvidia/llama-3.1-nemotron-70b-instruct", 
        # model="meta/llama-3.2-3b-instruct",
    )
    embed_model = EmbeddingWrapper(
        model="NV-Embed-QA", 
        max_nb_calls=800,
        # max_nb_calls_cache_miss=0,
    )

    urls = ["https://www.gutenberg.org/cache/epub/31516/pg31516.txt"]
    nodes = SimpleWebPageReader(html_to_text=True).load_data(urls)

    response_synthesizer = CascadeSummarize(
        llm=llm,
        use_max_chunks=10,
    )
    index = CascadeSummaryIndex.from_documents(
        nodes,
        llm=llm,
        transformations=[
            SentenceSplitter( chunk_size=350, chunk_overlap=50),
        ],
        response_synthesizer=response_synthesizer,
        embed_model=embed_model,
        show_progress=True,
        summary_query=DOCUMENT_SUMMARY,
        embed_summaries=False,        
    )
    summary_id = index.index_struct.doc_id_to_summary_id[nodes[0].id_]
    nodes = index.storage_context.docstore.get_nodes([summary_id])
    summary_node = nodes[0]
    children_ids = summary_node.metadata["summary_children"]
    children = index.storage_context.docstore.get_nodes(children_ids)

    print("\nsummary node:")
    print(summary_node.text)
    print("\nchildren:")
    for child in children:
        print("\nchild:")
        print(child.text)

    logger.info(f"Wrapper stats: {wrapper_stats_str()}")


def test_document_summary():
    prompt = DOCUMENT_SUMMARY
    print(f"\nprompt:\n{prompt}\n")

    test = {
        "context": "Once upon a time, in a warm and sunny place, there was a big pit. A little boy named Tom liked to play near the pit. One day, Tom lost his red ball. He was very sad.\nTom asked his friend, Sam, to help him search for the ball. They looked high and low, but they could not find the ball. Tom said, \"I think my ball fell into the pit.\"\nSam and Tom went close to the pit. They were scared, but they wanted to find the red ball. They looked into the pit, but it was too dark to see. Tom said, \"We must go in and search for my ball.\"\nThey went into the pit to search. It was dark and scary. They could not find the ball. They tried to get out, but the pit was too deep. Tom and Sam were stuck in the pit. They called for help, but no one could hear them. They were sad and scared, and they never got out of the pit.",

        "answer": "Tom, a little boy, lost his red ball and asked his friend Sam to help him search for it. They suspected it fell into a nearby pit, so they entered the pit to look for it. However, it was too dark to see, and they became stuck, unable to get out, and their calls for help went unheard.",
    }

    llm = LLMWrapper(
        model="meta/llama3-70b-instruct", 
        # model="nvidia/llama-3.1-nemotron-70b-instruct", 
        # model="meta/llama-3.2-3b-instruct",
    )
    result = llm.predict(
        DEFAULT_TREE_SUMMARIZE_PROMPT,
        context_str=test["context"],
        query_str=DOCUMENT_SUMMARY,

    )
    print(f"\nresult:\n{result}\n")
    print(f"\nexpected:\n{test['answer']}\n")


def run_prompt(prompt_id: str):
    prompt = prompt_ids[prompt_id]
    function = "test_" + prompt
    print(f"\nrunning {function}\n")
    globals()[function]()


if __name__ == "__main__":
    args = parse_args()
    run_prompt(args.prompt_test_id)
