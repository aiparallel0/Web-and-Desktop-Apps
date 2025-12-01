"""
=============================================================================
INTELLIGENT ANALYZER - ML-Based Pattern Analysis and Anomaly Detection
=============================================================================

This module implements Phase 2 of the CEF development path:
- ML-based pattern clustering for error categorization
- Anomaly detection for performance regressions
- Code embedding models for semantic similarity
- Historical trend analysis and forecasting

Circular Exchange Framework Integration:
-----------------------------------------
Module ID: shared.circular_exchange.intelligent_analyzer
Description: ML-powered analysis for intelligent continuous improvement
Dependencies: [shared.circular_exchange.data_collector, shared.circular_exchange.metrics_analyzer, shared.circular_exchange.persistence]
Exports: [IntelligentAnalyzer, PatternCluster, AnomalyDetector, TrendAnalyzer, CodeEmbeddings, INTELLIGENT_ANALYZER]

=============================================================================
"""

import logging
import threading
import math
import hashlib
from typing import Dict, Any, Optional, List, Tuple, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from enum import Enum
import statistics
import re

logger = logging.getLogger(__name__)


class AnomalyType(Enum):
    """Types of anomalies detected."""
    PERFORMANCE_SPIKE = "performance_spike"
    ERROR_RATE_INCREASE = "error_rate_increase"
    LATENCY_DEGRADATION = "latency_degradation"
    MEMORY_SPIKE = "memory_spike"
    SUCCESS_RATE_DROP = "success_rate_drop"
    UNUSUAL_PATTERN = "unusual_pattern"


class TrendDirection(Enum):
    """Direction of a trend."""
    IMPROVING = "improving"
    STABLE = "stable"
    DEGRADING = "degrading"
    VOLATILE = "volatile"


