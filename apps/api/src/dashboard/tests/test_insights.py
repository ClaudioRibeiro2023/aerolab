"""
Tests for Insights Module
"""

import pytest
from datetime import datetime, timedelta
from ..insights.anomalies import AnomalyDetector, AnomalyType, AnomalySeverity
from ..insights.forecasting import Forecaster, Forecast
from ..insights.recommendations import RecommendationEngine, RecommendationType
from ..insights.summaries import InsightSummarizer


class TestAnomalyDetector:
    """Tests for AnomalyDetector."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.detector = AnomalyDetector(sensitivity=0.5)
    
    def test_detect_spike_zscore(self):
        """Test detecting spike with Z-score."""
        # Normal values with one spike
        values = [100, 102, 98, 101, 99, 100, 500, 101, 99, 100]
        
        anomalies = self.detector.detect_zscore(
            values,
            metric_name="test_metric"
        )
        
        assert len(anomalies) >= 1
        spike = [a for a in anomalies if a.type == AnomalyType.SPIKE]
        assert len(spike) >= 1
    
    def test_detect_drop_zscore(self):
        """Test detecting drop with Z-score."""
        # Normal values with one drop
        values = [100, 102, 98, 101, 99, 100, 10, 101, 99, 100]
        
        anomalies = self.detector.detect_zscore(
            values,
            metric_name="test_metric"
        )
        
        assert len(anomalies) >= 1
        drops = [a for a in anomalies if a.type == AnomalyType.DROP]
        assert len(drops) >= 1
    
    def test_detect_iqr(self):
        """Test IQR detection."""
        values = [10, 12, 11, 10, 13, 11, 100, 12, 10, 11]
        
        anomalies = self.detector.detect_iqr(
            values,
            metric_name="test_metric"
        )
        
        assert len(anomalies) >= 1
    
    def test_detect_moving_average(self):
        """Test moving average detection."""
        values = [10] * 10 + [100] + [10] * 10
        
        anomalies = self.detector.detect_moving_average(
            values,
            window_size=5,
            metric_name="test_metric"
        )
        
        assert len(anomalies) >= 1
    
    def test_detect_trend_change(self):
        """Test trend change detection."""
        # Rising then falling
        values = list(range(0, 20)) + list(range(20, 0, -1))
        
        anomalies = self.detector.detect_trend_change(
            values,
            window_size=5,
            metric_name="test_metric"
        )
        
        trend_changes = [a for a in anomalies if a.type == AnomalyType.TREND_CHANGE]
        assert len(trend_changes) >= 1
    
    def test_no_anomalies_stable_data(self):
        """Test no anomalies in stable data."""
        values = [100 + (i % 3) for i in range(50)]  # Very stable
        
        anomalies = self.detector.detect_zscore(
            values,
            metric_name="test_metric"
        )
        
        assert len(anomalies) == 0
    
    def test_severity_calculation(self):
        """Test severity is calculated correctly."""
        # Create obvious anomaly
        values = [10] * 20 + [1000] + [10] * 20
        
        anomalies = self.detector.detect_zscore(
            values,
            metric_name="test_metric"
        )
        
        if anomalies:
            # High deviation should result in high severity
            assert anomalies[0].severity in [
                AnomalySeverity.HIGH,
                AnomalySeverity.CRITICAL
            ]


class TestForecaster:
    """Tests for Forecaster."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.forecaster = Forecaster()
    
    def test_linear_regression(self):
        """Test linear regression forecasting."""
        # Linear trend
        values = [10 + i * 2 for i in range(20)]
        
        forecast = self.forecaster.linear_regression(
            values,
            forecast_periods=5,
            metric_name="test"
        )
        
        assert len(forecast.points) == 5
        assert forecast.trend == "up"
    
    def test_exponential_smoothing(self):
        """Test exponential smoothing."""
        values = [100, 102, 98, 101, 99, 100, 103, 97, 100, 101]
        
        forecast = self.forecaster.exponential_smoothing(
            values,
            forecast_periods=5,
            metric_name="test"
        )
        
        assert len(forecast.points) == 5
        assert forecast.method == "exponential_smoothing"
    
    def test_holt_linear(self):
        """Test Holt's linear method."""
        values = [10 + i * 3 + (i % 3) for i in range(20)]
        
        forecast = self.forecaster.holt_linear(
            values,
            forecast_periods=5,
            metric_name="test"
        )
        
        assert len(forecast.points) == 5
    
    def test_auto_forecast(self):
        """Test auto forecast selection."""
        values = [10 + i for i in range(30)]
        
        forecast = self.forecaster.auto_forecast(
            values,
            forecast_periods=5,
            metric_name="test"
        )
        
        assert forecast is not None
        assert len(forecast.points) == 5
    
    def test_forecast_has_confidence_bounds(self):
        """Test forecast includes confidence bounds."""
        values = [100 + i for i in range(20)]
        
        forecast = self.forecaster.linear_regression(
            values,
            forecast_periods=3,
            metric_name="test"
        )
        
        for point in forecast.points:
            assert point.lower_bound <= point.value
            assert point.upper_bound >= point.value
    
    def test_evaluate_forecast(self):
        """Test forecast evaluation metrics."""
        actual = [100, 102, 98, 105, 103]
        predicted = [101, 100, 99, 104, 102]
        
        metrics = self.forecaster.evaluate_forecast(actual, predicted)
        
        assert "mape" in metrics
        assert "rmse" in metrics
        assert "mae" in metrics
        assert metrics["mape"] >= 0


