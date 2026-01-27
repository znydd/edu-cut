"""
Video Chunk Semantic Search with LLM Verification

Two-Phase Pipeline:
  Phase A (Offline): Ingest CSV → embed descriptions → store in ChromaDB
  Phase B (Runtime): Query → LLM rewrite → embed → vector search → LLM verify → post-process

Usage:
  # Phase A: Ingest chunks
  uv run python -m edu_search.search_v2 ingest --csv path/to/description.csv

  # Phase B: Search
  uv run python -m edu_search.search_v2 search --query "..." --db-path ./chromadb_v2
"""

import os
import re
import csv
import json
from pathlib import Path
from dataclasses import dataclass

import chromadb
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


# ============================================================================
# Utilities
# ============================================================================

def parse_timestamp(timestamp: str) -> tuple[float, float]:
    """
    Parse timestamp string HH:MM:SS.mmm-HH:MM:SS.mmm into (start_sec, end_sec).
    
    Examples:
        "00:00:00.000-00:00:10.500" -> (0.0, 10.5)
        "00:01:30.000-00:02:00.000" -> (90.0, 120.0)
    """
    pattern = r"(\d{2}):(\d{2}):(\d{2})\.(\d{3})-(\d{2}):(\d{2}):(\d{2})\.(\d{3})"
    match = re.match(pattern, timestamp)
    
    if not match:
        raise ValueError(f"Invalid timestamp format: {timestamp}")
    
    h1, m1, s1, ms1, h2, m2, s2, ms2 = map(int, match.groups())
    
    start_sec = h1 * 3600 + m1 * 60 + s1 + ms1 / 1000
    end_sec = h2 * 3600 + m2 * 60 + s2 + ms2 / 1000
    
    return start_sec, end_sec


