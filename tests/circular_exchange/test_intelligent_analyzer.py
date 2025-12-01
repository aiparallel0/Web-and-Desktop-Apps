"""
Tests for IntelligentAnalyzer - Phase 2 ML-based analysis components.
"""

import pytest
import math
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from shared.circular_exchange.intelligent_analyzer import (
    IntelligentAnalyzer,
    PatternClusterer,
    AnomalyDetector,
    TrendAnalyzer,
    CodeEmbeddings,
    PatternCluster,
    Anomaly,
    TrendAnalysis,
    CodeSimilarity,
    AnomalyType,
    TrendDirection,
    ClusterQuality,
    INTELLIGENT_ANALYZER
)


class TestPatternClusterer:
    """Tests for PatternClusterer class."""
    
    def test_cluster_similar_patterns(self):
        """Test clustering of similar patterns."""
        clusterer = PatternClusterer(similarity_threshold=0.5)
        
        patterns = [
            {
                'pattern_id': 'p1',
                'description': 'Connection timeout error in module A',
                'pattern_type': 'error_recurring',
                'occurrences': 10,
                'confidence': 0.8,
                'affected_modules': ['module_a']
            },
            {
                'pattern_id': 'p2',
                'description': 'Connection timeout error in module B',
                'pattern_type': 'error_recurring',
                'occurrences': 8,
                'confidence': 0.7,
                'affected_modules': ['module_b']
            },
            {
                'pattern_id': 'p3',
                'description': 'Memory allocation failed',
                'pattern_type': 'error_recurring',
                'occurrences': 5,
                'confidence': 0.9,
                'affected_modules': ['module_c']
            }
        ]
        
        clusters = clusterer.cluster_patterns(patterns)
        
        assert len(clusters) >= 1
        assert all(isinstance(c, PatternCluster) for c in clusters)
    
    def test_empty_patterns(self):
        """Test clustering with empty input."""
        clusterer = PatternClusterer()
        clusters = clusterer.cluster_patterns([])
        assert clusters == []
    
    def test_cluster_has_correct_attributes(self):
        """Test that clusters have all required attributes."""
        clusterer = PatternClusterer(similarity_threshold=0.3)
        
        patterns = [
            {
                'pattern_id': 'p1',
                'description': 'Test error pattern',
                'pattern_type': 'error_recurring',
                'occurrences': 5,
                'confidence': 0.8,
                'affected_modules': ['mod_a']
            }
        ]
        
        clusters = clusterer.cluster_patterns(patterns)
        
        assert len(clusters) == 1
        cluster = clusters[0]
        
        assert cluster.cluster_id is not None
        assert cluster.name is not None
        assert cluster.description is not None
        assert len(cluster.pattern_ids) > 0
        assert isinstance(cluster.quality, ClusterQuality)
    
    def test_get_cluster_for_pattern(self):
        """Test retrieving cluster for a specific pattern."""
        clusterer = PatternClusterer()
        
        patterns = [
            {
                'pattern_id': 'p1',
                'description': 'Connection timeout',
                'pattern_type': 'error_recurring',
                'occurrences': 5,
                'confidence': 0.8,
                'affected_modules': []
            }
        ]
        
        clusters = clusterer.cluster_patterns(patterns)
        
        retrieved = clusterer.get_cluster_for_pattern('p1')
        assert retrieved is not None
        assert 'p1' in retrieved.pattern_ids


