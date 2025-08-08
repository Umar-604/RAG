import hashlib
import json
import time
from typing import List, Dict, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle
import os

class SemanticCache:
    def __init__(self, cache_dir="./cache", similarity_threshold=0.85, max_cache_size=1000):
        self.cache_dir = cache_dir
        self.similarity_threshold = similarity_threshold
        self.max_cache_size = max_cache_size
        self.cache_file = os.path.join(cache_dir, "semantic_cache.pkl")
        
        # Initialize sentence transformer for semantic similarity
        self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        
        # Load existing cache
        self.cache = self._load_cache()
        self.query_embeddings = self._load_embeddings()
        