class TestRecommendationEngine:
    """Tests for RecommendationEngine."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.engine = RecommendationEngine()
    
    def test_analyze_high_cost(self):
        """Test recommendation for high cost."""
        metrics = {
            "avg_cost_per_request": 0.10,  # High cost
            "total_requests": 1000
        }
        
        recommendations = self.engine.analyze(metrics)
        
        cost_recs = [r for r in recommendations if r.type == RecommendationType.COST_SAVING]
        assert len(cost_recs) > 0
    
    def test_analyze_high_latency(self):
        """Test recommendation for high latency."""
        metrics = {
            "p95_latency_ms": 6000,  # 6 seconds
        }
        
        recommendations = self.engine.analyze(metrics)
        
        perf_recs = [r for r in recommendations if r.type == RecommendationType.OPTIMIZATION]
        assert len(perf_recs) > 0
    
    def test_analyze_high_error_rate(self):
        """Test recommendation for high error rate."""
        metrics = {
            "error_rate": 0.10,  # 10% errors
        }
        
        recommendations = self.engine.analyze(metrics)
        
        rel_recs = [r for r in recommendations if r.type == RecommendationType.RELIABILITY]
        assert len(rel_recs) > 0
    
    def test_dismiss_recommendation(self):
        """Test dismissing recommendation."""
        metrics = {"avg_cost_per_request": 0.10}
        recommendations = self.engine.analyze(metrics)
        
        if recommendations:
            rec_id = recommendations[0].id
            result = self.engine.dismiss(rec_id)
            
            assert result is True
            assert self.engine.get_recommendation(rec_id).dismissed is True
    
    def test_mark_implemented(self):
        """Test marking recommendation as implemented."""
        metrics = {"error_rate": 0.10}
        recommendations = self.engine.analyze(metrics)
        
        if recommendations:
            rec_id = recommendations[0].id
            self.engine.mark_implemented(rec_id)
            
            assert self.engine.get_recommendation(rec_id).implemented is True
    
    def test_get_active_recommendations(self):
        """Test getting active recommendations only."""
        metrics = {"avg_cost_per_request": 0.10, "error_rate": 0.10}
        self.engine.analyze(metrics)
        
        # Dismiss one
        recs = self.engine.get_active_recommendations()
        if recs:
            self.engine.dismiss(recs[0].id)
        
        active = self.engine.get_active_recommendations()
        dismissed = [r for r in self.engine._recommendations.values() if r.dismissed]
        
        assert len(active) == len(self.engine._recommendations) - len(dismissed)


class TestInsightSummarizer:
    """Tests for InsightSummarizer."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.summarizer = InsightSummarizer()
    
    def test_generate_summary(self):
        """Test generating summary."""
        metrics = {
            "total_requests": 10000,
            "success_rate": 0.95,
            "avg_latency_ms": 200,
            "p95_latency_ms": 500,
            "total_cost_usd": 150.00,
            "error_rate": 0.05,
        }
        
        summary = self.summarizer.generate_summary(metrics, "week")
        
        assert summary.headline != ""
        assert summary.summary != ""
        assert len(summary.key_metrics) > 0
    
    def test_summary_with_comparison(self):
        """Test summary with period comparison."""
        current = {
            "total_requests": 12000,
            "success_rate": 0.96,
            "avg_latency_ms": 180,
            "total_cost_usd": 160.00,
        }
        
        previous = {
            "total_requests": 10000,
            "success_rate": 0.94,
            "avg_latency_ms": 200,
            "total_cost_usd": 150.00,
        }
        
        summary = self.summarizer.generate_summary(
            current, "week", previous
        )
        
        # Should have change data
        metrics_with_change = [m for m in summary.key_metrics if "change" in m]
        assert len(metrics_with_change) > 0
    
    def test_highlights_generated(self):
        """Test highlights are generated."""
        metrics = {
            "total_requests": 50000,
            "success_rate": 0.99,  # Excellent
            "p95_latency_ms": 300,  # Good
        }
        
        summary = self.summarizer.generate_summary(metrics, "day")
        
        assert len(summary.highlights) > 0
    
    def test_concerns_generated(self):
        """Test concerns are generated for poor metrics."""
        metrics = {
            "total_requests": 10000,
            "success_rate": 0.85,  # Poor
            "error_rate": 0.15,  # High
            "p95_latency_ms": 8000,  # Very slow
        }
        
        summary = self.summarizer.generate_summary(metrics, "day")
        
        assert len(summary.concerns) > 0
    
    def test_daily_digest(self):
        """Test daily digest generation."""
        metrics = {
            "total_requests": 10000,
            "success_rate": 0.95,
            "total_cost_usd": 100.00,
        }
        
        digest = self.summarizer.generate_daily_digest(metrics)
        
        assert "# Daily Dashboard Digest" in digest
        assert "Overview" in digest


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