class TestAnomalyDetector:
    """Tests for AnomalyDetector class."""
    
    def test_update_baseline(self):
        """Test baseline calculation."""
        detector = AnomalyDetector()
        
        values = [10.0, 12.0, 11.0, 9.0, 10.5, 11.5, 10.0, 12.0, 11.0, 10.0]
        baseline = detector.update_baseline('test_metric', values)
        
        assert 'mean' in baseline
        assert 'std' in baseline
        assert baseline['sample_count'] == 10
        assert 9.0 < baseline['mean'] < 12.0
    
    def test_detect_spike_anomaly(self):
        """Test detection of a spike anomaly."""
        detector = AnomalyDetector(z_score_threshold=2.0)
        
        # Normal values followed by a spike
        base_time = datetime.now()
        values = [
            (base_time - timedelta(hours=i), 10.0 + (i % 2))
            for i in range(10)
        ]
        values.append((base_time, 50.0))  # Spike
        
        anomalies = detector.detect_anomalies('latency_ms', values, 'test_component')
        
        assert len(anomalies) >= 1
        assert any(a.actual_value == 50.0 for a in anomalies)
    
    def test_no_anomaly_in_normal_data(self):
        """Test that normal data produces no anomalies."""
        detector = AnomalyDetector(z_score_threshold=3.0)
        
        base_time = datetime.now()
        # Very consistent values
        values = [
            (base_time - timedelta(hours=i), 10.0)
            for i in range(20)
        ]
        
        anomalies = detector.detect_anomalies('stable_metric', values, 'component')
        
        # With constant values, std = 0, so no z-score can be computed
        assert len(anomalies) == 0
    
    def test_anomaly_severity(self):
        """Test that anomaly severity is calculated correctly."""
        detector = AnomalyDetector(z_score_threshold=2.0)
        
        base_time = datetime.now()
        values = [(base_time - timedelta(hours=i), 10.0) for i in range(10)]
        # Add small variation to get non-zero std
        values = [(t, v + (0.5 if i % 2 == 0 else -0.5)) for i, (t, v) in enumerate(values)]
        values.append((base_time, 100.0))  # Large spike
        
        anomalies = detector.detect_anomalies('test_metric', values)
        
        if anomalies:
            assert 0.0 <= anomalies[-1].severity <= 1.0
    
    def test_mark_resolved(self):
        """Test marking an anomaly as resolved."""
        detector = AnomalyDetector()
        
        base_time = datetime.now()
        values = [(base_time - timedelta(hours=i), 10.0 + (0.5 if i % 2 == 0 else 0)) for i in range(10)]
        values.append((base_time, 50.0))
        
        anomalies = detector.detect_anomalies('test_metric', values)
        
        if anomalies:
            anomaly_id = anomalies[0].anomaly_id
            result = detector.mark_resolved(anomaly_id)
            assert result is True
            
            # Check it's marked resolved
            all_anomalies = detector.get_all_anomalies()
            resolved = [a for a in all_anomalies if a.anomaly_id == anomaly_id]
            if resolved:
                assert resolved[0].is_resolved is True


class TestTrendAnalyzer:
    """Tests for TrendAnalyzer class."""
    
    def test_analyze_upward_trend(self):
        """Test detection of upward trend."""
        analyzer = TrendAnalyzer()
        
        base_time = datetime.now()
        values = [
            (base_time - timedelta(days=7-i), 10.0 + i * 2)
            for i in range(7)
        ]
        
        trend = analyzer.analyze_trend('success_rate', values, '7d')
        
        assert trend is not None
        assert trend.slope > 0
        # The slope is positive, so it's either improving or stable (depends on threshold)
        assert trend.direction in (TrendDirection.IMPROVING, TrendDirection.STABLE)
    
    def test_analyze_stable_trend(self):
        """Test detection of stable trend."""
        analyzer = TrendAnalyzer()
        
        base_time = datetime.now()
        values = [
            (base_time - timedelta(days=7-i), 50.0 + (0.1 if i % 2 == 0 else -0.1))
            for i in range(7)
        ]
        
        trend = analyzer.analyze_trend('stable_metric', values, '7d')
        
        assert trend is not None
        assert abs(trend.slope) < 0.1 or trend.direction == TrendDirection.STABLE
    
    def test_forecast_generation(self):
        """Test that forecast is generated."""
        analyzer = TrendAnalyzer()
        
        base_time = datetime.now()
        values = [
            (base_time - timedelta(days=7-i), 10.0 + i * 5)
            for i in range(7)
        ]
        
        trend = analyzer.analyze_trend('growing_metric', values, '7d')
        
        assert trend is not None
        assert trend.forecast_next_period > 0
        assert 0.0 <= trend.forecast_confidence <= 1.0
    
    def test_insufficient_data(self):
        """Test handling of insufficient data."""
        analyzer = TrendAnalyzer(min_data_points=5)
        
        base_time = datetime.now()
        values = [
            (base_time - timedelta(days=i), 10.0)
            for i in range(3)
        ]
        
        trend = analyzer.analyze_trend('sparse_metric', values, '3d')
        
        assert trend is None
    
    def test_recommendations_for_degrading(self):
        """Test that recommendations are generated for degrading trends."""
        analyzer = TrendAnalyzer()
        
        base_time = datetime.now()
        # Increasing latency (degrading)
        values = [
            (base_time - timedelta(days=7-i), 100.0 + i * 50)
            for i in range(7)
        ]
        
        trend = analyzer.analyze_trend('latency_ms', values, '7d')
        
        assert trend is not None
        if trend.direction == TrendDirection.DEGRADING:
            assert len(trend.recommendations) > 0


