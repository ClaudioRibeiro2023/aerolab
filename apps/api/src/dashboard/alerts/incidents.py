"""
Incidents - Gerenciamento de incidentes.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid


class IncidentStatus(str, Enum):
    """Status do incidente."""
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    IDENTIFIED = "identified"
    MONITORING = "monitoring"
    RESOLVED = "resolved"
    CLOSED = "closed"


class IncidentSeverity(str, Enum):
    """Severidade do incidente."""
    SEV1 = "sev1"  # Critical
    SEV2 = "sev2"  # Major
    SEV3 = "sev3"  # Minor
    SEV4 = "sev4"  # Low


@dataclass
class IncidentUpdate:
    """Atualização de incidente."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    author: str = ""
    message: str = ""
    status_change: Optional[IncidentStatus] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "author": self.author,
            "message": self.message,
            "statusChange": self.status_change.value if self.status_change else None,
        }


@dataclass
class Incident:
    """
    Incidente.
    
    Representa um problema que requer atenção.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Identificação
    title: str = ""
    description: str = ""
    
    # Relacionado a alertas
    alert_rule_ids: List[str] = field(default_factory=list)
    
    # Severidade e status
    severity: IncidentSeverity = IncidentSeverity.SEV3
    status: IncidentStatus = IncidentStatus.OPEN
    
    # Impacto
    impacted_services: List[str] = field(default_factory=list)
    impacted_users_estimate: int = 0
    
    # Responsáveis
    owner: str = ""
    responders: List[str] = field(default_factory=list)
    
    # Timeline
    updates: List[IncidentUpdate] = field(default_factory=list)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    
    # Root cause
    root_cause: str = ""
    resolution: str = ""
    
    # Post-mortem
    postmortem_url: str = ""
    
    # Labels
    labels: Dict[str, str] = field(default_factory=dict)
    
    @property
    def duration(self) -> Optional[timedelta]:
        """Duração do incidente."""
        if self.resolved_at:
            return self.resolved_at - self.created_at
        return datetime.now() - self.created_at
    
    @property
    def time_to_acknowledge(self) -> Optional[timedelta]:
        """Tempo até acknowledge."""
        if self.acknowledged_at:
            return self.acknowledged_at - self.created_at
        return None
    
    @property
    def time_to_resolve(self) -> Optional[timedelta]:
        """Tempo até resolução."""
        if self.resolved_at:
            return self.resolved_at - self.created_at
        return None
    
    def acknowledge(self, user: str) -> None:
        """Reconhece o incidente."""
        self.status = IncidentStatus.ACKNOWLEDGED
        self.acknowledged_at = datetime.now()
        self.responders.append(user)
        
        self.updates.append(IncidentUpdate(
            author=user,
            message="Incident acknowledged",
            status_change=IncidentStatus.ACKNOWLEDGED
        ))
    
    def update_status(
        self,
        status: IncidentStatus,
        user: str,
        message: str = ""
    ) -> None:
        """Atualiza status."""
        old_status = self.status
        self.status = status
        
        if status == IncidentStatus.RESOLVED and not self.resolved_at:
            self.resolved_at = datetime.now()
        elif status == IncidentStatus.CLOSED and not self.closed_at:
            self.closed_at = datetime.now()
        
        self.updates.append(IncidentUpdate(
            author=user,
            message=message or f"Status changed from {old_status.value} to {status.value}",
            status_change=status
        ))
    
    def add_update(self, user: str, message: str) -> None:
        """Adiciona atualização."""
        self.updates.append(IncidentUpdate(
            author=user,
            message=message
        ))
    
    def resolve(self, user: str, resolution: str) -> None:
        """Resolve o incidente."""
        self.resolution = resolution
        self.update_status(IncidentStatus.RESOLVED, user, resolution)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "alertRuleIds": self.alert_rule_ids,
            "severity": self.severity.value,
            "status": self.status.value,
            "impactedServices": self.impacted_services,
            "owner": self.owner,
            "responders": self.responders,
            "updates": [u.to_dict() for u in self.updates],
            "createdAt": self.created_at.isoformat(),
            "acknowledgedAt": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "resolvedAt": self.resolved_at.isoformat() if self.resolved_at else None,
            "duration": str(self.duration) if self.duration else None,
            "rootCause": self.root_cause,
            "resolution": self.resolution,
            "labels": self.labels,
        }


class IncidentManager:
    """Gerenciador de incidentes."""
    
    def __init__(self):
        self._incidents: Dict[str, Incident] = {}
    
    def create(
        self,
        title: str,
        description: str = "",
        severity: IncidentSeverity = IncidentSeverity.SEV3,
        alert_rule_ids: Optional[List[str]] = None
    ) -> Incident:
        """Cria incidente."""
        incident = Incident(
            title=title,
            description=description,
            severity=severity,
            alert_rule_ids=alert_rule_ids or []
        )
        
        self._incidents[incident.id] = incident
        return incident
    
    def get(self, incident_id: str) -> Optional[Incident]:
        """Obtém incidente por ID."""
        return self._incidents.get(incident_id)
    
    def list(
        self,
        status: Optional[IncidentStatus] = None,
        severity: Optional[IncidentSeverity] = None,
        limit: int = 100
    ) -> List[Incident]:
        """Lista incidentes."""
        incidents = list(self._incidents.values())
        
        if status:
            incidents = [i for i in incidents if i.status == status]
        if severity:
            incidents = [i for i in incidents if i.severity == severity]
        
        return sorted(incidents, key=lambda i: i.created_at, reverse=True)[:limit]
    
    def get_open(self) -> List[Incident]:
        """Lista incidentes abertos."""
        return [
            i for i in self._incidents.values()
            if i.status not in (IncidentStatus.RESOLVED, IncidentStatus.CLOSED)
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas."""
        incidents = list(self._incidents.values())
        
        open_count = len([i for i in incidents if i.status == IncidentStatus.OPEN])
        resolved = [i for i in incidents if i.resolved_at]
        
        avg_resolution_time = None
        if resolved:
            total_time = sum((i.time_to_resolve.total_seconds() for i in resolved if i.time_to_resolve), 0)
            avg_resolution_time = total_time / len(resolved) / 60  # minutos
        
        return {
            "total": len(incidents),
            "open": open_count,
            "acknowledged": len([i for i in incidents if i.status == IncidentStatus.ACKNOWLEDGED]),
            "resolved": len(resolved),
            "avgResolutionTimeMinutes": avg_resolution_time,
            "bySeverity": {
                "sev1": len([i for i in incidents if i.severity == IncidentSeverity.SEV1]),
                "sev2": len([i for i in incidents if i.severity == IncidentSeverity.SEV2]),
                "sev3": len([i for i in incidents if i.severity == IncidentSeverity.SEV3]),
                "sev4": len([i for i in incidents if i.severity == IncidentSeverity.SEV4]),
            }
        }


# Singleton
_manager: Optional[IncidentManager] = None


def get_incident_manager() -> IncidentManager:
    """Obtém gerenciador de incidentes."""
    global _manager
    if _manager is None:
        _manager = IncidentManager()
    return _manager