class ClusterQuality(Enum):
    """Quality rating for pattern clusters."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class PatternCluster:
    """Represents a cluster of similar patterns."""
    cluster_id: str
    name: str
    description: str
    pattern_ids: List[str] = field(default_factory=list)
    centroid_features: Dict[str, float] = field(default_factory=dict)
    sample_messages: List[str] = field(default_factory=list)
    total_occurrences: int = 0
    quality: ClusterQuality = ClusterQuality.MEDIUM
    root_cause: Optional[str] = None
    suggested_fix: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['quality'] = self.quality.value
        data['created_at'] = self.created_at.isoformat()
        return data


@dataclass
class Anomaly:
    """Represents a detected anomaly."""
    anomaly_id: str
    anomaly_type: AnomalyType
    description: str
    severity: float  # 0.0 to 1.0
    detected_at: datetime
    metric_name: str
    expected_value: float
    actual_value: float
    deviation_percent: float
    affected_components: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    is_resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['anomaly_type'] = self.anomaly_type.value
        data['detected_at'] = self.detected_at.isoformat()
        if self.resolved_at:
            data['resolved_at'] = self.resolved_at.isoformat()
        return data


@dataclass
class TrendAnalysis:
    """Represents trend analysis results."""
    analysis_id: str
    metric_name: str
    time_range: str
    direction: TrendDirection
    slope: float  # Rate of change
    r_squared: float  # Goodness of fit (0.0 to 1.0)
    data_points: int
    forecast_next_period: float
    forecast_confidence: float
    seasonal_pattern: Optional[str] = None
    change_points: List[datetime] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['direction'] = self.direction.value
        data['created_at'] = self.created_at.isoformat()
        data['change_points'] = [cp.isoformat() for cp in self.change_points]
        return data


@dataclass
class CodeSimilarity:
    """Represents similarity between code elements."""
    source_id: str
    target_id: str
    similarity_score: float  # 0.0 to 1.0
    similarity_type: str  # "semantic", "structural", "lexical"
    common_patterns: List[str] = field(default_factory=list)
    suggested_refactoring: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


class PatternClusterer:
    """
    Clusters similar patterns using feature-based similarity.
    
    This is a lightweight implementation that doesn't require
    external ML libraries, using cosine similarity and
    hierarchical agglomerative clustering concepts.
    """
    
    def __init__(self, similarity_threshold: float = 0.7):
        self.similarity_threshold = similarity_threshold
        self._clusters: Dict[str, PatternCluster] = {}
        self._pattern_to_cluster: Dict[str, str] = {}
    
    def cluster_patterns(self, patterns: List[Dict[str, Any]]) -> List[PatternCluster]:
        """
        Cluster patterns based on feature similarity.
        
        Args:
            patterns: List of pattern dictionaries with 'pattern_id', 'description', 'metadata'
            
        Returns:
            List of PatternCluster objects
        """
        if not patterns:
            return []
        
        # Extract features from each pattern
        pattern_features: Dict[str, Dict[str, float]] = {}
        for pattern in patterns:
            features = self._extract_features(pattern)
            pattern_features[pattern['pattern_id']] = features
        
        # Perform clustering using simple agglomerative approach
        clusters = self._agglomerative_cluster(pattern_features, patterns)
        
        return clusters
    
    def _extract_features(self, pattern: Dict[str, Any]) -> Dict[str, float]:
        """Extract feature vector from a pattern."""
        features = {}
        
        # Text-based features from description
        description = pattern.get('description', '')
        words = re.findall(r'\w+', description.lower())
        word_counts = Counter(words)
        
        # Key error keywords
        error_keywords = ['timeout', 'connection', 'memory', 'null', 'exception',
                         'failed', 'error', 'invalid', 'missing', 'permission',
                         'overflow', 'crash', 'deadlock', 'race', 'leak']
        
        for keyword in error_keywords:
            features[f'kw_{keyword}'] = float(word_counts.get(keyword, 0))
        
        # Numeric features
        features['occurrences'] = float(pattern.get('occurrences', 0))
        features['confidence'] = float(pattern.get('confidence', 0.0))
        features['num_modules'] = float(len(pattern.get('affected_modules', [])))
        
        # Pattern type as one-hot
        pattern_type = pattern.get('pattern_type', '')
        if isinstance(pattern_type, str):
            features[f'type_{pattern_type}'] = 1.0
        
        return features
    
    def _cosine_similarity(self, features1: Dict[str, float], features2: Dict[str, float]) -> float:
        """Calculate cosine similarity between two feature vectors."""
        all_keys = set(features1.keys()) | set(features2.keys())
        
        dot_product = sum(features1.get(k, 0) * features2.get(k, 0) for k in all_keys)
        norm1 = math.sqrt(sum(v ** 2 for v in features1.values()))
        norm2 = math.sqrt(sum(v ** 2 for v in features2.values()))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _agglomerative_cluster(
        self,
        pattern_features: Dict[str, Dict[str, float]],
        patterns: List[Dict[str, Any]]
    ) -> List[PatternCluster]:
        """Perform agglomerative clustering on patterns."""
        pattern_ids = list(pattern_features.keys())
        pattern_map = {p['pattern_id']: p for p in patterns}
        
        # Start with each pattern in its own cluster
        current_clusters: List[Set[str]] = [{pid} for pid in pattern_ids]
        
        # Iteratively merge most similar clusters
        while len(current_clusters) > 1:
            best_similarity = 0.0
            best_pair = (0, 1)
            
            for i in range(len(current_clusters)):
                for j in range(i + 1, len(current_clusters)):
                    sim = self._cluster_similarity(
                        current_clusters[i],
                        current_clusters[j],
                        pattern_features
                    )
                    if sim > best_similarity:
                        best_similarity = sim
                        best_pair = (i, j)
            
            if best_similarity < self.similarity_threshold:
                break
            
            # Merge the best pair
            i, j = best_pair
            merged = current_clusters[i] | current_clusters[j]
            current_clusters = [c for idx, c in enumerate(current_clusters) if idx not in (i, j)]
            current_clusters.append(merged)
        
        # Convert to PatternCluster objects
        result_clusters = []
        for idx, cluster_pids in enumerate(current_clusters):
            cluster_patterns = [pattern_map[pid] for pid in cluster_pids if pid in pattern_map]
            
            if not cluster_patterns:
                continue
            
            # Calculate centroid features
            centroid = self._calculate_centroid([pattern_features[pid] for pid in cluster_pids])
            
            # Generate cluster name and description
            name, description = self._generate_cluster_name(cluster_patterns)
            
            # Determine root cause and fix
            root_cause, suggested_fix = self._analyze_cluster_root_cause(cluster_patterns)
            
            cluster = PatternCluster(
                cluster_id=f"cluster_{idx}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                name=name,
                description=description,
                pattern_ids=list(cluster_pids),
                centroid_features=centroid,
                sample_messages=[p.get('description', '')[:100] for p in cluster_patterns[:3]],
                total_occurrences=sum(p.get('occurrences', 0) for p in cluster_patterns),
                quality=ClusterQuality.HIGH if len(cluster_pids) >= 3 else ClusterQuality.MEDIUM,
                root_cause=root_cause,
                suggested_fix=suggested_fix
            )
            result_clusters.append(cluster)
            
            # Update mappings
            self._clusters[cluster.cluster_id] = cluster
            for pid in cluster_pids:
                self._pattern_to_cluster[pid] = cluster.cluster_id
        
        return result_clusters
    
    def _cluster_similarity(
        self,
        cluster1: Set[str],
        cluster2: Set[str],
        pattern_features: Dict[str, Dict[str, float]]
    ) -> float:
        """Calculate average linkage similarity between clusters."""
        similarities = []
        for pid1 in cluster1:
            for pid2 in cluster2:
                if pid1 in pattern_features and pid2 in pattern_features:
                    sim = self._cosine_similarity(pattern_features[pid1], pattern_features[pid2])
                    similarities.append(sim)
        
        return statistics.mean(similarities) if similarities else 0.0
    
    def _calculate_centroid(self, feature_vectors: List[Dict[str, float]]) -> Dict[str, float]:
        """Calculate centroid of feature vectors."""
        if not feature_vectors:
            return {}
        
        all_keys = set()
        for fv in feature_vectors:
            all_keys.update(fv.keys())
        
        centroid = {}
        for key in all_keys:
            values = [fv.get(key, 0.0) for fv in feature_vectors]
            centroid[key] = statistics.mean(values)
        
        return centroid
    
    def _generate_cluster_name(self, patterns: List[Dict[str, Any]]) -> Tuple[str, str]:
        """Generate a name and description for a cluster."""
        # Find common keywords
        all_words = []
        for pattern in patterns:
            desc = pattern.get('description', '')
            words = re.findall(r'\w+', desc.lower())
            all_words.extend(words)
        
        word_counts = Counter(all_words)
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'in', 'on', 'at', 'to', 'for'}
        common_words = [w for w, _ in word_counts.most_common(5) if w not in stop_words and len(w) > 2]
        
        name = f"{' '.join(common_words[:2]).title()} Issues" if common_words else "Related Issues"
        description = f"Cluster of {len(patterns)} related patterns with common themes: {', '.join(common_words[:3])}"
        
        return name, description
    
    def _analyze_cluster_root_cause(self, patterns: List[Dict[str, Any]]) -> Tuple[Optional[str], Optional[str]]:
        """Analyze cluster to determine root cause and suggested fix."""
        all_descriptions = ' '.join(p.get('description', '') for p in patterns).lower()
        
        # Common root cause patterns
        root_causes = {
            'connection timeout': ('Network connectivity issues', 'Add retry logic with exponential backoff'),
            'pool exhaustion': ('Resource pool limits reached', 'Increase pool size or add queuing'),
            'memory error': ('Memory allocation failures', 'Add memory limits and garbage collection'),
            'null pointer': ('Uninitialized or null references', 'Add null checks and defensive programming'),
            'permission denied': ('Access control issues', 'Review and update permissions'),
            'rate limit': ('API rate limiting', 'Implement request throttling and caching'),
        }
        
        for pattern, (cause, fix) in root_causes.items():
            if pattern in all_descriptions:
                return cause, fix
        
        return None, None
    
    def get_cluster(self, cluster_id: str) -> Optional[PatternCluster]:
        """Get a cluster by ID."""
        return self._clusters.get(cluster_id)
    
    def get_cluster_for_pattern(self, pattern_id: str) -> Optional[PatternCluster]:
        """Get the cluster containing a specific pattern."""
        cluster_id = self._pattern_to_cluster.get(pattern_id)
        if cluster_id:
            return self._clusters.get(cluster_id)
        return None


class AnomalyDetector:
    """
    Detects anomalies in time series data using statistical methods.
    
    Uses Z-score based detection with rolling statistics for
    identifying performance regressions and unusual patterns.
    """
    
    def __init__(
        self,
        z_score_threshold: float = 2.5,
        min_samples: int = 10,
        rolling_window: int = 20
    ):
        self.z_score_threshold = z_score_threshold
        self.min_samples = min_samples
        self.rolling_window = rolling_window
        self._baselines: Dict[str, Dict[str, float]] = {}
        self._detected_anomalies: List[Anomaly] = []
    
    def update_baseline(
        self,
        metric_name: str,
        values: List[float]
    ) -> Dict[str, float]:
        """Update the baseline statistics for a metric."""
        if len(values) < self.min_samples:
            return {}
        
        baseline = {
            'mean': statistics.mean(values),
            'std': statistics.stdev(values) if len(values) > 1 else 0.0,
            'median': statistics.median(values),
            'min': min(values),
            'max': max(values),
            'sample_count': len(values),
            'updated_at': datetime.now().isoformat()
        }
        
        self._baselines[metric_name] = baseline
        return baseline
    
    def detect_anomalies(
        self,
        metric_name: str,
        values: List[Tuple[datetime, float]],
        component: str = ""
    ) -> List[Anomaly]:
        """
        Detect anomalies in a time series of values.
        
        Args:
            metric_name: Name of the metric being analyzed
            values: List of (timestamp, value) tuples
            component: Component name for context
            
        Returns:
            List of detected Anomaly objects
        """
        if len(values) < self.min_samples:
            return []
        
        # Sort by timestamp
        sorted_values = sorted(values, key=lambda x: x[0])
        timestamps = [v[0] for v in sorted_values]
        measurements = [v[1] for v in sorted_values]
        
        # Update baseline with all values
        self.update_baseline(metric_name, measurements)
        baseline = self._baselines.get(metric_name, {})
        
        if not baseline or baseline.get('std', 0) == 0:
            return []
        
        mean = baseline['mean']
        std = baseline['std']
        
        anomalies = []
        for i, (timestamp, value) in enumerate(sorted_values):
            # Calculate Z-score
            z_score = abs(value - mean) / std if std > 0 else 0.0
            
            if z_score > self.z_score_threshold:
                deviation_percent = ((value - mean) / mean * 100) if mean != 0 else 0.0
                
                # Determine anomaly type
                if value > mean:
                    if 'latency' in metric_name.lower() or 'time' in metric_name.lower():
                        anomaly_type = AnomalyType.LATENCY_DEGRADATION
                    elif 'memory' in metric_name.lower():
                        anomaly_type = AnomalyType.MEMORY_SPIKE
                    elif 'error' in metric_name.lower():
                        anomaly_type = AnomalyType.ERROR_RATE_INCREASE
                    else:
                        anomaly_type = AnomalyType.PERFORMANCE_SPIKE
                else:
                    if 'success' in metric_name.lower() or 'rate' in metric_name.lower():
                        anomaly_type = AnomalyType.SUCCESS_RATE_DROP
                    else:
                        anomaly_type = AnomalyType.UNUSUAL_PATTERN
                
                anomaly = Anomaly(
                    anomaly_id=f"anomaly_{metric_name}_{timestamp.strftime('%Y%m%d%H%M%S')}",
                    anomaly_type=anomaly_type,
                    description=f"{metric_name} deviated {abs(deviation_percent):.1f}% from baseline",
                    severity=min(z_score / 5.0, 1.0),  # Normalize to 0-1
                    detected_at=timestamp,
                    metric_name=metric_name,
                    expected_value=mean,
                    actual_value=value,
                    deviation_percent=deviation_percent,
                    affected_components=[component] if component else [],
                    context={
                        'z_score': z_score,
                        'baseline_mean': mean,
                        'baseline_std': std
                    }
                )
                anomalies.append(anomaly)
                self._detected_anomalies.append(anomaly)
        
        return anomalies
    
    def get_baseline(self, metric_name: str) -> Optional[Dict[str, float]]:
        """Get baseline statistics for a metric."""
        return self._baselines.get(metric_name)
    
    def get_all_anomalies(self, since: Optional[datetime] = None) -> List[Anomaly]:
        """Get all detected anomalies, optionally filtered by time."""
        if since:
            return [a for a in self._detected_anomalies if a.detected_at >= since]
        return self._detected_anomalies.copy()
    
    def mark_resolved(self, anomaly_id: str) -> bool:
        """Mark an anomaly as resolved."""
        for anomaly in self._detected_anomalies:
            if anomaly.anomaly_id == anomaly_id:
                anomaly.is_resolved = True
                anomaly.resolved_at = datetime.now()
                return True
        return False


class TrendAnalyzer:
    """
    Analyzes trends in time series data using linear regression
    and moving averages.
    """
    
    def __init__(self, min_data_points: int = 5):
        self.min_data_points = min_data_points
        self._trend_history: Dict[str, List[TrendAnalysis]] = defaultdict(list)
    
    def analyze_trend(
        self,
        metric_name: str,
        values: List[Tuple[datetime, float]],
        time_range_label: str = "7d"
    ) -> Optional[TrendAnalysis]:
        """
        Analyze trend in a time series.
        
        Args:
            metric_name: Name of the metric
            values: List of (timestamp, value) tuples
            time_range_label: Label for the time range (e.g., "7d", "30d")
            
        Returns:
            TrendAnalysis object or None if insufficient data
        """
        if len(values) < self.min_data_points:
            return None
        
        # Sort by timestamp
        sorted_values = sorted(values, key=lambda x: x[0])
        
        # Convert timestamps to numeric values (seconds from first timestamp)
        base_time = sorted_values[0][0]
        x_values = [(v[0] - base_time).total_seconds() for v in sorted_values]
        y_values = [v[1] for v in sorted_values]
        
        # Calculate linear regression
        slope, intercept, r_squared = self._linear_regression(x_values, y_values)
        
        # Determine trend direction
        if r_squared < 0.3:
            direction = TrendDirection.VOLATILE
        elif abs(slope) < 0.001:
            direction = TrendDirection.STABLE
        elif slope > 0:
            # For metrics like latency/errors, increasing is bad
            if 'latency' in metric_name.lower() or 'error' in metric_name.lower():
                direction = TrendDirection.DEGRADING
            else:
                direction = TrendDirection.IMPROVING
        else:
            # For metrics like latency/errors, decreasing is good
            if 'latency' in metric_name.lower() or 'error' in metric_name.lower():
                direction = TrendDirection.IMPROVING
            else:
                direction = TrendDirection.DEGRADING
        
        # Forecast next period
        next_x = x_values[-1] + (x_values[-1] - x_values[0]) / len(x_values)
        forecast_value = slope * next_x + intercept
        
        # Calculate forecast confidence based on R-squared
        forecast_confidence = min(r_squared * 0.8 + 0.2, 1.0)
        
        # Detect change points using simple derivative analysis
        change_points = self._detect_change_points(sorted_values)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            metric_name, direction, slope, r_squared
        )
        
        # Detect seasonal patterns (simplified)
        seasonal_pattern = self._detect_seasonality(y_values)
        
        analysis = TrendAnalysis(
            analysis_id=f"trend_{metric_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            metric_name=metric_name,
            time_range=time_range_label,
            direction=direction,
            slope=slope,
            r_squared=r_squared,
            data_points=len(values),
            forecast_next_period=forecast_value,
            forecast_confidence=forecast_confidence,
            seasonal_pattern=seasonal_pattern,
            change_points=change_points,
            recommendations=recommendations
        )
        
        self._trend_history[metric_name].append(analysis)
        
        return analysis
    
    def _linear_regression(self, x: List[float], y: List[float]) -> Tuple[float, float, float]:
        """
        Calculate simple linear regression.
        
        Returns:
            (slope, intercept, r_squared)
        """
        n = len(x)
        if n < 2:
            return 0.0, 0.0, 0.0
        
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi ** 2 for xi in x)
        sum_y2 = sum(yi ** 2 for yi in y)
        
        # Calculate slope and intercept
        denominator = n * sum_x2 - sum_x ** 2
        if denominator == 0:
            return 0.0, statistics.mean(y), 0.0
        
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        intercept = (sum_y - slope * sum_x) / n
        
        # Calculate R-squared
        y_mean = sum_y / n
        ss_tot = sum((yi - y_mean) ** 2 for yi in y)
        ss_res = sum((yi - (slope * xi + intercept)) ** 2 for xi, yi in zip(x, y))
        
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        r_squared = max(0.0, min(1.0, r_squared))  # Clamp to [0, 1]
        
        return slope, intercept, r_squared
    
    def _detect_change_points(
        self,
        values: List[Tuple[datetime, float]]
    ) -> List[datetime]:
        """Detect significant change points in the time series."""
        if len(values) < 5:
            return []
        
        measurements = [v[1] for v in values]
        change_points = []
        
        # Use rolling window to detect significant changes
        window_size = max(3, len(measurements) // 5)
        
        for i in range(window_size, len(measurements) - window_size):
            before = measurements[i - window_size:i]
            after = measurements[i:i + window_size]
            
            before_mean = statistics.mean(before)
            after_mean = statistics.mean(after)
            before_std = statistics.stdev(before) if len(before) > 1 else 0.0
            
            # Significant change if difference > 2 standard deviations
            if before_std > 0 and abs(after_mean - before_mean) > 2 * before_std:
                change_points.append(values[i][0])
        
        return change_points
    
    def _detect_seasonality(self, values: List[float]) -> Optional[str]:
        """Detect simple seasonal patterns."""
        if len(values) < 14:
            return None
        
        # Check for weekly pattern (7-day period)
        if len(values) >= 14:
            first_week = values[:7]
            second_week = values[7:14]
            correlation = self._calculate_correlation(first_week, second_week)
            
            if correlation > 0.7:
                return "weekly"
        
        return None
    
    def _calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient."""
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        
        n = len(x)
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        
        numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
        denominator_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x))
        denominator_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y))
        
        if denominator_x == 0 or denominator_y == 0:
            return 0.0
        
        return numerator / (denominator_x * denominator_y)
    
    def _generate_recommendations(
        self,
        metric_name: str,
        direction: TrendDirection,
        slope: float,
        r_squared: float
    ) -> List[str]:
        """Generate recommendations based on trend analysis."""
        recommendations = []
        
        if direction == TrendDirection.DEGRADING:
            recommendations.append(f"Investigate recent changes affecting {metric_name}")
            if 'latency' in metric_name.lower():
                recommendations.append("Consider performance optimization or caching")
            elif 'error' in metric_name.lower():
                recommendations.append("Review error handling and add monitoring")
            elif 'memory' in metric_name.lower():
                recommendations.append("Check for memory leaks and optimize allocation")
        
        if direction == TrendDirection.VOLATILE:
            recommendations.append("High variability detected - investigate inconsistent behavior")
            recommendations.append("Consider adding circuit breakers or rate limiting")
        
        if r_squared < 0.3:
            recommendations.append("Low trend correlation - monitor for more data")
        
        return recommendations
    
    def get_trend_history(self, metric_name: str) -> List[TrendAnalysis]:
        """Get historical trend analyses for a metric."""
        return self._trend_history.get(metric_name, [])