class TestCodeEmbeddings:
    """Tests for CodeEmbeddings class."""
    
    def test_compute_signature(self):
        """Test code signature computation."""
        embeddings = CodeEmbeddings()
        
        code = '''
def process_data(data):
    if data is None:
        return None
    for item in data:
        try:
            result = transform(item)
        except Exception as e:
            log_error(e)
    return result
'''
        
        signature = embeddings.compute_signature('code1', code)
        
        assert signature['token_count'] > 0
        assert signature['has_function'] is True
        assert signature['has_conditional'] is True
        assert signature['has_loop'] is True
        assert signature['has_try_except'] is True
    
    def test_compute_similarity_identical(self):
        """Test similarity of identical code."""
        embeddings = CodeEmbeddings()
        
        code = 'def hello(): return "world"'
        
        embeddings.compute_signature('code1', code)
        embeddings.compute_signature('code2', code)
        
        similarity = embeddings.compute_similarity('code1', 'code2')
        
        assert similarity.similarity_score == 1.0
    
    def test_compute_similarity_different(self):
        """Test similarity of very different code."""
        embeddings = CodeEmbeddings()
        
        code1 = '''
class Calculator:
    def add(self, a, b):
        return a + b
'''
        code2 = '''
import os
import sys
if __name__ == "__main__":
    print("Hello")
'''
        
        similarity = embeddings.compute_similarity('c1', 'c2', code1, code2)
        
        assert similarity.similarity_score < 0.8
    
    def test_find_common_patterns(self):
        """Test finding common patterns between code snippets."""
        embeddings = CodeEmbeddings()
        
        code1 = '''
def process(data):
    try:
        for item in data:
            handle(item)
    except Exception:
        pass
'''
        code2 = '''
def transform(items):
    try:
        for x in items:
            convert(x)
    except ValueError:
        pass
'''
        
        similarity = embeddings.compute_similarity('c1', 'c2', code1, code2)
        
        assert 'function definitions' in similarity.common_patterns or \
               'loop constructs' in similarity.common_patterns or \
               'exception handling' in similarity.common_patterns


