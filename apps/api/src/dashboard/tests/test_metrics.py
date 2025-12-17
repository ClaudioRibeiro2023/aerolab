"""
Tests for Metrics Module
"""

import pytest
from datetime import datetime, timedelta
from ..metrics.collector import MetricCollector, MetricType, Metric
from ..metrics.aggregator import TimeSeriesAggregator, AggregationFunction
from ..metrics.storage import MetricStorage
from ..metrics.queries import QueryEngine, QueryParser


class TestMetricCollector:
    """Tests for MetricCollector."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.collector = MetricCollector()
    
    def test_register_metric(self):
        """Test metric registration."""
        metric = self.collector.register(
            name="test_requests_total",
            metric_type=MetricType.COUNTER,
            description="Test counter",
            labels=["method", "status"]
        )
        
        assert metric.name == "test_requests_total"
        assert metric.type == MetricType.COUNTER
        assert "method" in metric.labels
    
    def test_record_counter(self):
        """Test recording counter values."""
        self.collector.register(
            name="requests_total",
            metric_type=MetricType.COUNTER
        )
        
        self.collector.record("requests_total", 1)
        self.collector.record("requests_total", 5)
        
        metric = self.collector.get_metric("requests_total")
        assert metric is not None
        assert len(metric.points) == 2
    
    def test_increment_counter(self):
        """Test incrementing counter."""
        self.collector.register(
            name="errors_total",
            metric_type=MetricType.COUNTER
        )
        
        self.collector.increment("errors_total")
        self.collector.increment("errors_total", 5)
        
        metric = self.collector.get_metric("errors_total")
        points = metric.points
        assert points[-1].value == 5
    
    def test_gauge_metric(self):
        """Test gauge metric."""
        self.collector.register(
            name="temperature",
            metric_type=MetricType.GAUGE
        )
        
        self.collector.record("temperature", 25.5)
        self.collector.record("temperature", 26.0)
        
        metric = self.collector.get_metric("temperature")
        assert metric.points[-1].value == 26.0
    
    def test_histogram_metric(self):
        """Test histogram metric."""
        self.collector.register(
            name="latency",
            metric_type=MetricType.HISTOGRAM,
            buckets=[0.1, 0.5, 1.0, 5.0]
        )
        
        self.collector.record("latency", 0.3)
        self.collector.record("latency", 0.7)
        self.collector.record("latency", 2.0)
        
        metric = self.collector.get_metric("latency")
        assert len(metric.points) == 3
    
    def test_export_prometheus(self):
        """Test Prometheus format export."""
        self.collector.register(
            name="http_requests",
            metric_type=MetricType.COUNTER,
            description="HTTP requests"
        )
        self.collector.record("http_requests", 100)
        
        output = self.collector.export_prometheus()
        
        assert "# HELP http_requests HTTP requests" in output
        assert "# TYPE http_requests counter" in output
        assert "http_requests" in output


class TestTimeSeriesAggregator:
    """Tests for TimeSeriesAggregator."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.aggregator = TimeSeriesAggregator()
    
    def test_aggregate_sum(self):
        """Test sum aggregation."""
        points = [
            {"timestamp": datetime.now() - timedelta(minutes=i), "value": 10}
            for i in range(10)
        ]
        
        result = self.aggregator.aggregate(
            points,
            AggregationFunction.SUM,
            "5m"
        )
        
        assert len(result) > 0
        assert sum(p["value"] for p in result) == 100
    
    def test_aggregate_avg(self):
        """Test average aggregation."""
        base_time = datetime.now()
        points = [
            {"timestamp": base_time - timedelta(minutes=i), "value": i * 10}
            for i in range(6)
        ]
        
        result = self.aggregator.aggregate(
            points,
            AggregationFunction.AVG,
            "10m"
        )
        
        assert len(result) > 0
    
    def test_aggregate_max(self):
        """Test max aggregation."""
        base_time = datetime.now()
        points = [
            {"timestamp": base_time - timedelta(minutes=i), "value": i * 10}
            for i in range(5)
        ]
        
        result = self.aggregator.aggregate(
            points,
            AggregationFunction.MAX,
            "1h"
        )
        
        assert result[0]["value"] == 40
    
    def test_downsample(self):
        """Test downsampling."""
        points = [
            {"timestamp": datetime.now() - timedelta(seconds=i), "value": i}
            for i in range(100)
        ]
        
        result = self.aggregator.downsample(
            points,
            target_points=10,
            function=AggregationFunction.AVG
        )
        
        assert len(result) <= 10


