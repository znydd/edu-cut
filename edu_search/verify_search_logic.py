import unittest
from unittest.mock import MagicMock, patch
import os
import pandas as pd
from edu_search.search import QwenSearchPipeline

class TestSearchPipeline(unittest.TestCase):
    def setUp(self):
        # Mock ChromaDB client to avoid actual disk writes during unit tests
        with patch('chromadb.PersistentClient') as mock_chroma:
            self.pipeline = QwenSearchPipeline(db_path=":memory:")
            self.pipeline.chroma_client = mock_chroma.return_value
            self.pipeline.collection = MagicMock()

    @patch('openai.OpenAI')
    @patch('pandas.read_csv')
    def test_indexing(self, mock_read_csv, mock_openai):
        # Setup mock data for CSVs
        desc_data = {
            'id': [0, 1],
            'timestamp': ['00:00:00.000-00:00:09.000', '00:00:09.000-00:00:20.000'],
            'description': ['Intro to vectors', 'Vector addition']
        }
        trans_data = {
            'Start': [5.62, 10.0],
            'End': [9.0, 15.0],
            'Segment': ['Music', 'Let\'s add vectors']
        }
        
        mock_read_csv.side_effect = [pd.DataFrame(desc_data), pd.DataFrame(trans_data)]
        
        # Mock embedding response
        mock_emb_resp = MagicMock()
        mock_emb_resp.data = [MagicMock(embedding=[0.1]*128)]
        self.pipeline.client = MagicMock()
        self.pipeline.client.embeddings.create.return_value = mock_emb_resp
        
        self.pipeline.load_and_index_data("desc.csv", "trans.csv")
        
        self.assertTrue(self.pipeline.collection.add.called)
        self.assertEqual(len(self.pipeline.collection.add.call_args[1]['ids']), 2)

    @patch('openai.OpenAI')
    def test_search_flow(self, mock_openai):
        # Mock extract_topics
        self.pipeline.extract_topics = MagicMock(return_value="vectors, addition")
        # Mock expand_query
        self.pipeline.expand_query = MagicMock(return_value=["what is a vector", "how to add vectors"])
        # Mock get_embedding
        self.pipeline.get_embedding = MagicMock(return_value=[0.1]*128)
        
        # Mock collection search results
        self.pipeline.collection.query.return_value = {
            "ids": [["segment_0"]],
            "documents": [["Intro content"]],
            "metadatas": [[{"timestamp": "0-10s"}]]
        }
        
        # Mock rerank (bypassing it or mocking successfully)
        self.pipeline.rerank = MagicMock(side_effect=lambda q, c: c[:1])
        
        results = self.pipeline.search("vector concepts")
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], "segment_0")
        self.assertTrue(self.pipeline.extract_topics.called)
        self.assertTrue(self.pipeline.expand_query.called)

if __name__ == '__main__':
    unittest.main()
