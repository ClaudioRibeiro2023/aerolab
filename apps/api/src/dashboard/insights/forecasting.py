"""
Forecasting - Previsão de tendências.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
import statistics
import math
import logging

logger = logging.getLogger(__name__)


@dataclass
class ForecastPoint:
    """Ponto de previsão."""
    timestamp: datetime
    value: float
    lower_bound: float  # Intervalo de confiança inferior
    upper_bound: float  # Intervalo de confiança superior
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "value": round(self.value, 4),
            "lowerBound": round(self.lower_bound, 4),
            "upperBound": round(self.upper_bound, 4),
        }


@dataclass
class Forecast:
    """Resultado de previsão."""
    metric: str = ""
    method: str = ""
    
    # Pontos previstos
    points: List[ForecastPoint] = field(default_factory=list)
    
    # Métricas de qualidade
    confidence: float = 0.0  # 0-1
    mape: Optional[float] = None  # Mean Absolute Percentage Error
    rmse: Optional[float] = None  # Root Mean Square Error
    
    # Tendência
    trend: str = "stable"  # up, down, stable
    trend_strength: float = 0.0
    
    # Sazonalidade
    has_seasonality: bool = False
    seasonality_period: Optional[int] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "metric": self.metric,
            "method": self.method,
            "points": [p.to_dict() for p in self.points],
            "confidence": round(self.confidence, 2),
            "mape": round(self.mape, 4) if self.mape else None,
            "trend": self.trend,
            "trendStrength": round(self.trend_strength, 2),
            "hasSeasonality": self.has_seasonality,
            "seasonalityPeriod": self.seasonality_period,
        }


class Forecaster:
    """
    Previsão de séries temporais.
    
    Métodos:
    - Linear Regression
    - Exponential Smoothing
    - Moving Average
    - Holt-Winters (simplificado)
    """
    
    def __init__(self, confidence_level: float = 0.95):
        self.confidence_level = confidence_level
        # Z-score para 95% confidence
        self.z_score = 1.96
    
    def linear_regression(
        self,
        values: List[float],
        timestamps: Optional[List[datetime]] = None,
        forecast_periods: int = 10,
        metric_name: str = ""
    ) -> Forecast:
        """
        Previsão por regressão linear.
        """
        if len(values) < 3:
            return Forecast(metric=metric_name, method="linear")
        
        n = len(values)
        x = list(range(n))
        
        # Calcular slope e intercept
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(values)
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        slope = numerator / denominator if denominator != 0 else 0
        intercept = y_mean - slope * x_mean
        
        # Calcular erro padrão
        predictions = [intercept + slope * i for i in range(n)]
        errors = [values[i] - predictions[i] for i in range(n)]
        std_error = statistics.stdev(errors) if len(errors) > 1 else 0
        
        # Gerar previsões
        points = []
        last_ts = timestamps[-1] if timestamps else datetime.now()
        interval = timedelta(hours=1)  # Default interval
        
        if timestamps and len(timestamps) > 1:
            interval = (timestamps[-1] - timestamps[-2])
        
        for i in range(forecast_periods):
            future_x = n + i
            predicted = intercept + slope * future_x
            
            # Intervalo de confiança
            margin = self.z_score * std_error * math.sqrt(1 + 1/n)
            
            points.append(ForecastPoint(
                timestamp=last_ts + interval * (i + 1),
                value=predicted,
                lower_bound=predicted - margin,
                upper_bound=predicted + margin
            ))
        
        # Determinar tendência
        trend = "stable"
        if slope > 0.01:
            trend = "up"
        elif slope < -0.01:
            trend = "down"
        
        return Forecast(
            metric=metric_name,
            method="linear_regression",
            points=points,
            confidence=0.8,
            trend=trend,
            trend_strength=abs(slope)
        )
    
    def exponential_smoothing(
        self,
        values: List[float],
        timestamps: Optional[List[datetime]] = None,
        alpha: float = 0.3,
        forecast_periods: int = 10,
        metric_name: str = ""
    ) -> Forecast:
        """
        Previsão por Exponential Smoothing.
        
        Dá mais peso aos valores recentes.
        """
        if len(values) < 3:
            return Forecast(metric=metric_name, method="exponential_smoothing")
        
        # Simple Exponential Smoothing
        smoothed = [values[0]]
        
        for i in range(1, len(values)):
            s = alpha * values[i] + (1 - alpha) * smoothed[-1]
            smoothed.append(s)
        
        last_smoothed = smoothed[-1]
        
        # Calcular erro
        errors = [abs(values[i] - smoothed[i]) for i in range(len(values))]
        std_error = statistics.stdev(errors) if len(errors) > 1 else 0
        
        # Gerar previsões (flat para SES)
        points = []
        last_ts = timestamps[-1] if timestamps else datetime.now()
        interval = timedelta(hours=1)
        
        if timestamps and len(timestamps) > 1:
            interval = (timestamps[-1] - timestamps[-2])
        
        for i in range(forecast_periods):
            margin = self.z_score * std_error * math.sqrt(i + 1)
            
            points.append(ForecastPoint(
                timestamp=last_ts + interval * (i + 1),
                value=last_smoothed,
                lower_bound=last_smoothed - margin,
                upper_bound=last_smoothed + margin
            ))
        
        return Forecast(
            metric=metric_name,
            method="exponential_smoothing",
            points=points,
            confidence=0.75,
            trend="stable"
        )
    
    def holt_linear(
        self,
        values: List[float],
        timestamps: Optional[List[datetime]] = None,
        alpha: float = 0.3,
        beta: float = 0.1,
        forecast_periods: int = 10,
        metric_name: str = ""
    ) -> Forecast:
        """
        Holt's Linear Trend Method.
        
        Captura tendência linear.
        """
        if len(values) < 3:
            return Forecast(metric=metric_name, method="holt_linear")
        
        # Inicialização
        level = values[0]
        trend = values[1] - values[0] if len(values) > 1 else 0
        
        levels = [level]
        trends = [trend]
        
        for i in range(1, len(values)):
            prev_level = level
            level = alpha * values[i] + (1 - alpha) * (level + trend)
            trend = beta * (level - prev_level) + (1 - beta) * trend
            
            levels.append(level)
            trends.append(trend)
        
        # Calcular erro
        fitted = [levels[i] + trends[i] for i in range(len(values))]
        errors = [abs(values[i] - fitted[i]) for i in range(len(values))]
        std_error = statistics.stdev(errors) if len(errors) > 1 else 0
        
        # Gerar previsões
        points = []
        last_ts = timestamps[-1] if timestamps else datetime.now()
        interval = timedelta(hours=1)
        
        if timestamps and len(timestamps) > 1:
            interval = (timestamps[-1] - timestamps[-2])
        
        for i in range(forecast_periods):
            forecast_value = level + (i + 1) * trend
            margin = self.z_score * std_error * math.sqrt(i + 1)
            
            points.append(ForecastPoint(
                timestamp=last_ts + interval * (i + 1),
                value=forecast_value,
                lower_bound=forecast_value - margin,
                upper_bound=forecast_value + margin
            ))
        
        # Tendência
        trend_direction = "stable"
        if trend > 0.01:
            trend_direction = "up"
        elif trend < -0.01:
            trend_direction = "down"
        
        return Forecast(
            metric=metric_name,
            method="holt_linear",
            points=points,
            confidence=0.8,
            trend=trend_direction,
            trend_strength=abs(trend)
        )
    
    def auto_forecast(
        self,
        values: List[float],
        timestamps: Optional[List[datetime]] = None,
        forecast_periods: int = 10,
        metric_name: str = ""
    ) -> Forecast:
        """
        Seleciona automaticamente o melhor método.
        """
        if len(values) < 5:
            return self.exponential_smoothing(values, timestamps, 0.3, forecast_periods, metric_name)
        
        # Detectar tendência
        first_half = statistics.mean(values[:len(values)//2])
        second_half = statistics.mean(values[len(values)//2:])
        
        has_trend = abs(second_half - first_half) / (first_half if first_half != 0 else 1) > 0.05
        
        if has_trend:
            return self.holt_linear(values, timestamps, 0.3, 0.1, forecast_periods, metric_name)
        else:
            return self.exponential_smoothing(values, timestamps, 0.3, forecast_periods, metric_name)
    
    def evaluate_forecast(
        self,
        actual: List[float],
        predicted: List[float]
    ) -> Dict[str, float]:
        """Avalia qualidade da previsão."""
        if len(actual) != len(predicted) or len(actual) == 0:
            return {}
        
        # MAPE
        mape_values = []
        for a, p in zip(actual, predicted):
            if a != 0:
                mape_values.append(abs((a - p) / a))
        mape = statistics.mean(mape_values) if mape_values else 0
        
        # RMSE
        squared_errors = [(a - p) ** 2 for a, p in zip(actual, predicted)]
        rmse = math.sqrt(statistics.mean(squared_errors))
        
        # MAE
        mae = statistics.mean(abs(a - p) for a, p in zip(actual, predicted))
        
        return {
            "mape": mape,
            "rmse": rmse,
            "mae": mae,
        }


# Singleton
_forecaster: Optional[Forecaster] = None


def get_forecaster() -> Forecaster:
    """Obtém forecaster."""
    global _forecaster
    if _forecaster is None:
        _forecaster = Forecaster()
    return _forecaster
