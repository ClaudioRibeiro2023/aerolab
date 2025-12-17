"""
Módulo de Compliance LGPD/GDPR.

Gerencia consentimento, anonimização, direito ao esquecimento
e auditoria de dados pessoais.
"""

import os
import json
import hashlib
import re
from typing import Optional, List, Dict, Any, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum


class ConsentType(Enum):
    """Tipos de consentimento."""
    ESSENTIAL = "essential"           # Necessário para funcionamento
    ANALYTICS = "analytics"           # Análises e métricas
    MARKETING = "marketing"           # Marketing e comunicação
    THIRD_PARTY = "third_party"       # Compartilhamento com terceiros
    AI_PROCESSING = "ai_processing"   # Processamento por IA


class DataCategory(Enum):
    """Categorias de dados pessoais."""
    IDENTIFICATION = "identification"   # Nome, email, telefone
    FINANCIAL = "financial"             # Dados financeiros
    HEALTH = "health"                   # Dados de saúde
    BIOMETRIC = "biometric"             # Dados biométricos
    LOCATION = "location"               # Geolocalização
    BEHAVIORAL = "behavioral"           # Comportamento, preferências
    SENSITIVE = "sensitive"             # Dados sensíveis


@dataclass
class Consent:
    """Registro de consentimento."""
    user_id: str
    consent_type: ConsentType
    granted: bool
    granted_at: datetime
    expires_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    version: str = "1.0"


@dataclass
class DataSubjectRequest:
    """Requisição de titular de dados (DSAR)."""
    id: str
    user_id: str
    request_type: str  # access, rectification, erasure, portability
    status: str  # pending, processing, completed, rejected
    created_at: datetime
    completed_at: Optional[datetime] = None
    response: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


@dataclass
class AuditLog:
    """Log de auditoria de acesso a dados."""
    id: str
    timestamp: datetime
    user_id: str
    action: str
    data_category: DataCategory
    resource: str
    ip_address: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


class PIIDetector:
    """Detector de Informações Pessoais Identificáveis (PII)."""
    
    # Padrões de PII
    PATTERNS = {
        "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "cpf": r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}",
        "cnpj": r"\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}",
        "phone_br": r"(?:\+55\s?)?(?:\(?\d{2}\)?\s?)?\d{4,5}[-\s]?\d{4}",
        "credit_card": r"\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}",
        "ip_address": r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}",
        "date_of_birth": r"\d{2}/\d{2}/\d{4}",
        "rg": r"\d{2}\.?\d{3}\.?\d{3}-?[\dXx]",
    }
    
    @classmethod
    def detect(cls, text: str) -> Dict[str, List[str]]:
        """Detecta PII em texto."""
        found = {}
        for pii_type, pattern in cls.PATTERNS.items():
            matches = re.findall(pattern, text)
            if matches:
                found[pii_type] = matches
        return found
    
    @classmethod
    def has_pii(cls, text: str) -> bool:
        """Verifica se texto contém PII."""
        return bool(cls.detect(text))
    
    @classmethod
    def anonymize(cls, text: str, replacement: str = "[REDACTED]") -> str:
        """Anonimiza PII em texto."""
        result = text
        for pattern in cls.PATTERNS.values():
            result = re.sub(pattern, replacement, result)
        return result
    
    @classmethod
    def pseudonymize(cls, text: str, salt: str = "") -> str:
        """Pseudonimiza PII com hash."""
        result = text
        for pii_type, pattern in cls.PATTERNS.items():
            matches = re.findall(pattern, text)
            for match in matches:
                hash_value = hashlib.sha256(f"{match}{salt}".encode()).hexdigest()[:12]
                result = result.replace(match, f"[{pii_type.upper()}_{hash_value}]")
        return result


