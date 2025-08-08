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
