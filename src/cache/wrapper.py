import logging
from typing import Any, List
from llama_index.core.bridge.pydantic import Field
from llama_index.llms.nvidia import NVIDIA
from llama_index.embeddings.nvidia import NVIDIAEmbedding
from llama_index.core.base.llms.types import ChatMessage, ChatResponse, CompletionResponse, LLMMetadata
from llama_index.core.prompts import BasePromptTemplate

from src.cache.file_cache import file_cache, afile_cache


logger = logging.getLogger(__name__)

global_native_llm = None
global_native_embed_model = None

global_nb_llm_calls = 0
global_nb_embed_calls = 0

global_nb_llm_calls_cache_miss = 0
global_nb_embed_calls_cache_miss = 0

global_max_nb_llm_calls = None
global_max_nb_embed_calls = None

global_max_nb_llm_calls_cache_miss = None
global_max_nb_embed_calls_cache_miss = None


def wrapper_stats_str():
    def call_stats_str(nb_calls, nb_calls_cache_miss):
        nb_cached = nb_calls - nb_calls_cache_miss
        pc_cached = nb_cached / nb_calls * 100 if nb_calls > 0 else 0
        return f"calls:{nb_calls}, missed:{nb_calls_cache_miss}, cached:{nb_cached}({pc_cached:.0f}%)"
    llm_str = call_stats_str(global_nb_llm_calls, global_nb_llm_calls_cache_miss)
    embed_str = call_stats_str(global_nb_embed_calls, global_nb_embed_calls_cache_miss)
    return f"LLM: {llm_str}, Embedding: {embed_str}"


# llm cache call
@file_cache(verbose=True)
def chat_with_cache(messages: List[ChatMessage]) -> ChatResponse:
    global global_native_llm
    global global_nb_llm_calls_cache_miss
    global_nb_llm_calls_cache_miss += 1
    result = global_native_llm.chat(messages)
    return result

@afile_cache(verbose=True)
async def achat_with_cache(messages: List[ChatMessage]) -> ChatResponse:
    global global_native_llm
    global global_nb_llm_calls_cache_miss
    global_nb_llm_calls_cache_miss += 1
    result = await global_native_llm.achat(messages)
    return result

@file_cache(verbose=True)
def predict_with_cache(
    prompt: BasePromptTemplate,
    **prompt_args: Any,
) -> str:
    global global_native_llm
    global global_nb_llm_calls_cache_miss
    global_nb_llm_calls_cache_miss += 1
    result = global_native_llm.predict(prompt, **prompt_args)
    return result

# llm cache class
class LLMWrapper(NVIDIA):

    # field required by pydantic for the constructor
    max_nb_calls: int = Field(default=None)
    max_nb_calls_cache_miss: int = Field(default=None)

    def __init__(self, model: str, max_nb_calls: int=None, max_nb_calls_cache_miss: int=None, kwargs: dict=None):
        super().__init__(model=model, kwargs=kwargs)
        global global_native_llm
        global_native_llm = NVIDIA(model=model, kwargs=kwargs)
        global global_max_nb_llm_calls
        global_max_nb_llm_calls = max_nb_calls
        global global_max_nb_llm_calls_cache_miss
        global_max_nb_llm_calls_cache_miss = max_nb_calls_cache_miss

    def _update_and_check_nb_calls(self) -> bool:
        global global_nb_llm_calls
        global_nb_llm_calls += 1

        global global_max_nb_llm_calls
        if global_max_nb_llm_calls is not None and global_nb_llm_calls > global_max_nb_llm_calls:
            error_msg = f"Maximum number of calls to the LLM reached: {global_max_nb_llm_calls}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        global global_nb_llm_calls_cache_miss
        global global_max_nb_llm_calls_cache_miss
        if global_max_nb_llm_calls_cache_miss is not None and global_nb_llm_calls_cache_miss > global_max_nb_llm_calls_cache_miss:
            error_msg = f"Maximum number of calls cache miss to the LLM reached: {global_max_nb_llm_calls_cache_miss}"
            logger.error(error_msg)
            raise Exception(error_msg)

    def chat(
        self, messages: List[ChatMessage]
    ) -> ChatResponse:
        self._update_and_check_nb_calls()
        return chat_with_cache(messages)
    
    async def achat(
        self, messages: List[ChatMessage]
    ) -> ChatResponse:
        self._update_and_check_nb_calls()
        return await achat_with_cache(messages)
    
    def predict(
        self,
        prompt: BasePromptTemplate,
        **prompt_args: Any,
    ) -> str:
        self._update_and_check_nb_calls()
        return predict_with_cache(prompt, **prompt_args)


# embedding cache call
@file_cache(verbose=True)
def _get_text_embeddings_with_cache(texts: List[str]) -> List[List[float]]:
    global global_native_embed_model
    global global_nb_embed_calls_cache_miss
    global_nb_embed_calls_cache_miss += 1
    return global_native_embed_model._get_text_embeddings(texts)

# embedding cache class
class EmbeddingWrapper(NVIDIAEmbedding):

    # field required by pydantic for the constructor
    max_nb_calls: int = Field(default=None)
    max_nb_calls_cache_miss: int = Field(default=None)

    def __init__(self, model: str, max_nb_calls: int=None, max_nb_calls_cache_miss: int=None, kwargs: dict=None):
        super().__init__(model=model, kwargs=kwargs)
        global global_native_embed_model
        global_native_embed_model = NVIDIAEmbedding(model=model, kwargs=kwargs)
        # truncate to the end of chunks if needed to avoid context window exceptions raised by the embedding model
        global_native_embed_model.truncate = "END"
        global global_max_nb_embed_calls
        global_max_nb_embed_calls = max_nb_calls
        global global_max_nb_embed_calls_cache_miss
        global_max_nb_embed_calls_cache_miss = max_nb_calls_cache_miss

    def _update_and_check_nb_calls(self) -> bool:
        global global_nb_embed_calls
        global_nb_embed_calls += 1

        global global_max_nb_embed_calls
        if global_max_nb_embed_calls is not None and global_nb_embed_calls > global_max_nb_embed_calls:
            error_msg = f"Maximum number of calls to the embedding model reached: {self.max_nb_calls}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        global global_nb_embed_calls_cache_miss
        global global_max_nb_embed_calls_cache_miss
        if global_max_nb_embed_calls_cache_miss is not None and global_nb_embed_calls_cache_miss > global_max_nb_embed_calls_cache_miss:
            error_msg = f"Maximum number of calls cache miss to the embedding model reached: {global_max_nb_embed_calls_cache_miss}"
            logger.error(error_msg)
            raise Exception(error_msg)

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        # print(f'_get_text_embeddings: ')
        # for text in texts:
        #     print('text:')
        #     print(text)
        self._update_and_check_nb_calls()
        return _get_text_embeddings_with_cache(texts)
