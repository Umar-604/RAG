import time
import json
import os
from typing import List, Dict, Tuple
from datetime import datetime
import numpy as np
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class EvaluationMetrics:
    """Data class for storing evaluation metrics"""
    query: str
    response: str
    sources: List[str]
    response_time: float
    relevance_score: float = 0.0
    factual_consistency: float = 0.0
    completeness: float = 0.0
    timestamp: str = ""


class RAGEvaluator:
    def __init__(self, metrics_file="./metrics/rag_metrics.json"):
        self.metrics_file = metrics_file
        self.metrics_dir = os.path.dirname(metrics_file)
        os.makedirs(self.metrics_dir, exist_ok=True)
        
        # Load existing metrics
        self.metrics = self._load_metrics()
        
        # Performance tracking
        self.query_times = []
        self.cache_hits = 0
        self.total_queries = 0
    
    def _load_metrics(self) -> List[Dict]:
        """Load existing metrics from file"""
        if os.path.exists(self.metrics_file):
            try:
                with open(self.metrics_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _save_metrics(self):
        """Save metrics to file"""
        with open(self.metrics_file, 'w') as f:
            json.dump(self.metrics, f, indent=2)
   def evaluate_response(self, query: str, response: str, sources: List[str], 
                        response_time: float, cache_hit: bool = False) -> EvaluationMetrics:
        """Evaluate a single response"""
        metrics = EvaluationMetrics(
            query=query,
            response=response,
            sources=sources,
            response_time=response_time,
            timestamp=datetime.now().isoformat()
        )
        
        # Calculate relevance score (simple keyword-based for now)
        metrics.relevance_score = self._calculate_relevance(query, response)
        
        # Calculate factual consistency
        metrics.factual_consistency = self._calculate_factual_consistency(response, sources)
        
        # Calculate completeness
        metrics.completeness = self._calculate_completeness(response)
        
        # Store metrics
        self.metrics.append({
            'query': metrics.query,
            'response': metrics.response,
            'sources': metrics.sources,
            'response_time': metrics.response_time,
            'relevance_score': metrics.relevance_score,
            'factual_consistency': metrics.factual_consistency,
            'completeness': metrics.completeness,
            'cache_hit': cache_hit,
            'timestamp': metrics.timestamp
        })
        
        # Update performance tracking
        self.query_times.append(response_time)
        self.total_queries += 1
        if cache_hit:
            self.cache_hits += 1
        
        # Save metrics
        self._save_metrics()
        
        return metrics
    