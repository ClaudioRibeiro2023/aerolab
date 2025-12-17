"""
Anomaly Detection - Detecção de anomalias em métricas.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
import statistics
import math
import logging

logger = logging.getLogger(__name__)


class AnomalyType(str, Enum):
    """Tipos de anomalia."""
    SPIKE = "spike"           # Pico súbito
    DROP = "drop"             # Queda súbita
    TREND_CHANGE = "trend"    # Mudança de tendência
    OUTLIER = "outlier"       # Valor fora do padrão
    MISSING = "missing"       # Dados faltantes
    PATTERN_BREAK = "pattern" # Quebra de padrão


class AnomalySeverity(str, Enum):
    """Severidade da anomalia."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Anomaly:
    """Anomalia detectada."""
    id: str = ""
    metric: str = ""
    type: AnomalyType = AnomalyType.OUTLIER
    severity: AnomalySeverity = AnomalySeverity.MEDIUM
    
    # Valores
    value: float = 0.0
    expected_value: float = 0.0
    deviation: float = 0.0  # Desvios padrão da média
    
    # Tempo
    timestamp: datetime = field(default_factory=datetime.now)
    duration: Optional[timedelta] = None
    
    # Contexto
    description: str = ""
    possible_causes: List[str] = field(default_factory=list)
    
    # Score
    confidence: float = 0.0  # 0-1
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "metric": self.metric,
            "type": self.type.value,
            "severity": self.severity.value,
            "value": self.value,
            "expectedValue": self.expected_value,
            "deviation": round(self.deviation, 2),
            "timestamp": self.timestamp.isoformat(),
            "duration": str(self.duration) if self.duration else None,
            "description": self.description,
            "possibleCauses": self.possible_causes,
            "confidence": round(self.confidence, 2),
        }