class GDPRCompliance:
    """
    Gerenciador de Compliance LGPD/GDPR.
    
    Features:
    - Gestão de consentimentos
    - Detecção de PII
    - Anonimização/Pseudonimização
    - Direito ao esquecimento
    - Portabilidade de dados
    - Auditoria de acessos
    - Políticas de retenção
    
    Configuração:
        GDPR_STORAGE_PATH: Diretório para dados de compliance
        GDPR_RETENTION_DAYS: Período de retenção padrão
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = Path(storage_path or os.getenv("GDPR_STORAGE_PATH", "./data/compliance"))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.retention_days = int(os.getenv("GDPR_RETENTION_DAYS", "365"))
        
        # Cache em memória
        self._consents: Dict[str, List[Consent]] = {}
        self._requests: Dict[str, DataSubjectRequest] = {}
        self._audit_logs: List[AuditLog] = []
        
        self._load_data()
    
    def _load_data(self):
        """Carrega dados persistidos."""
        consents_file = self.storage_path / "consents.json"
        if consents_file.exists():
            data = json.loads(consents_file.read_text())
            for user_id, consents in data.items():
                self._consents[user_id] = [
                    Consent(
                        user_id=c["user_id"],
                        consent_type=ConsentType(c["consent_type"]),
                        granted=c["granted"],
                        granted_at=datetime.fromisoformat(c["granted_at"]),
                        expires_at=datetime.fromisoformat(c["expires_at"]) if c.get("expires_at") else None,
                        ip_address=c.get("ip_address"),
                        user_agent=c.get("user_agent"),
                        version=c.get("version", "1.0")
                    )
                    for c in consents
                ]
    
    def _save_data(self):
        """Persiste dados."""
        consents_data = {}
        for user_id, consents in self._consents.items():
            consents_data[user_id] = [
                {
                    "user_id": c.user_id,
                    "consent_type": c.consent_type.value,
                    "granted": c.granted,
                    "granted_at": c.granted_at.isoformat(),
                    "expires_at": c.expires_at.isoformat() if c.expires_at else None,
                    "ip_address": c.ip_address,
                    "user_agent": c.user_agent,
                    "version": c.version
                }
                for c in consents
            ]
        
        (self.storage_path / "consents.json").write_text(json.dumps(consents_data, indent=2))
    
    # Gestão de Consentimento
    def grant_consent(
        self,
        user_id: str,
        consent_type: ConsentType,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        expires_days: Optional[int] = None
    ) -> Consent:
        """Registra consentimento."""
        consent = Consent(
            user_id=user_id,
            consent_type=consent_type,
            granted=True,
            granted_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=expires_days) if expires_days else None,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if user_id not in self._consents:
            self._consents[user_id] = []
        
        # Remover consentimento anterior do mesmo tipo
        self._consents[user_id] = [
            c for c in self._consents[user_id]
            if c.consent_type != consent_type
        ]
        
        self._consents[user_id].append(consent)
        self._save_data()
        
        self._log_audit(user_id, "consent_granted", DataCategory.BEHAVIORAL, 
                        f"consent:{consent_type.value}")
        
        return consent
    
    def revoke_consent(self, user_id: str, consent_type: ConsentType) -> bool:
        """Revoga consentimento."""
        if user_id not in self._consents:
            return False
        
        for consent in self._consents[user_id]:
            if consent.consent_type == consent_type:
                consent.granted = False
                self._save_data()
                self._log_audit(user_id, "consent_revoked", DataCategory.BEHAVIORAL,
                               f"consent:{consent_type.value}")
                return True
        
        return False
    
    def has_consent(self, user_id: str, consent_type: ConsentType) -> bool:
        """Verifica se usuário tem consentimento ativo."""
        if user_id not in self._consents:
            return False
        
        for consent in self._consents[user_id]:
            if consent.consent_type == consent_type and consent.granted:
                if consent.expires_at and consent.expires_at < datetime.utcnow():
                    return False
                return True
        
        return False
    
    def get_user_consents(self, user_id: str) -> List[Dict[str, Any]]:
        """Retorna todos os consentimentos do usuário."""
        consents = self._consents.get(user_id, [])
        return [
            {
                "type": c.consent_type.value,
                "granted": c.granted,
                "granted_at": c.granted_at.isoformat(),
                "expires_at": c.expires_at.isoformat() if c.expires_at else None,
                "active": c.granted and (not c.expires_at or c.expires_at > datetime.utcnow())
            }
            for c in consents
        ]
    
    # Direitos do Titular (DSAR)
    def request_data_access(self, user_id: str) -> DataSubjectRequest:
        """Solicita acesso aos dados pessoais (Art. 15 GDPR)."""
        import uuid
        
        request = DataSubjectRequest(
            id=str(uuid.uuid4()),
            user_id=user_id,
            request_type="access",
            status="pending",
            created_at=datetime.utcnow()
        )
        
        self._requests[request.id] = request
        self._log_audit(user_id, "data_access_requested", DataCategory.IDENTIFICATION,
                       f"request:{request.id}")
        
        return request
    
    def request_data_erasure(self, user_id: str) -> DataSubjectRequest:
        """Solicita exclusão dos dados (Direito ao Esquecimento - Art. 17 GDPR)."""
        import uuid
        
        request = DataSubjectRequest(
            id=str(uuid.uuid4()),
            user_id=user_id,
            request_type="erasure",
            status="pending",
            created_at=datetime.utcnow()
        )
        
        self._requests[request.id] = request
        self._log_audit(user_id, "data_erasure_requested", DataCategory.IDENTIFICATION,
                       f"request:{request.id}")
        
        return request
    
    def request_data_portability(self, user_id: str) -> DataSubjectRequest:
        """Solicita portabilidade dos dados (Art. 20 GDPR)."""
        import uuid
        
        request = DataSubjectRequest(
            id=str(uuid.uuid4()),
            user_id=user_id,
            request_type="portability",
            status="pending",
            created_at=datetime.utcnow()
        )
        
        self._requests[request.id] = request
        self._log_audit(user_id, "data_portability_requested", DataCategory.IDENTIFICATION,
                       f"request:{request.id}")
        
        return request
    
    def process_erasure_request(
        self,
        request_id: str,
        data_sources: List[Any]
    ) -> bool:
        """Processa requisição de exclusão."""
        request = self._requests.get(request_id)
        if not request or request.request_type != "erasure":
            return False
        
        request.status = "processing"
        user_id = request.user_id
        
        # Remover dados de cada fonte
        for source in data_sources:
            if hasattr(source, "delete_user_data"):
                source.delete_user_data(user_id)
        
        # Remover consentimentos
        if user_id in self._consents:
            del self._consents[user_id]
        
        request.status = "completed"
        request.completed_at = datetime.utcnow()
        
        self._save_data()
        self._log_audit(user_id, "data_erased", DataCategory.IDENTIFICATION,
                       f"request:{request_id}")
        
        return True
    
    def export_user_data(
        self,
        user_id: str,
        data_sources: List[Any],
        format: str = "json"
    ) -> Dict[str, Any]:
        """Exporta todos os dados do usuário (Portabilidade)."""
        export = {
            "user_id": user_id,
            "exported_at": datetime.utcnow().isoformat(),
            "format": format,
            "data": {}
        }
        
        # Coletar dados de cada fonte
        for source in data_sources:
            source_name = getattr(source, "name", type(source).__name__)
            if hasattr(source, "get_user_data"):
                export["data"][source_name] = source.get_user_data(user_id)
        
        # Incluir consentimentos
        export["data"]["consents"] = self.get_user_consents(user_id)
        
        self._log_audit(user_id, "data_exported", DataCategory.IDENTIFICATION,
                       f"format:{format}")
        
        return export
    
    # Auditoria
    def _log_audit(
        self,
        user_id: str,
        action: str,
        data_category: DataCategory,
        resource: str,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Registra log de auditoria."""
        import uuid
        
        log = AuditLog(
            id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            user_id=user_id,
            action=action,
            data_category=data_category,
            resource=resource,
            ip_address=ip_address,
            details=details or {}
        )
        
        self._audit_logs.append(log)
        
        # Persistir logs periodicamente
        if len(self._audit_logs) % 100 == 0:
            self._save_audit_logs()
    
    def _save_audit_logs(self):
        """Salva logs de auditoria."""
        logs_file = self.storage_path / f"audit_{datetime.utcnow().strftime('%Y%m%d')}.json"
        
        existing = []
        if logs_file.exists():
            existing = json.loads(logs_file.read_text())
        
        new_logs = [
            {
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "user_id": log.user_id,
                "action": log.action,
                "data_category": log.data_category.value,
                "resource": log.resource,
                "ip_address": log.ip_address,
                "details": log.details
            }
            for log in self._audit_logs
        ]
        
        logs_file.write_text(json.dumps(existing + new_logs, indent=2))
        self._audit_logs = []
    
    def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Consulta logs de auditoria."""
        # Carregar logs dos arquivos
        logs = []
        for log_file in sorted(self.storage_path.glob("audit_*.json"), reverse=True):
            if len(logs) >= limit:
                break
            
            file_logs = json.loads(log_file.read_text())
            for log in file_logs:
                if user_id and log["user_id"] != user_id:
                    continue
                if action and log["action"] != action:
                    continue
                
                log_time = datetime.fromisoformat(log["timestamp"])
                if start_date and log_time < start_date:
                    continue
                if end_date and log_time > end_date:
                    continue
                
                logs.append(log)
                if len(logs) >= limit:
                    break
        
        return logs


# Singleton
_compliance: Optional[GDPRCompliance] = None


def get_gdpr_compliance() -> GDPRCompliance:
    """Obtém instância singleton do módulo de compliance."""
    global _compliance
    if _compliance is None:
        _compliance = GDPRCompliance()
    return _compliance