class CodeEmbeddings:
    """
    Lightweight code similarity analysis using token-based features.
    
    This is a simplified implementation that works without ML libraries,
    using lexical and structural similarity measures.
    """
    
    def __init__(self):
        self._code_signatures: Dict[str, Dict[str, Any]] = {}
    
    def compute_signature(self, code_id: str, code: str) -> Dict[str, Any]:
        """
        Compute a signature for a code snippet.
        
        Args:
            code_id: Unique identifier for the code
            code: The code string
            
        Returns:
            Signature dictionary
        """
        # Tokenize the code
        tokens = re.findall(r'\w+', code.lower())
        
        # Count different types of elements
        signature = {
            'token_count': len(tokens),
            'unique_tokens': len(set(tokens)),
            'line_count': code.count('\n') + 1,
            'token_freq': dict(Counter(tokens).most_common(20)),
            'has_class': 'class' in tokens,
            'has_function': 'def' in tokens or 'function' in tokens,
            'has_loop': 'for' in tokens or 'while' in tokens,
            'has_conditional': 'if' in tokens or 'else' in tokens,
            'has_try_except': 'try' in tokens or 'except' in tokens or 'catch' in tokens,
            'indentation_levels': self._count_indentation_levels(code),
            'code_hash': hashlib.md5(code.encode()).hexdigest()
        }
        
        self._code_signatures[code_id] = signature
        return signature
    
    def _count_indentation_levels(self, code: str) -> int:
        """Count the number of unique indentation levels."""
        indentations = set()
        for line in code.split('\n'):
            stripped = line.lstrip()
            if stripped:
                indent = len(line) - len(stripped)
                indentations.add(indent)
        return len(indentations)
    
    def compute_similarity(
        self,
        code_id1: str,
        code_id2: str,
        code1: Optional[str] = None,
        code2: Optional[str] = None
    ) -> CodeSimilarity:
        """
        Compute similarity between two code snippets.
        
        Args:
            code_id1: ID of first code snippet
            code_id2: ID of second code snippet
            code1: Optional code string (if not already computed)
            code2: Optional code string (if not already computed)
            
        Returns:
            CodeSimilarity object
        """
        # Get or compute signatures
        if code_id1 not in self._code_signatures and code1:
            self.compute_signature(code_id1, code1)
        if code_id2 not in self._code_signatures and code2:
            self.compute_signature(code_id2, code2)
        
        sig1 = self._code_signatures.get(code_id1, {})
        sig2 = self._code_signatures.get(code_id2, {})
        
        if not sig1 or not sig2:
            return CodeSimilarity(
                source_id=code_id1,
                target_id=code_id2,
                similarity_score=0.0,
                similarity_type="unknown"
            )
        
        # Calculate different similarity measures
        lexical_sim = self._lexical_similarity(sig1, sig2)
        structural_sim = self._structural_similarity(sig1, sig2)
        
        # Weighted combination
        combined_sim = lexical_sim * 0.6 + structural_sim * 0.4
        
        # Determine primary similarity type
        if lexical_sim > structural_sim:
            similarity_type = "lexical"
        else:
            similarity_type = "structural"
        
        # Find common patterns
        common_patterns = self._find_common_patterns(sig1, sig2)
        
        # Suggest refactoring if high similarity
        suggested_refactoring = None
        if combined_sim > 0.7:
            suggested_refactoring = "Consider extracting common functionality into a shared module"
        
        return CodeSimilarity(
            source_id=code_id1,
            target_id=code_id2,
            similarity_score=combined_sim,
            similarity_type=similarity_type,
            common_patterns=common_patterns,
            suggested_refactoring=suggested_refactoring
        )
    
    def _lexical_similarity(self, sig1: Dict[str, Any], sig2: Dict[str, Any]) -> float:
        """Calculate lexical similarity based on token overlap."""
        tokens1 = set(sig1.get('token_freq', {}).keys())
        tokens2 = set(sig2.get('token_freq', {}).keys())
        
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)
        
        return intersection / union if union > 0 else 0.0
    
    def _structural_similarity(self, sig1: Dict[str, Any], sig2: Dict[str, Any]) -> float:
        """Calculate structural similarity based on code structure."""
        structural_features = [
            'has_class', 'has_function', 'has_loop', 
            'has_conditional', 'has_try_except'
        ]
        
        matches = sum(
            1 for f in structural_features 
            if sig1.get(f) == sig2.get(f)
        )
        
        # Also consider line count similarity
        lines1 = sig1.get('line_count', 0)
        lines2 = sig2.get('line_count', 0)
        line_sim = 1 - abs(lines1 - lines2) / max(lines1, lines2, 1)
        
        return (matches / len(structural_features) + line_sim) / 2
    
    def _find_common_patterns(self, sig1: Dict[str, Any], sig2: Dict[str, Any]) -> List[str]:
        """Find common patterns between two signatures."""
        patterns = []
        
        if sig1.get('has_class') and sig2.get('has_class'):
            patterns.append("class definitions")
        if sig1.get('has_function') and sig2.get('has_function'):
            patterns.append("function definitions")
        if sig1.get('has_try_except') and sig2.get('has_try_except'):
            patterns.append("exception handling")
        if sig1.get('has_loop') and sig2.get('has_loop'):
            patterns.append("loop constructs")
        
        # Find common frequent tokens
        freq1 = sig1.get('token_freq', {})
        freq2 = sig2.get('token_freq', {})
        common_tokens = set(freq1.keys()) & set(freq2.keys())
        
        # Filter to meaningful tokens (not common keywords)
        keywords = {'def', 'class', 'if', 'else', 'for', 'while', 'return', 'import', 'from'}
        meaningful_common = [t for t in common_tokens if t not in keywords and len(t) > 3]
        
        if meaningful_common:
            patterns.append(f"common identifiers: {', '.join(meaningful_common[:3])}")
        
        return patterns
    
    def get_signature(self, code_id: str) -> Optional[Dict[str, Any]]:
        """Get computed signature for a code ID."""
        return self._code_signatures.get(code_id)