class TestMetricStorage:
    """Tests for MetricStorage."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.storage = MetricStorage()
    
    def test_write_and_read(self):
        """Test writing and reading points."""
        now = datetime.now()
        
        self.storage.write(
            metric="cpu_usage",
            value=45.5,
            timestamp=now,
            labels={"host": "server1"}
        )
        
        points = self.storage.read(
            metric="cpu_usage",
            start_time=now - timedelta(minutes=1),
            end_time=now + timedelta(minutes=1)
        )
        
        assert len(points) == 1
        assert points[0].value == 45.5
    
    def test_batch_write(self):
        """Test batch writing."""
        now = datetime.now()
        
        points = [
            {"metric": "requests", "value": i, "timestamp": now - timedelta(seconds=i)}
            for i in range(10)
        ]
        
        self.storage.write_batch(points)
        
        result = self.storage.read(
            metric="requests",
            start_time=now - timedelta(minutes=1),
            end_time=now + timedelta(minutes=1)
        )
        
        assert len(result) == 10
    
    def test_label_filtering(self):
        """Test filtering by labels."""
        now = datetime.now()
        
        self.storage.write("http_requests", 100, now, {"method": "GET", "status": "200"})
        self.storage.write("http_requests", 50, now, {"method": "POST", "status": "200"})
        self.storage.write("http_requests", 10, now, {"method": "GET", "status": "500"})
        
        points = self.storage.read(
            metric="http_requests",
            start_time=now - timedelta(minutes=1),
            end_time=now + timedelta(minutes=1),
            labels={"method": "GET"}
        )
        
        assert len(points) == 2


class TestQueryEngine:
    """Tests for QueryEngine."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.storage = MetricStorage()
        self.engine = QueryEngine(self.storage)
        
        # Seed data
        now = datetime.now()
        for i in range(24):
            self.storage.write(
                "requests_total",
                100 + i * 10,
                now - timedelta(hours=i),
                {"method": "GET"}
            )
    
    def test_simple_query(self):
        """Test simple metric query."""
        result = self.engine.execute("requests_total")
        
        assert result is not None
        assert len(result.data) > 0
    
    def test_sum_query(self):
        """Test sum aggregation query."""
        result = self.engine.execute("sum(requests_total)")
        
        assert result is not None
        assert result.scalar is not None
    
    def test_rate_query(self):
        """Test rate query."""
        result = self.engine.execute("rate(requests_total[5m])")
        
        assert result is not None
    
    def test_query_with_labels(self):
        """Test query with label filter."""
        result = self.engine.execute('requests_total{method="GET"}')
        
        assert result is not None


class TestQueryParser:
    """Tests for QueryParser."""
    
    def test_parse_simple_metric(self):
        """Test parsing simple metric name."""
        parser = QueryParser()
        result = parser.parse("requests_total")
        
        assert result["metric"] == "requests_total"
        assert result["labels"] == {}
    
    def test_parse_with_labels(self):
        """Test parsing with labels."""
        parser = QueryParser()
        result = parser.parse('http_requests{method="GET",status="200"}')
        
        assert result["metric"] == "http_requests"
        assert result["labels"]["method"] == "GET"
        assert result["labels"]["status"] == "200"
    
    def test_parse_with_function(self):
        """Test parsing with function."""
        parser = QueryParser()
        result = parser.parse("sum(requests_total)")
        
        assert result["function"] == "sum"
        assert result["metric"] == "requests_total"
    
    def test_parse_with_range(self):
        """Test parsing with time range."""
        parser = QueryParser()
        result = parser.parse("rate(requests_total[5m])")
        
        assert result["function"] == "rate"
        assert result["range"] == "5m"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
