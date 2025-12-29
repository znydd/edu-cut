import os
import csv
import json
import pandas as pd
import chromadb
from chromadb.utils import embedding_functions
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

class QwenSearchPipeline:
    def __init__(self, 
                 api_base=os.getenv("QWEN_API_BASE", "http://localhost:8080/v1"),
                 api_key=os.getenv("QWEN_API_KEY", "no-key"),
                 llm_model="qwen3-4b-think",
                 embed_model="qwen3-embedding",
                 rerank_model="qwen3-reranker",
                 db_path="./chromadb"):
        
        self.client = OpenAI(api_key=api_key, base_url=api_base)
        self.llm_model = llm_model
        self.embed_model = embed_model
        self.rerank_model = rerank_model
        
        self.chroma_client = chromadb.PersistentClient(path=db_path)
        self.collection = self.chroma_client.get_or_create_collection(
            name="edu_video_segments"
        )

    def get_embedding(self, text):
        response = self.client.embeddings.create(
            input=[text],
            model=self.embed_model
        )
        return response.data[0].embedding

    def load_and_index_data(self, description_csv, transcript_csv):
        """
        Loads description and transcript, merges them, and indexes into ChromaDB.
        """
        # Load descriptions
        desc_df = pd.read_csv(description_csv)
        # Load transcript
        trans_df = pd.read_csv(transcript_csv)

        # Basic merging strategy: Descriptions are already chunked segments.
        # We'll associate transcript text within the description's timestamp range.
        
        # simplified for now: just use descriptions if they already contain key info,
        # or join transcript segments roughly based on index if timestamps are hard to sync perfectly.
        # Looking at previous vec_search.ipynb, they just use description blocks.
        
        documents = []
        metadatas = []
        ids = []

        for idx, row in desc_df.iterrows():
            # Combine description and any metadata
            content = f"Timestamp: {row['timestamp']}\nDescription: {row['description']}"
            
            # Find relevant transcript parts (rough match)
            # In a real SOTA we'd parse timestamps, but here we take the description's lead.
            
            documents.append(content)
            metadatas.append({"timestamp": row["timestamp"], "id": str(row["id"])})
            ids.append(f"segment_{row['id']}")

        # Batch embed and add to collection
        # ChromaDB can handle local embedding or we can pass our OpenAI embeddings
        embeddings = [self.get_embedding(doc) for doc in documents]
        
        self.collection.add(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"Indexed {len(documents)} segments.")

    def extract_topics(self):
        """
        Extract topics from all indexed documents using the LLM.
        """
        results = self.collection.get()
        all_text = "\n---\n".join(results["documents"][:20]) # Limit context for topic extraction
        
        prompt = f"Based on the following video segment descriptions, list all major topics taught or discussed. Format as a simple comma-separated list.\n\nSegments:\n{all_text}"
        
        response = self.client.chat.completions.create(
            model=self.llm_model,
            messages=[{"role": "user", "content": prompt}]
        )
        topics = response.choices[0].message.content
        return topics

    def expand_query(self, query, topics):
        """
        Query + topic list -> LLM -> multiple better specific queries
        """
        prompt = f"""Given the user query: '{query}'
And the following topics available in the video: {topics}

Generate 3-5 more specific and better search queries that would help find the most relevant sections of the video in a vector database.
Output ONLY the queries, one per line."""

        response = self.client.chat.completions.create(
            model=self.llm_model,
            messages=[{"role": "user", "content": prompt}]
        )
        expanded_queries = response.choices[0].message.content.strip().split("\n")
        return [q.strip("- ").strip() for q in expanded_queries if q.strip()]

    def rerank(self, query, candidates):
        """
        Rerank candidates using the reranker API.
        OpenAI python package doesn't have a direct rerank method, 
        so we either use a custom endpoint if available via client.post 
        or use LLM as a reranker if model is SOTA reranker.
        """
        if not candidates:
            return []

        # Try to use a custom /rerank endpoint if the base_url supports it
        try:
            # Many OpenAI-compat servers support /rerank
            response = self.client.post(
                "/rerank",
                body={
                    "model": self.rerank_model,
                    "query": query,
                    "documents": [c["document"] for c in candidates],
                    "top_n": 5
                },
                cast_to=dict
            )
            # Standard rerank response format
            ranked_indices = [item["index"] for item in response.get("results", [])]
            return [candidates[i] for i in ranked_indices]
        except Exception as e:
            print(f"Reranking API error or not supported: {e}. Falling back to original order.")
            return candidates[:5]

    def search(self, query):
        # 1. Get topics (context)
        topics = self.extract_topics()
        print(f"Extracted Topics: {topics}")
        
        # 2. Expand query
        expanded_queries = self.expand_query(query, topics)
        expanded_queries.append(query) # keep original
        print(f"Expanded Queries: {expanded_queries}")
        
        # 3. Vector search for each query
        all_candidates = []
        seen_ids = set()
        
        for q in expanded_queries:
            q_emb = self.get_embedding(q)
            results = self.collection.query(
                query_embeddings=[q_emb],
                n_results=5
            )
            
            for i in range(len(results["ids"][0])):
                doc_id = results["ids"][0][i]
                if doc_id not in seen_ids:
                    all_candidates.append({
                        "id": doc_id,
                        "document": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i]
                    })
                    seen_ids.add(doc_id)
        
        # 4. Rerank
        final_results = self.rerank(query, all_candidates)
        return final_results

if __name__ == "__main__":
    # Example usage
    pipeline = QwenSearchPipeline()
    
    # Paths (adjust as needed)
    DESC_PATH = "/home/znyd/hacking/edu-cut/store/wxBG5Ei7a_w/responses/description.csv"
    TRANS_PATH = "/home/znyd/hacking/edu-cut/store/wxBG5Ei7a_w/subtitle/wxBG5Ei7a_w_transcript.csv"
    
    if os.path.exists(DESC_PATH) and os.path.exists(TRANS_PATH):
        # Index data if collection is empty
        if pipeline.collection.count() == 0:
            pipeline.load_and_index_data(DESC_PATH, TRANS_PATH)
        
        test_query = "explain the concept of vectors"
        results = pipeline.search(test_query)
        
        print("\n--- Search Results ---")
        for i, res in enumerate(results):
            print(f"{i+1}. [{res['metadata']['timestamp']}] {res['document'][:200]}...")
    else:
        print("Data files not found. Please check paths.")
