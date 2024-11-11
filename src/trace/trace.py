import logging
import json
import os
from llama_index.core.base.llms.types import ChatMessage, ChatResponse
from llama_index.core.callbacks import LlamaDebugHandler
from llama_index.core.callbacks.schema import CBEvent, CBEventType
from llama_index.core.base.response.schema import Response
from llama_index.core.schema import Document, NodeWithScore

from src.run.utils import base_dir_for_run


logger = logging.getLogger(__name__)


class LlamaDebugEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, CBEvent):
            return {"event_type": obj.event_type.value, "payload": obj.payload, "time": obj.time, "id_": obj.id_}
        if isinstance(obj, CBEventType):
            return obj.value
        if isinstance(obj, Response):
            return {"response": obj.__str__(), "source": obj.get_formatted_sources()}
        if isinstance(obj, NodeWithScore):
            return obj.__str__()
        if isinstance(obj, ChatMessage):
            return obj.__str__()
        if isinstance(obj, ChatResponse):
            return obj.__str__()
        if isinstance(obj, Document):
            return obj.__str__()
        return obj.__str__()


def save_llama_debug(llama_debug: LlamaDebugHandler, run_id: str, base_dir: str, args=None):
    steps_str = args.steps.replace(",", "_")
    with open(os.path.join(base_dir_for_run(run_id, base_dir), f"llama_debug_{steps_str}.json"), "w") as f:
        json.dump({
            "event_pairs_by_type": llama_debug._event_pairs_by_type,
            "event_pairs_by_id": llama_debug._event_pairs_by_id,
            "sequential_events": llama_debug._sequential_events,
            "trace_map": llama_debug._trace_map,
        }, f, indent=4, cls=LlamaDebugEncoder)
