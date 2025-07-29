import torch
from vlm import VLM
from embedding import Embedding
import faiss
import numpy as np
import chromadb
from chromadb.config import Settings


def main():

    video_path="./media/back_flip.mp4"
    resp = VLM().inference(video_path)
    emb_obj = Embedding()
    docs_emb = emb_obj.get_embeddings(resp)

    query = "Is someone doing backflip or jump?"
    query_emb = emb_obj.get_embeddings(query, "query")
    

    docs_embeddings = docs_emb.cpu().detach().numpy().astype("float32").tolist()

    client = chromadb.Client(Settings(anonymized_telemetry=False))
    # Create or get a collection
    collection = client.get_or_create_collection(name="educut_vector_store")


    collection.add(
    documents=[resp],
    embeddings=docs_embeddings,
    ids='0',
    metadatas=[{"source": "manual"} for _ in [resp]]
    )

    #Query
    query_embedding = query_emb.cpu().detach().numpy().astype("float32").tolist()

       # Perform search
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=1
    )
    print("=================================================================")

    for doc, dist in zip(results["documents"][0], results["distances"][0]):
        print(f"Match: {doc} (distance: {dist:.4f})")

    return

if __name__ == "__main__":
    main()
