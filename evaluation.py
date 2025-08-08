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