def format_timestamp(start_sec: float, end_sec: float) -> str:
    """Convert numeric seconds back to HH:MM:SS.mmm-HH:MM:SS.mmm format."""
    def sec_to_str(sec: float) -> str:
        h = int(sec // 3600)
        m = int((sec % 3600) // 60)
        s = int(sec % 60)
        ms = int((sec % 1) * 1000)
        return f"{h:02}:{m:02}:{s:02}.{ms:03}"
    
    return f"{sec_to_str(start_sec)}-{sec_to_str(end_sec)}"


@dataclass
class SearchResult:
    """Final search result after post-processing."""
    chunk_ids: list[str]
    start_sec: float
    end_sec: float
    timestamp: str
    description: str = ""


# ============================================================================
# Phase A: Offline Ingest
# ============================================================================

class VideoChunkIngest:
    """Ingests video chunk descriptions into ChromaDB."""
    
    def __init__(
        self,
        db_path: str = "./chromadb_v2",
        collection_name: str = "video_chunks",
        api_base: str = None,
        api_key: str = "no-key",
        embed_model: str = "text-embedding",
    ):
        self.db_path = db_path
        self.collection_name = collection_name
        
        # OpenAI-compatible client for local llama.cpp server
        self.api_base = api_base or os.getenv("LLAMA_API_BASE", "http://localhost:8080/v1")
        self.client = OpenAI(api_key=api_key, base_url=self.api_base)
        self.embed_model = embed_model
        
        # ChromaDB setup
        self.chroma_client = chromadb.PersistentClient(path=db_path)
        self.collection = self.chroma_client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
    
    def get_embedding(self, text: str) -> list[float]:
        """Generate embedding for text using local embedding model."""
        response = self.client.embeddings.create(
            input=[text],
            model=self.embed_model
        )
        return response.data[0].embedding
    
    def load_csv(self, csv_path: str) -> list[dict]:
        """Load CSV with columns: id, timestamp, description."""
        chunks = []
        
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                chunk_id = str(row["id"])
                timestamp = row["timestamp"]
                description = row["description"]
                
                start_sec, end_sec = parse_timestamp(timestamp)
                
                chunks.append({
                    "id": chunk_id,
                    "timestamp": timestamp,
                    "start_sec": start_sec,
                    "end_sec": end_sec,
                    "description": description,
                })
        
        return chunks
    
    def run(self, csv_path: str, batch_size: int = 10) -> int:
        """
        Main ingest pipeline:
        1. Load CSV
        2. Generate embeddings  
        3. Store in ChromaDB
        
        Returns number of chunks ingested.
        """
        chunks = self.load_csv(csv_path)
        print(f"Loaded {len(chunks)} chunks from {csv_path}")
        
        # Process in batches
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            
            ids = []
            embeddings = []
            documents = []
            metadatas = []
            
            for chunk in batch:
                embedding = self.get_embedding(chunk["description"])
                
                ids.append(f"chunk_{chunk['id']}")
                embeddings.append(embedding)
                documents.append(chunk["description"])
                metadatas.append({
                    "id": chunk["id"],
                    "timestamp": chunk["timestamp"],
                    "start_sec": chunk["start_sec"],
                    "end_sec": chunk["end_sec"],
                })
            
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            )
            
            print(f"Ingested batch {i // batch_size + 1} ({len(batch)} chunks)")
        
        print(f"Total chunks in collection: {self.collection.count()}")
        return len(chunks)


# ============================================================================
# Phase B: Runtime Search
# ============================================================================

class VideoSearchPipeline:
    """
    Runtime search pipeline with LLM query rewriting and verification.
    
    Flow:
    1. LLM rewrites user query for better retrieval
    2. Embed the rewritten query
    3. Vector search returns top-K candidates
    4. LLM verifies and selects relevant chunks
    5. Post-process: filter small chunks, merge adjacent
    """
    
    def __init__(
        self,
        db_path: str = "./chromadb_v2",
        collection_name: str = "video_chunks",
        embed_api_base: str = None,
        llm_api_base: str = None,
        api_key: str = "no-key",
        embed_model: str = "text-embedding",
        llm_model: str = "qwen3-4b",
        top_k: int = 20,
        min_duration: float = 2.0,
        merge_gap: float = 3.0,
    ):
        self.db_path = db_path
        self.collection_name = collection_name
        self.top_k = top_k
        self.min_duration = min_duration
        self.merge_gap = merge_gap
        
        # Embedding client
        self.embed_api_base = embed_api_base or os.getenv("EMBED_API_BASE", "http://localhost:8080/v1")
        self.embed_client = OpenAI(api_key=api_key, base_url=self.embed_api_base)
        self.embed_model = embed_model
        
        # LLM client (may be same or different server)
        self.llm_api_base = llm_api_base or os.getenv("LLM_API_BASE", "http://localhost:8081/v1")
        self.llm_client = OpenAI(api_key=api_key, base_url=self.llm_api_base)
        self.llm_model = llm_model
        
        # ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=db_path)
        self.collection = self.chroma_client.get_collection(name=collection_name)
    
    def get_embedding(self, text: str) -> list[float]:
        """Generate embedding for query."""
        response = self.embed_client.embeddings.create(
            input=[text],
            model=self.embed_model
        )
        return response.data[0].embedding
    
    def rewrite_query(self, query: str) -> str:
        """
        Use LLM to rewrite query for better semantic retrieval.
        Returns plain text improved query.
        """
        prompt = f"""Rewrite the following user query to improve semantic search retrieval for finding relevant video segments.
Make it more specific and descriptive while preserving the original intent.
Output ONLY the rewritten query, nothing else.

User query: {query}

Rewritten query:"""
        
        try:
            response = self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200,
            )
            rewritten = response.choices[0].message.content.strip()
            print(f"[Query Rewrite] {query} -> {rewritten}")
            return rewritten
        except Exception as e:
            print(f"[Query Rewrite Error] {e}, using original query")
            return query
    
    def search_vectors(self, query_embedding: list[float]) -> list[dict]:
        """Perform vector similarity search, return top-K candidates."""
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=self.top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        candidates = []
        for i in range(len(results["ids"][0])):
            candidates.append({
                "id": results["metadatas"][0][i]["id"],
                "timestamp": results["metadatas"][0][i]["timestamp"],
                "start_sec": results["metadatas"][0][i]["start_sec"],
                "end_sec": results["metadatas"][0][i]["end_sec"],
                "description": results["documents"][0][i],
                "distance": results["distances"][0][i],
            })
        
        return candidates
    
    def verify_chunks(self, query: str, candidates: list[dict]) -> list[str]:
        """
        Use LLM to verify which candidate chunks actually answer the query.
        Returns list of selected chunk IDs.
        """
        # Build context for LLM
        chunks_text = "\n\n".join([
            f"[Chunk {c['id']}] ({c['timestamp']})\n{c['description'][:500]}..."
            for c in candidates[:10]  # Limit to top 10 for context
        ])
        
        prompt = f"""You are a video search assistant. Given a user query and a list of video segment descriptions,
select the chunks that are MOST RELEVANT to answering the query.

User Query: {query}

Video Segments:
{chunks_text}

Return a JSON array of selected chunk IDs that are relevant to the query.
Only include chunks that directly address the query topic.
Output ONLY the JSON array, nothing else.

Example output: ["0", "3", "7"]

Selected chunks:"""

        try:
            response = self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=100,
            )
            content = response.choices[0].message.content.strip()
            
            # Parse JSON array
            # Handle potential markdown code blocks
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            selected_ids = json.loads(content)
            print(f"[LLM Verification] Selected {len(selected_ids)} chunks: {selected_ids}")
            return selected_ids
            
        except Exception as e:
            print(f"[LLM Verification Error] {e}, falling back to top results")
            # Fallback: return top 5 chunks by distance
            return [c["id"] for c in candidates[:5]]
    
    def post_process(self, candidates: list[dict], selected_ids: list[str]) -> list[SearchResult]:
        """
        Post-process selected chunks:
        1. Filter chunks < min_duration
        2. Merge adjacent chunks with gap <= merge_gap
        """
        # Filter to selected chunks
        selected = [c for c in candidates if c["id"] in selected_ids]
        
        if not selected:
            return []
        
        # Filter by duration
        selected = [
            c for c in selected
            if (c["end_sec"] - c["start_sec"]) >= self.min_duration
        ]
        
        if not selected:
            return []
        
        # Sort by start time
        selected.sort(key=lambda c: c["start_sec"])
        
        # Merge adjacent chunks
        merged = []
        current_group = [selected[0]]
        
        for chunk in selected[1:]:
            prev = current_group[-1]
            gap = chunk["start_sec"] - prev["end_sec"]
            
            if gap <= self.merge_gap:
                # Merge into current group
                current_group.append(chunk)
            else:
                # Finalize current group and start new
                merged.append(self._finalize_group(current_group))
                current_group = [chunk]
        
        # Finalize last group
        merged.append(self._finalize_group(current_group))
        
        return merged
    
    def _finalize_group(self, group: list[dict]) -> SearchResult:
        """Convert a group of chunks into a single SearchResult."""
        start_sec = min(c["start_sec"] for c in group)
        end_sec = max(c["end_sec"] for c in group)
        chunk_ids = [c["id"] for c in group]
        descriptions = [c["description"][:200] for c in group]
        
        return SearchResult(
            chunk_ids=chunk_ids,
            start_sec=start_sec,
            end_sec=end_sec,
            timestamp=format_timestamp(start_sec, end_sec),
            description="\n---\n".join(descriptions),
        )
    
    def search(self, query: str) -> list[SearchResult]:
        """
        Main search entry point.
        
        Returns list of SearchResult with chunk_ids, start_sec, end_sec, timestamp.
        """
        print(f"\n[Search] Query: {query}")
        
        # 1. Rewrite query for better retrieval
        improved_query = self.rewrite_query(query)
        
        # 2. Embed query
        query_embedding = self.get_embedding(improved_query)
        
        # 3. Vector search
        candidates = self.search_vectors(query_embedding)
        print(f"[Vector Search] Found {len(candidates)} candidates")
        
        if not candidates:
            return []
        
        # 4. LLM verification
        selected_ids = self.verify_chunks(query, candidates)
        
        # 5. Post-process
        results = self.post_process(candidates, selected_ids)
        print(f"[Post-Process] {len(results)} final results after filtering/merging")
        
        return results


