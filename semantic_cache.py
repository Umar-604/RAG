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
        
        # Ensure cache directory exists
        os.makedirs(cache_dir, exist_ok=True)
    
    def _load_cache(self) -> Dict:
        """Load cache from disk"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'rb') as f:
                    return pickle.load(f)
            except:
                return {}
        return {}
    
    def _load_embeddings(self) -> Dict:
        """Load query embeddings from disk"""
        embeddings_file = os.path.join(self.cache_dir, "query_embeddings.pkl")
        if os.path.exists(embeddings_file):
            try:
                with open(embeddings_file, 'rb') as f:
                    return pickle.load(f)
            except:
                return {}
        return {}
    
    def _save_cache(self):
        """Save cache to disk"""
        with open(self.cache_file, 'wb') as f:
            pickle.dump(self.cache, f)
        
        embeddings_file = os.path.join(self.cache_dir, "query_embeddings.pkl")
        with open(embeddings_file, 'wb') as f:
            pickle.dump(self.query_embeddings, f)
    
    def _get_query_hash(self, query: str) -> str:
        """Generate hash for query"""
        return hashlib.md5(query.encode()).hexdigest()
    
    def _compute_similarity(self, query1: str, query2: str) -> float:
        """Compute semantic similarity between two queries"""
        embeddings = self.embedding_model.encode([query1, query2])
        similarity = np.dot(embeddings[0], embeddings[1]) / (
            np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
        )
        return similarity
    
    def get(self, query: str) -> Optional[Dict]:
        """Get cached result for similar query"""
        query_hash = self._get_query_hash(query)
        
        # Check exact match first
        if query_hash in self.cache:
            return self.cache[query_hash]
        
        # Check semantic similarity
        query_embedding = self.embedding_model.encode([query])[0]
        
        for cached_query_hash, cached_embedding in self.query_embeddings.items():
            similarity = np.dot(query_embedding, cached_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(cached_embedding)
            )
            
            if similarity >= self.similarity_threshold:
                print(f"🎯 Semantic cache hit! Similarity: {similarity:.3f}")
                return self.cache[cached_query_hash]
        
        return None
    
    def set(self, query: str, result: Dict):
        """Cache query and result"""
        query_hash = self._get_query_hash(query)
        
        # Add to cache
        self.cache[query_hash] = {
            'result': result,
            'timestamp': time.time(),
            'query': query
        }
        
        # Add embedding
        query_embedding = self.embedding_model.encode([query])[0]
        self.query_embeddings[query_hash] = query_embedding
        
        # Manage cache size
        if len(self.cache) > self.max_cache_size:
            self._evict_oldest()
        
        # Save to disk
        self._save_cache()
        print(f"💾 Cached query: {query[:50]}...")
    
    def _evict_oldest(self):
        """Remove oldest cache entries"""
        sorted_items = sorted(
            self.cache.items(), 
            key=lambda x: x[1]['timestamp']
        )
        
        # Remove oldest 20% of entries
        to_remove = len(sorted_items) // 5
        for i in range(to_remove):
            query_hash = sorted_items[i][0]
            del self.cache[query_hash]
            if query_hash in self.query_embeddings:
                del self.query_embeddings[query_hash]
    
    def clear(self):
        """Clear all cache"""
        self.cache = {}
        self.query_embeddings = {}
        self._save_cache()
        print("🗑️ Cache cleared")
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        return {
            'cache_size': len(self.cache),
            'max_size': self.max_cache_size,
            'similarity_threshold': self.similarity_threshold
        } 