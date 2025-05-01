from embedding import Embedding
import chromadb
from chromadb.config import Settings

class Vector_store:
    def __init__(self):
        self.client = chromadb.PersistentClient("./data")
        self.collection = self.client.get_or_create_collection(name="educut_vec_store")
        self.emb_obj = Embedding()


    def store(self, resp, timestamps):

        docs_emb = self.emb_obj.get_embeddings(resp)
        docs_embeddings = docs_emb.cpu().detach().numpy().astype("float32").tolist()
        unique_id = f"{timestamps[0]}_{timestamps[1]}" 

        self.collection.add(
        documents=[resp],
        embeddings=docs_embeddings,
        ids=unique_id,
        metadatas=[{"timestamp": f"{timestamps[0]}s - {timestamps[1]}s"}]
        )

        return

    def query(self):
        query = "Tell me about factory pattern?"
        query_emb = self.emb_obj.get_embeddings(query, "query")
        #Query
        query_embedding = query_emb.cpu().detach().numpy().astype("float32").tolist()

           # Perform search
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=10
        )
        print("=================================================================")
        print(results)

        for doc, dist, meta in zip(results["documents"][0], results["distances"][0], results['metadatas'][0]):
            print(f"Match: {doc} (distance: {dist:.4f})\n medadata: {meta}")

# obj = Vector_store()
# obj.query()