class IntelligentAnalyzer:
    """
    Main orchestrator for Phase 2 intelligent analysis.
    
    Combines:
    - Pattern clustering for error categorization
    - Anomaly detection for performance regressions
    - Trend analysis for forecasting
    - Code embeddings for semantic similarity
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern for global intelligent analysis."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the intelligent analyzer."""
        if self._initialized:
            return
        
        self._lock = threading.RLock()
        
        # Initialize components
        self.pattern_clusterer = PatternClusterer(similarity_threshold=0.6)
        self.anomaly_detector = AnomalyDetector(z_score_threshold=2.5)
        self.trend_analyzer = TrendAnalyzer(min_data_points=5)
        self.code_embeddings = CodeEmbeddings()
        
        # Analysis results
        self._analysis_results: List[Dict[str, Any]] = []
        
        # Subscribers
        self._anomaly_subscribers: List[callable] = []
        self._cluster_subscribers: List[callable] = []
        self._trend_subscribers: List[callable] = []
        
        self._initialized = True
        logger.info("IntelligentAnalyzer initialized")
    
    def run_full_analysis(self) -> Dict[str, Any]:
        """
        Run a complete intelligent analysis cycle.
        
        Returns:
            Dictionary with all analysis results
        """
        logger.info("Running full intelligent analysis...")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'clusters': [],
            'anomalies': [],
            'trends': [],
            'code_similarities': [],
            'summary': {}
        }
        
        try:
            # Get data from metrics analyzer
            from shared.circular_exchange import METRICS_ANALYZER
            
            # Cluster error patterns
            patterns = METRICS_ANALYZER.get_patterns()
            pattern_dicts = [p.to_dict() for p in patterns]
            clusters = self.pattern_clusterer.cluster_patterns(pattern_dicts)
            results['clusters'] = [c.to_dict() for c in clusters]
            
            # Notify cluster subscribers
            for cluster in clusters:
                self._notify_cluster_subscribers(cluster)
            
        except Exception as e:
            logger.warning("Could not perform pattern clustering: %s", e)
        
        try:
            # Detect anomalies in metrics
            from shared.circular_exchange import DATA_COLLECTOR
            
            # Get recent test results for anomaly detection
            since = datetime.now() - timedelta(hours=24)
            test_results = DATA_COLLECTOR.get_test_results(since=since, limit=1000)
            
            if test_results:
                # Aggregate by hour for latency analysis
                hourly_latencies: Dict[datetime, List[float]] = defaultdict(list)
                for tr in test_results:
                    hour = tr.timestamp.replace(minute=0, second=0, microsecond=0)
                    hourly_latencies[hour].append(tr.duration_ms)
                
                latency_values = [
                    (hour, statistics.mean(durations))
                    for hour, durations in sorted(hourly_latencies.items())
                ]
                
                anomalies = self.anomaly_detector.detect_anomalies(
                    "test_latency_ms",
                    latency_values,
                    "test_suite"
                )
                results['anomalies'] = [a.to_dict() for a in anomalies]
                
                # Notify anomaly subscribers
                for anomaly in anomalies:
                    self._notify_anomaly_subscribers(anomaly)
            
        except Exception as e:
            logger.warning("Could not perform anomaly detection: %s", e)
        
        try:
            # Analyze trends
            from shared.circular_exchange import DATA_COLLECTOR
            
            since = datetime.now() - timedelta(days=7)
            test_results = DATA_COLLECTOR.get_test_results(since=since, limit=5000)
            
            if test_results:
                # Pass rate trend
                daily_pass_rates: Dict[datetime, List[bool]] = defaultdict(list)
                for tr in test_results:
                    day = tr.timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
                    daily_pass_rates[day].append(tr.status.value == 'passed')
                
                pass_rate_values = [
                    (day, sum(results) / len(results) * 100)
                    for day, results in sorted(daily_pass_rates.items())
                ]
                
                if len(pass_rate_values) >= 5:
                    trend = self.trend_analyzer.analyze_trend(
                        "test_pass_rate",
                        pass_rate_values,
                        "7d"
                    )
                    if trend:
                        results['trends'].append(trend.to_dict())
                        self._notify_trend_subscribers(trend)
            
        except Exception as e:
            logger.warning("Could not perform trend analysis: %s", e)
        
        # Generate summary
        results['summary'] = {
            'clusters_found': len(results['clusters']),
            'anomalies_detected': len(results['anomalies']),
            'trends_analyzed': len(results['trends']),
            'high_severity_anomalies': len([a for a in results.get('anomalies', []) if a.get('severity', 0) > 0.7])
        }
        
        self._analysis_results.append(results)
        logger.info("Intelligent analysis complete: %s", results['summary'])
        
        return results
    
    # =========================================================================
    # SUBSCRIPTION MANAGEMENT
    # =========================================================================
    
    def subscribe_to_anomalies(self, callback: callable) -> None:
        """Subscribe to anomaly detection notifications."""
        with self._lock:
            if callback not in self._anomaly_subscribers:
                self._anomaly_subscribers.append(callback)
    
    def subscribe_to_clusters(self, callback: callable) -> None:
        """Subscribe to pattern cluster notifications."""
        with self._lock:
            if callback not in self._cluster_subscribers:
                self._cluster_subscribers.append(callback)
    
    def subscribe_to_trends(self, callback: callable) -> None:
        """Subscribe to trend analysis notifications."""
        with self._lock:
            if callback not in self._trend_subscribers:
                self._trend_subscribers.append(callback)
    
    def _notify_anomaly_subscribers(self, anomaly: Anomaly) -> None:
        """Notify all anomaly subscribers."""
        for callback in self._anomaly_subscribers:
            try:
                callback(anomaly)
            except Exception as e:
                logger.error("Error notifying anomaly subscriber: %s", e)
    
    def _notify_cluster_subscribers(self, cluster: PatternCluster) -> None:
        """Notify all cluster subscribers."""
        for callback in self._cluster_subscribers:
            try:
                callback(cluster)
            except Exception as e:
                logger.error("Error notifying cluster subscriber: %s", e)
    
    def _notify_trend_subscribers(self, trend: TrendAnalysis) -> None:
        """Notify all trend subscribers."""
        for callback in self._trend_subscribers:
            try:
                callback(trend)
            except Exception as e:
                logger.error("Error notifying trend subscriber: %s", e)
    
    # =========================================================================
    # QUERY METHODS
    # =========================================================================
    
    def get_analysis_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent analysis results."""
        return self._analysis_results[-limit:]
    
    def get_clusters(self) -> List[PatternCluster]:
        """Get all pattern clusters."""
        return list(self.pattern_clusterer._clusters.values())
    
    def get_anomalies(self, since: Optional[datetime] = None) -> List[Anomaly]:
        """Get detected anomalies."""
        return self.anomaly_detector.get_all_anomalies(since)
    
    def get_trends(self, metric_name: str) -> List[TrendAnalysis]:
        """Get trend analysis history for a metric."""
        return self.trend_analyzer.get_trend_history(metric_name)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of intelligent analysis capabilities."""
        return {
            'total_clusters': len(self.pattern_clusterer._clusters),
            'total_anomalies': len(self.anomaly_detector._detected_anomalies),
            'metrics_with_baselines': list(self.anomaly_detector._baselines.keys()),
            'metrics_with_trends': list(self.trend_analyzer._trend_history.keys()),
            'code_signatures': len(self.code_embeddings._code_signatures),
            'analysis_runs': len(self._analysis_results)
        }


# Global singleton instance
INTELLIGENT_ANALYZER = IntelligentAnalyzer()


# Circular Exchange Framework Integration
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    CIRCULAR_EXCHANGE_AVAILABLE = False

if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="shared.circular_exchange.intelligent_analyzer",
            file_path=__file__,
            description="ML-powered intelligent analysis for continuous improvement",
            dependencies=[
                "shared.circular_exchange.data_collector",
                "shared.circular_exchange.metrics_analyzer",
                "shared.circular_exchange.persistence"
            ],
            exports=[
                "IntelligentAnalyzer", "PatternCluster", "AnomalyDetector",
                "TrendAnalyzer", "CodeEmbeddings", "Anomaly", "TrendAnalysis",
                "CodeSimilarity", "AnomalyType", "TrendDirection", "ClusterQuality",
                "PatternClusterer", "INTELLIGENT_ANALYZER"
            ]
        ))
    except Exception:
        pass  # Ignore registration errors during import
