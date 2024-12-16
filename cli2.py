from llama_index.llms.ollama import Ollama

llm = Ollama(model="Qwen2.5-14B-Instruct-IQ4_XS", base_url="https://chat.darwin-x.com", request_timeout=60.0)

response = llm.complete("What is the capital of France?")
print(response)