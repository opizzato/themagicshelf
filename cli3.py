from llama_index.embeddings.ollama import OllamaEmbedding

ollama_embedding = OllamaEmbedding(
    model_name="mxbai-embed-large:latest",
    base_url="https://chat.darwin-x.com",
    ollama_additional_kwargs={"mirostat": 0},
)

pass_embedding = ollama_embedding.get_text_embedding_batch(
    ["This is a passage!", "This is another passage"], show_progress=True
)
print(pass_embedding)

query_embedding = ollama_embedding.get_query_embedding("Where is blue?")
print(query_embedding)