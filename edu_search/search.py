"""
OpenAI-compatible Embedding API caller for llama.cpp server.
"""

import requests
from typing import Union


class EmbeddingClient:
    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        model: str = "Qwen3-Embedding-0.6B-Q8_0.gguf",
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.embedding_endpoint = f"{self.base_url}/v1/embeddings"

    def get_embedding(self, text: Union[str, list[str]]) -> list[list[float]]:

        # Normalize input to list
        if isinstance(text, str):
            input_texts = [text]
        else:
            input_texts = text

        payload = {
            "input": input_texts,
            "model": self.model,
        }

        response = requests.post(
            self.embedding_endpoint,
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()

        data = response.json()

        # Extract embeddings from OpenAI-compatible response format
        if "data" not in data:
            raise ValueError(f"Unexpected response format: {data}")

        # Sort by index to ensure correct order
        sorted_data = sorted(data["data"], key=lambda x: x["index"])
        embeddings = [item["embedding"] for item in sorted_data]

        return embeddings

    def embed_single(self, text: str) -> list[float]:
        embeddings = self.get_embedding(text)
        return embeddings[0]


# Convenience function for quick usage
def get_embeddings(
    texts: Union[str, list[str]],
    base_url: str = "http://localhost:8080",
) -> list[list[float]]:

    client = EmbeddingClient(base_url=base_url)
    return client.get_embedding(texts)


if __name__ == "__main__":
    # Example usage
    client = EmbeddingClient()

    # Single text embedding
    text = "Vector addition is a binary operation that takes two vectors as input and returns a vector as output."
    query = "What is vector addition?"
    embedding = client.embed_single(text)
    query_embedding = client.embed_single(query)
    print(f"Embedding dimension: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")
    print(f"Query embedding dimension: {len(query_embedding)}")
    print(f"Query first 5 values: {query_embedding[:5]}")

    # # Batch embedding
    # texts = ["Hello, world!", "How are you?"]
    # embeddings = client.get_embedding(texts)
    # print(f"\nBatch embeddings count: {len(embeddings)}")
