"""
Pub/Sub Manager - Sistema de publish/subscribe para dashboards.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable, Set
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)


@dataclass
class Subscription:
    """Inscrição em um tópico."""
    id: str
    topic: str
    callback: Callable
    filter_func: Optional[Callable] = None
    created_at: datetime = field(default_factory=datetime.now)
    message_count: int = 0
    last_message_at: Optional[datetime] = None
    
    async def deliver(self, message: Any) -> bool:
        """Entrega mensagem para o subscriber."""
        # Aplicar filtro se existir
        if self.filter_func:
            try:
                if not self.filter_func(message):
                    return False
            except Exception:
                return False
        
        try:
            if asyncio.iscoroutinefunction(self.callback):
                await self.callback(message)
            else:
                self.callback(message)
            
            self.message_count += 1
            self.last_message_at = datetime.now()
            return True
            
        except Exception as e:
            logger.error(f"Error delivering message to subscription {self.id}: {e}")
            return False


@dataclass
class Topic:
    """Tópico de pub/sub."""
    name: str
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    
    # Stats
    message_count: int = 0
    subscriber_count: int = 0
    
    # Retention
    retain_last: bool = False
    last_message: Optional[Any] = None
    
    def record_message(self, message: Any):
        """Registra mensagem publicada."""
        self.message_count += 1
        if self.retain_last:
            self.last_message = message


class PubSubManager:
    """
    Gerenciador de Pub/Sub.
    
    Permite publicação e inscrição em tópicos para comunicação
    desacoplada entre componentes.
    """
    
    def __init__(self, max_topics: int = 1000, max_subscribers_per_topic: int = 100):
        self._topics: Dict[str, Topic] = {}
        self._subscriptions: Dict[str, Dict[str, Subscription]] = {}  # topic -> {sub_id: sub}
        self._subscriber_topics: Dict[str, Set[str]] = {}  # sub_id -> topics
        
        self._max_topics = max_topics
        self._max_subscribers = max_subscribers_per_topic
        
        self._sub_counter = 0
    
    def create_topic(
        self,
        name: str,
        description: str = "",
        retain_last: bool = False,
    ) -> Topic:
        """Cria um novo tópico."""
        if name in self._topics:
            return self._topics[name]
        
        if len(self._topics) >= self._max_topics:
            raise ValueError(f"Maximum number of topics ({self._max_topics}) reached")
        
        topic = Topic(
            name=name,
            description=description,
            retain_last=retain_last,
        )
        
        self._topics[name] = topic
        self._subscriptions[name] = {}
        
        logger.debug(f"Created topic: {name}")
        return topic
    
    def delete_topic(self, name: str) -> bool:
        """Remove um tópico."""
        if name not in self._topics:
            return False
        
        # Limpar inscrições
        subs = self._subscriptions.pop(name, {})
        for sub_id in subs:
            if sub_id in self._subscriber_topics:
                self._subscriber_topics[sub_id].discard(name)
        
        del self._topics[name]
        logger.debug(f"Deleted topic: {name}")
        return True
    
    def subscribe(
        self,
        topic: str,
        callback: Callable,
        filter_func: Optional[Callable] = None,
        subscriber_id: Optional[str] = None,
    ) -> str:
        """Inscreve em um tópico."""
        # Criar tópico se não existir
        if topic not in self._topics:
            self.create_topic(topic)
        
        # Verificar limite
        if len(self._subscriptions[topic]) >= self._max_subscribers:
            raise ValueError(f"Maximum subscribers for topic {topic} reached")
        
        # Gerar ID
        if not subscriber_id:
            self._sub_counter += 1
            subscriber_id = f"sub_{self._sub_counter}"
        
        sub = Subscription(
            id=subscriber_id,
            topic=topic,
            callback=callback,
            filter_func=filter_func,
        )
        
        self._subscriptions[topic][subscriber_id] = sub
        
        # Rastrear tópicos do subscriber
        if subscriber_id not in self._subscriber_topics:
            self._subscriber_topics[subscriber_id] = set()
        self._subscriber_topics[subscriber_id].add(topic)
        
        # Atualizar contagem
        self._topics[topic].subscriber_count = len(self._subscriptions[topic])
        
        # Entregar última mensagem retida
        if self._topics[topic].retain_last and self._topics[topic].last_message is not None:
            asyncio.create_task(sub.deliver(self._topics[topic].last_message))
        
        logger.debug(f"Subscription {subscriber_id} created for topic {topic}")
        return subscriber_id
    
    def unsubscribe(self, subscriber_id: str, topic: Optional[str] = None):
        """Cancela inscrição."""
        if topic:
            # Cancelar de tópico específico
            if topic in self._subscriptions:
                self._subscriptions[topic].pop(subscriber_id, None)
                self._topics[topic].subscriber_count = len(self._subscriptions[topic])
            
            if subscriber_id in self._subscriber_topics:
                self._subscriber_topics[subscriber_id].discard(topic)
        else:
            # Cancelar de todos os tópicos
            topics = self._subscriber_topics.pop(subscriber_id, set())
            for t in topics:
                if t in self._subscriptions:
                    self._subscriptions[t].pop(subscriber_id, None)
                    if t in self._topics:
                        self._topics[t].subscriber_count = len(self._subscriptions[t])
        
        logger.debug(f"Subscription {subscriber_id} removed from topic {topic or 'all'}")
    
    async def publish(self, topic: str, message: Any) -> int:
        """
        Publica mensagem em um tópico.
        
        Returns:
            Número de subscribers que receberam a mensagem
        """
        if topic not in self._topics:
            logger.warning(f"Publishing to non-existent topic: {topic}")
            return 0
        
        self._topics[topic].record_message(message)
        
        delivered = 0
        subs = self._subscriptions.get(topic, {})
        
        for sub in subs.values():
            if await sub.deliver(message):
                delivered += 1
        
        return delivered
    
    async def publish_many(self, topic: str, messages: List[Any]) -> int:
        """Publica múltiplas mensagens."""
        total = 0
        for msg in messages:
            total += await self.publish(topic, msg)
        return total
    
    def get_topic(self, name: str) -> Optional[Topic]:
        """Obtém tópico por nome."""
        return self._topics.get(name)
    
    def list_topics(self) -> List[Topic]:
        """Lista todos os tópicos."""
        return list(self._topics.values())
    
    def get_subscriptions(self, topic: str) -> List[Subscription]:
        """Lista inscrições de um tópico."""
        return list(self._subscriptions.get(topic, {}).values())
    
    def get_subscriber_topics(self, subscriber_id: str) -> Set[str]:
        """Lista tópicos de um subscriber."""
        return self._subscriber_topics.get(subscriber_id, set())
    
    def get_stats(self) -> Dict[str, Any]:
        """Estatísticas do sistema."""
        total_subs = sum(len(s) for s in self._subscriptions.values())
        total_msgs = sum(t.message_count for t in self._topics.values())
        
        return {
            "totalTopics": len(self._topics),
            "totalSubscriptions": total_subs,
            "totalMessages": total_msgs,
            "topTopics": sorted(
                [
                    {"name": t.name, "subscribers": t.subscriber_count, "messages": t.message_count}
                    for t in self._topics.values()
                ],
                key=lambda x: x["subscribers"],
                reverse=True
            )[:10],
        }


# Singleton
_manager: Optional[PubSubManager] = None


def get_pubsub_manager() -> PubSubManager:
    """Obtém gerenciador de pub/sub."""
    global _manager
    if _manager is None:
        _manager = PubSubManager()
    return _manager


# Tópicos pré-definidos para dashboard
DASHBOARD_TOPICS = {
    "dashboard.metrics": "Real-time metric updates",
    "dashboard.alerts": "Alert notifications",
    "dashboard.widgets": "Widget data updates",
    "dashboard.traces": "Trace events",
    "dashboard.agents": "Agent execution events",
}


def initialize_dashboard_topics():
    """Inicializa tópicos padrão do dashboard."""
    manager = get_pubsub_manager()
    
    for name, description in DASHBOARD_TOPICS.items():
        manager.create_topic(name, description, retain_last=True)