# ============================================================================
# CLI Entry Points
# ============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Video Chunk Semantic Search with LLM Verification"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest CSV into vector DB")
    ingest_parser.add_argument("--csv", required=True, help="Path to description CSV")
    ingest_parser.add_argument("--db-path", default="./chromadb_v2", help="ChromaDB path")
    ingest_parser.add_argument("--collection", default="video_chunks", help="Collection name")
    ingest_parser.add_argument("--embed-api", default=None, help="Embedding API base URL")
    ingest_parser.add_argument("--batch-size", type=int, default=10, help="Batch size")
    
    # Rewrite-query command (Step 1 for single-GPU workflow)
    rewrite_parser = subparsers.add_parser("rewrite-query", help="[Single-GPU Step 1] LLM rewrites query for better retrieval")
    rewrite_parser.add_argument("--query", required=True, help="Original search query")
    rewrite_parser.add_argument("--output", default="./improved_query.txt", help="Output file for improved query")
    rewrite_parser.add_argument("--llm-api", default=None, help="LLM API base URL")
    
    # Search command (Step 2 for single-GPU OR full search)
    search_parser = subparsers.add_parser("search", help="[Single-GPU Step 2] Embed query, vector search, group results")
    search_parser.add_argument("--query", default=None, help="Search query (or use --query-file)")
    search_parser.add_argument("--query-file", default=None, help="File containing improved query (from rewrite-query)")
    search_parser.add_argument("--db-path", default="./chromadb_v2", help="ChromaDB path")
    search_parser.add_argument("--collection", default="video_chunks", help="Collection name")
    search_parser.add_argument("--embed-api", default=None, help="Embedding API base URL")
    search_parser.add_argument("--top-k", type=int, default=20, help="Top K candidates per query")
    search_parser.add_argument("--top-results", type=int, default=5, help="Final top N chunks to return")
    
    args = parser.parse_args()
    
    if args.command == "ingest":
        ingest = VideoChunkIngest(
            db_path=args.db_path,
            collection_name=args.collection,
            api_base=args.embed_api,
        )
        count = ingest.run(args.csv, batch_size=args.batch_size)
        print(f"\n✓ Successfully ingested {count} chunks")
    
    elif args.command == "rewrite-query":
        # Step 1: LLM rewrites query for better retrieval
        print(f"\n[Step 1] Rewriting query with LLM...")
        print(f"  Original: {args.query}")
        
        llm_api = args.llm_api or os.getenv("LLM_API_BASE", "http://localhost:8080/v1")
        llm_client = OpenAI(api_key="no-key", base_url=llm_api)
        
        prompt = f"""Generate 3 different paraphrases or alternative representations of the following query.
Each paraphrase should capture the same meaning but use different words or phrasing.
Output each paraphrase on a new line, nothing else.

Query: {args.query}

Paraphrases:"""
        
        try:
            response = llm_client.chat.completions.create(
                model="qwen3-4b",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=300,
            )
            content = response.choices[0].message.content.strip()
            
            # Parse paraphrases (one per line, clean up numbering/bullets)
            paraphrases = []
            for line in content.split('\n'):
                line = line.strip()
                if not line:
                    continue
                # Remove common prefixes like "1.", "- ", "* ", etc.
                line = line.lstrip('0123456789.-*) ').strip()
                line = line.strip('"\'')
                if line:
                    paraphrases.append(line)
            
            # Add original query too
            paraphrases.insert(0, args.query)
            
            print(f"  Generated {len(paraphrases)} queries:")
            for i, p in enumerate(paraphrases):
                print(f"    {i+1}. {p}")
            
            # Save to file (one per line)
            with open(args.output, "w") as f:
                f.write('\n'.join(paraphrases))
            
            print(f"\n✓ Saved to {args.output}")
            print(f"\nNow switch to embedding server and run:")
            print(f"  uv run python -m edu_search.search_v2 search --query-file {args.output}")
            
        except Exception as e:
            print(f"\n✗ LLM error: {e}")
            print("Saving original query instead...")
            with open(args.output, "w") as f:
                f.write(args.query)
    
    elif args.command == "search":
        # Step 2: Embed query, vector search, group results
        
        # Get queries from file or argument
        queries = []
        if args.query_file:
            with open(args.query_file, "r") as f:
                queries = [line.strip() for line in f if line.strip()]
            print(f"\n[Step 2] Searching with {len(queries)} queries from file...")
        elif args.query:
            queries = [args.query]
            print(f"\n[Search] Direct query mode...")
        else:
            print("Error: Must provide --query or --query-file")
            return
        
        for i, q in enumerate(queries):
            print(f"  {i+1}. {q}")
        
        # Embed queries and search
        embed_api = args.embed_api or os.getenv("EMBED_API_BASE", "http://localhost:8080/v1")
        embed_client = OpenAI(api_key="no-key", base_url=embed_api)
        
        chroma_client = chromadb.PersistentClient(path=args.db_path)
        collection = chroma_client.get_collection(name=args.collection)
        
        # Collect all candidates, deduplicate by ID
        all_candidates = {}
        
        for query in queries:
            response = embed_client.embeddings.create(
                input=[query],
                model="text-embedding"
            )
            query_embedding = response.data[0].embedding
            
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=args.top_k,
                include=["documents", "metadatas", "distances"]
            )
            
            for i in range(len(results["ids"][0])):
                chunk_id = results["metadatas"][0][i]["id"]
                if chunk_id not in all_candidates:
                    all_candidates[chunk_id] = {
                        "id": chunk_id,
                        "timestamp": results["metadatas"][0][i]["timestamp"],
                        "start_sec": results["metadatas"][0][i]["start_sec"],
                        "end_sec": results["metadatas"][0][i]["end_sec"],
                        "description": results["documents"][0][i],
                        "distance": results["distances"][0][i],
                    }
                else:
                    # Keep the better (lower) distance
                    if results["distances"][0][i] < all_candidates[chunk_id]["distance"]:
                        all_candidates[chunk_id]["distance"] = results["distances"][0][i]
        
        candidates = list(all_candidates.values())
        print(f"\n  ✓ Found {len(candidates)} unique candidates from {len(queries)} queries")
        
        if not candidates:
            print("\nNo results.")
            return
        
        # Sort by distance (lower = better match) and take top N
        candidates.sort(key=lambda c: c["distance"])
        candidates = candidates[:args.top_results]
        
        # Output results
        print("\n" + "="*60)
        print(f"TOP {len(candidates)} RESULTS")
        print("="*60)
        
        for i, c in enumerate(candidates, 1):
            print(f"\n[{i}] Chunk {c['id']}")
            print(f"  Timestamp: {c['timestamp']}")
            print(f"  Distance:  {c['distance']:.4f}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