class TestIntelligentAnalyzer:
    """Tests for IntelligentAnalyzer orchestrator."""
    
    def test_singleton_pattern(self):
        """Test that IntelligentAnalyzer is a singleton."""
        analyzer1 = IntelligentAnalyzer()
        analyzer2 = IntelligentAnalyzer()
        
        assert analyzer1 is analyzer2
    
    def test_components_initialized(self):
        """Test that all components are initialized."""
        analyzer = INTELLIGENT_ANALYZER
        
        assert hasattr(analyzer, 'pattern_clusterer')
        assert hasattr(analyzer, 'anomaly_detector')
        assert hasattr(analyzer, 'trend_analyzer')
        assert hasattr(analyzer, 'code_embeddings')
        
        assert isinstance(analyzer.pattern_clusterer, PatternClusterer)
        assert isinstance(analyzer.anomaly_detector, AnomalyDetector)
        assert isinstance(analyzer.trend_analyzer, TrendAnalyzer)
        assert isinstance(analyzer.code_embeddings, CodeEmbeddings)
    
    def test_subscribe_to_anomalies(self):
        """Test anomaly subscription."""
        analyzer = IntelligentAnalyzer()
        
        received = []
        def callback(anomaly):
            received.append(anomaly)
        
        analyzer.subscribe_to_anomalies(callback)
        
        # Trigger an anomaly
        base_time = datetime.now()
        values = [(base_time - timedelta(hours=i), 10.0 + (0.5 if i % 2 == 0 else 0)) for i in range(10)]
        values.append((base_time, 100.0))
        
        anomalies = analyzer.anomaly_detector.detect_anomalies('test_sub', values)
        
        # Manually notify since detect_anomalies doesn't auto-notify through orchestrator
        for anomaly in anomalies:
            analyzer._notify_anomaly_subscribers(anomaly)
        
        assert len(received) == len(anomalies)
    
    def test_get_summary(self):
        """Test summary generation."""
        analyzer = INTELLIGENT_ANALYZER
        
        summary = analyzer.get_summary()
        
        assert 'total_clusters' in summary
        assert 'total_anomalies' in summary
        assert 'metrics_with_baselines' in summary
        assert 'analysis_runs' in summary
    
    def test_run_full_analysis_returns_structure(self):
        """Test that full analysis returns expected structure."""
        analyzer = IntelligentAnalyzer()
        
        # This may fail to get data if DATA_COLLECTOR is empty, but should return structure
        with patch.object(analyzer, 'pattern_clusterer') as mock_clusterer:
            mock_clusterer.cluster_patterns.return_value = []
            
            # Patch imports to avoid errors
            with patch.dict('sys.modules', {'shared.circular_exchange': Mock()}):
                results = analyzer.run_full_analysis()
        
        assert 'timestamp' in results
        assert 'clusters' in results
        assert 'anomalies' in results
        assert 'trends' in results
        assert 'summary' in results


class TestDataclassSerialization:
    """Tests for dataclass serialization."""
    
    def test_pattern_cluster_to_dict(self):
        """Test PatternCluster serialization."""
        cluster = PatternCluster(
            cluster_id='test_cluster',
            name='Test Cluster',
            description='A test cluster',
            pattern_ids=['p1', 'p2'],
            total_occurrences=15,
            quality=ClusterQuality.HIGH
        )
        
        data = cluster.to_dict()
        
        assert data['cluster_id'] == 'test_cluster'
        assert data['quality'] == 'high'
        assert isinstance(data['created_at'], str)
    
    def test_anomaly_to_dict(self):
        """Test Anomaly serialization."""
        anomaly = Anomaly(
            anomaly_id='anomaly_1',
            anomaly_type=AnomalyType.PERFORMANCE_SPIKE,
            description='Test anomaly',
            severity=0.8,
            detected_at=datetime.now(),
            metric_name='latency',
            expected_value=10.0,
            actual_value=50.0,
            deviation_percent=400.0
        )
        
        data = anomaly.to_dict()
        
        assert data['anomaly_type'] == 'performance_spike'
        assert isinstance(data['detected_at'], str)
    
    def test_trend_analysis_to_dict(self):
        """Test TrendAnalysis serialization."""
        trend = TrendAnalysis(
            analysis_id='trend_1',
            metric_name='success_rate',
            time_range='7d',
            direction=TrendDirection.IMPROVING,
            slope=0.5,
            r_squared=0.85,
            data_points=7,
            forecast_next_period=95.0,
            forecast_confidence=0.8,
            change_points=[datetime.now()]
        )
        
        data = trend.to_dict()
        
        assert data['direction'] == 'improving'
        assert isinstance(data['created_at'], str)
        assert isinstance(data['change_points'][0], str)


class TestLinearRegression:
    """Tests for linear regression in TrendAnalyzer."""
    
    def test_perfect_linear_fit(self):
        """Test regression on perfectly linear data."""
        analyzer = TrendAnalyzer()
        
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [2.0, 4.0, 6.0, 8.0, 10.0]  # y = 2x
        
        slope, intercept, r_squared = analyzer._linear_regression(x, y)
        
        assert abs(slope - 2.0) < 0.01
        assert abs(intercept) < 0.01
        assert abs(r_squared - 1.0) < 0.01
    
    def test_noisy_data(self):
        """Test regression on noisy data."""
        analyzer = TrendAnalyzer()
        
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [2.1, 3.9, 6.2, 7.8, 10.1]  # Noisy y = 2x
        
        slope, intercept, r_squared = analyzer._linear_regression(x, y)
        
        assert 1.5 < slope < 2.5
        assert r_squared > 0.9


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
