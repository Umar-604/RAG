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
    

       def _calculate_relevance(self, query: str, response: str) -> float:
        """Calculate relevance score between query and response"""
        query_words = set(query.lower().split())
        response_words = set(response.lower().split())
        
        if not query_words:
            return 0.0
        
        # Simple keyword overlap
        overlap = len(query_words.intersection(response_words))
        relevance = overlap / len(query_words)
        
        return min(relevance * 2, 1.0)  # Scale up and cap at 1.0
    
    def _calculate_factual_consistency(self, response: str, sources: List[str]) -> float:
        """Calculate factual consistency score"""
        # Simple heuristic: more sources = higher consistency
        if not sources:
            return 0.0
        
        # Base score from number of sources
        base_score = min(len(sources) / 3, 1.0)
        
        # Additional points for specific indicators
        indicators = [
            "according to",
            "based on",
            "research shows",
            "studies indicate",
            "evidence suggests"
        ]
        
        indicator_score = sum(1 for indicator in indicators if indicator in response.lower()) / len(indicators)
        
        return (base_score + indicator_score) / 2
    
    def _calculate_completeness(self, response: str) -> float:
        """Calculate response completeness"""
        # Simple heuristic based on response length and structure
        if not response:
            return 0.0
        
        # Length score (normalized)
        length_score = min(len(response.split()) / 100, 1.0)
        
        # Structure score (has sections, formatting)
        structure_indicators = [
            "**",  # Bold text
            "📄",  # Source indicators
            "---",  # Separators
            "\n\n"  # Paragraphs
        ]
        
        structure_score = sum(1 for indicator in structure_indicators if indicator in response) / len(structure_indicators)
        
        return (length_score + structure_score) / 2
    
    def get_performance_summary(self) -> Dict:
        """Get overall performance summary"""
        if not self.metrics:
            return {
                'total_queries': 0,
                'average_response_time': 0,
                'cache_hit_rate': 0,
                'average_relevance': 0,
                'average_consistency': 0,
                'average_completeness': 0
            }
        
        # Calculate averages
        avg_response_time = np.mean([m['response_time'] for m in self.metrics])
        avg_relevance = np.mean([m['relevance_score'] for m in self.metrics])
        avg_consistency = np.mean([m['factual_consistency'] for m in self.metrics])
        avg_completeness = np.mean([m['completeness'] for m in self.metrics])
        
        cache_hit_rate = self.cache_hits / self.total_queries if self.total_queries > 0 else 0
        
        return {
            'total_queries': self.total_queries,
            'average_response_time': avg_response_time,
            'cache_hit_rate': cache_hit_rate,
            'average_relevance': avg_relevance,
            'average_consistency': avg_consistency,
            'average_completeness': avg_completeness,
            'total_metrics_recorded': len(self.metrics)
        }
    