class AnomalyDetector:
    """
    Detector de anomalias.
    
    Algoritmos:
    - Z-Score (desvio padrão)
    - IQR (Interquartile Range)
    - Moving Average
    - Isolation Forest (simplificado)
    """
    
    def __init__(
        self,
        sensitivity: float = 0.5,  # 0=low, 1=high
        min_data_points: int = 10
    ):
        self.sensitivity = sensitivity
        self.min_data_points = min_data_points
        
        # Threshold baseado em sensibilidade
        # sensitivity 0.5 = 2.5 desvios padrão
        self.z_threshold = 4.0 - (sensitivity * 3.0)
    
    def detect_zscore(
        self,
        values: List[float],
        timestamps: Optional[List[datetime]] = None,
        metric_name: str = ""
    ) -> List[Anomaly]:
        """
        Detecção por Z-Score.
        
        Identifica valores que estão muitos desvios padrão da média.
        """
        if len(values) < self.min_data_points:
            return []
        
        mean = statistics.mean(values)
        stdev = statistics.stdev(values) if len(values) > 1 else 0
        
        if stdev == 0:
            return []
        
        anomalies = []
        
        for i, value in enumerate(values):
            z_score = abs(value - mean) / stdev
            
            if z_score > self.z_threshold:
                anomaly_type = AnomalyType.SPIKE if value > mean else AnomalyType.DROP
                severity = self._calculate_severity(z_score)
                
                anomaly = Anomaly(
                    id=f"anomaly_{i}",
                    metric=metric_name,
                    type=anomaly_type,
                    severity=severity,
                    value=value,
                    expected_value=mean,
                    deviation=z_score,
                    timestamp=timestamps[i] if timestamps else datetime.now(),
                    description=f"Value {value:.2f} is {z_score:.1f} standard deviations from mean {mean:.2f}",
                    confidence=min(z_score / 5.0, 1.0)
                )
                anomalies.append(anomaly)
        
        return anomalies
    
    def detect_iqr(
        self,
        values: List[float],
        timestamps: Optional[List[datetime]] = None,
        metric_name: str = ""
    ) -> List[Anomaly]:
        """
        Detecção por IQR (Interquartile Range).
        
        Mais robusto contra outliers extremos.
        """
        if len(values) < self.min_data_points:
            return []
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        q1_idx = n // 4
        q3_idx = (3 * n) // 4
        
        q1 = sorted_values[q1_idx]
        q3 = sorted_values[q3_idx]
        iqr = q3 - q1
        
        # Ajustar multiplier pela sensibilidade
        multiplier = 2.5 - (self.sensitivity * 1.5)
        
        lower_bound = q1 - (multiplier * iqr)
        upper_bound = q3 + (multiplier * iqr)
        
        anomalies = []
        
        for i, value in enumerate(values):
            if value < lower_bound or value > upper_bound:
                anomaly_type = AnomalyType.SPIKE if value > upper_bound else AnomalyType.DROP
                deviation = abs(value - (q1 + q3) / 2) / iqr if iqr > 0 else 0
                
                anomaly = Anomaly(
                    id=f"anomaly_iqr_{i}",
                    metric=metric_name,
                    type=anomaly_type,
                    severity=self._calculate_severity(deviation),
                    value=value,
                    expected_value=(q1 + q3) / 2,
                    deviation=deviation,
                    timestamp=timestamps[i] if timestamps else datetime.now(),
                    description=f"Value {value:.2f} is outside IQR bounds [{lower_bound:.2f}, {upper_bound:.2f}]",
                    confidence=min(deviation / 3.0, 1.0)
                )
                anomalies.append(anomaly)
        
        return anomalies
    
    def detect_moving_average(
        self,
        values: List[float],
        timestamps: Optional[List[datetime]] = None,
        window_size: int = 5,
        metric_name: str = ""
    ) -> List[Anomaly]:
        """
        Detecção por Moving Average.
        
        Compara valores com média móvel local.
        """
        if len(values) < window_size + self.min_data_points:
            return []
        
        anomalies = []
        
        for i in range(window_size, len(values)):
            window = values[i - window_size:i]
            ma = statistics.mean(window)
            std = statistics.stdev(window) if len(window) > 1 else 0
            
            if std == 0:
                continue
            
            current = values[i]
            z_score = abs(current - ma) / std
            
            if z_score > self.z_threshold:
                anomaly_type = AnomalyType.SPIKE if current > ma else AnomalyType.DROP
                
                anomaly = Anomaly(
                    id=f"anomaly_ma_{i}",
                    metric=metric_name,
                    type=anomaly_type,
                    severity=self._calculate_severity(z_score),
                    value=current,
                    expected_value=ma,
                    deviation=z_score,
                    timestamp=timestamps[i] if timestamps else datetime.now(),
                    description=f"Value {current:.2f} deviates from moving average {ma:.2f}",
                    confidence=min(z_score / 5.0, 1.0)
                )
                anomalies.append(anomaly)
        
        return anomalies
    
    def detect_trend_change(
        self,
        values: List[float],
        timestamps: Optional[List[datetime]] = None,
        window_size: int = 10,
        metric_name: str = ""
    ) -> List[Anomaly]:
        """
        Detecta mudanças de tendência.
        """
        if len(values) < window_size * 2:
            return []
        
        anomalies = []
        
        for i in range(window_size, len(values) - window_size):
            before = values[i - window_size:i]
            after = values[i:i + window_size]
            
            # Calcular tendências (slope simplificado)
            before_trend = (before[-1] - before[0]) / window_size if window_size > 0 else 0
            after_trend = (after[-1] - after[0]) / window_size if window_size > 0 else 0
            
            # Detectar inversão de tendência
            if before_trend * after_trend < 0:  # Sinais opostos
                trend_change = abs(after_trend - before_trend)
                
                if trend_change > 0.1:  # Threshold mínimo
                    anomaly = Anomaly(
                        id=f"anomaly_trend_{i}",
                        metric=metric_name,
                        type=AnomalyType.TREND_CHANGE,
                        severity=AnomalySeverity.MEDIUM,
                        value=values[i],
                        expected_value=values[i-1] + before_trend,
                        deviation=trend_change,
                        timestamp=timestamps[i] if timestamps else datetime.now(),
                        description=f"Trend changed from {before_trend:.3f} to {after_trend:.3f}",
                        confidence=min(trend_change, 1.0)
                    )
                    anomalies.append(anomaly)
        
        return anomalies
    
    def detect_all(
        self,
        values: List[float],
        timestamps: Optional[List[datetime]] = None,
        metric_name: str = ""
    ) -> List[Anomaly]:
        """Executa todos os detectores e combina resultados."""
        all_anomalies = []
        
        # Z-Score
        all_anomalies.extend(
            self.detect_zscore(values, timestamps, metric_name)
        )
        
        # IQR
        all_anomalies.extend(
            self.detect_iqr(values, timestamps, metric_name)
        )
        
        # Moving Average
        all_anomalies.extend(
            self.detect_moving_average(values, timestamps, 5, metric_name)
        )
        
        # Trend Change
        all_anomalies.extend(
            self.detect_trend_change(values, timestamps, 10, metric_name)
        )
        
        # Deduplicate by timestamp (keep highest confidence)
        seen = {}
        for anomaly in all_anomalies:
            key = (anomaly.timestamp, anomaly.type)
            if key not in seen or anomaly.confidence > seen[key].confidence:
                seen[key] = anomaly
        
        return sorted(seen.values(), key=lambda a: a.confidence, reverse=True)
    
    def _calculate_severity(self, deviation: float) -> AnomalySeverity:
        """Calcula severidade baseada no desvio."""
        if deviation > 5:
            return AnomalySeverity.CRITICAL
        elif deviation > 4:
            return AnomalySeverity.HIGH
        elif deviation > 3:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW


# Singleton
_detector: Optional[AnomalyDetector] = None


def get_anomaly_detector(sensitivity: float = 0.5) -> AnomalyDetector:
    """Obtém detector de anomalias."""
    global _detector
    if _detector is None:
        _detector = AnomalyDetector(sensitivity=sensitivity)
    return _detector
