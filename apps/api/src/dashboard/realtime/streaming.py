"""
Streaming Manager - Streaming de métricas em tempo real.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Callable, AsyncGenerator
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)


class StreamStatus(str, Enum):
    """Status do stream."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class MetricStream:
    """Stream de métricas."""
    id: str
    name: str
    query: str
    
    # Configuração
    interval_seconds: float = 1.0
    buffer_size: int = 100
    
    # Status
    status: StreamStatus = StreamStatus.IDLE
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    
    # Estatísticas
    points_emitted: int = 0
    errors: int = 0
    last_error: Optional[str] = None
    
    # Buffer
    buffer: List[Dict[str, Any]] = field(default_factory=list)
    
    # Callbacks
    _data_callback: Optional[Callable] = None
    _error_callback: Optional[Callable] = None
    
    def add_point(self, point: Dict[str, Any]):
        """Adiciona ponto ao buffer."""
        self.buffer.append(point)
        self.points_emitted += 1
        
        # Limitar tamanho do buffer
        if len(self.buffer) > self.buffer_size:
            self.buffer = self.buffer[-self.buffer_size:]
    
    def get_recent_points(self, count: int = 10) -> List[Dict[str, Any]]:
        """Obtém pontos recentes."""
        return self.buffer[-count:]
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "query": self.query,
            "intervalSeconds": self.interval_seconds,
            "status": self.status.value,
            "startedAt": self.started_at.isoformat() if self.started_at else None,
            "stoppedAt": self.stopped_at.isoformat() if self.stopped_at else None,
            "pointsEmitted": self.points_emitted,
            "errors": self.errors,
            "lastError": self.last_error,
            "bufferSize": len(self.buffer),
        }


class StreamManager:
    """
    Gerenciador de streams de métricas.
    
    Cria e gerencia streams de dados em tempo real para widgets.
    """
    
    def __init__(self, query_executor: Optional[Callable] = None):
        self._streams: Dict[str, MetricStream] = {}
        self._tasks: Dict[str, asyncio.Task] = {}
        self._query_executor = query_executor
        self._running = False
    
    async def start(self):
        """Inicia o gerenciador."""
        self._running = True
        logger.info("Stream manager started")
    
    async def stop(self):
        """Para o gerenciador e todos os streams."""
        self._running = False
        
        # Parar todos os streams
        for stream_id in list(self._streams.keys()):
            await self.stop_stream(stream_id)
        
        logger.info("Stream manager stopped")
    
    def create_stream(
        self,
        stream_id: str,
        name: str,
        query: str,
        interval_seconds: float = 1.0,
        buffer_size: int = 100,
        data_callback: Optional[Callable] = None,
        error_callback: Optional[Callable] = None,
    ) -> MetricStream:
        """Cria um novo stream."""
        if stream_id in self._streams:
            raise ValueError(f"Stream {stream_id} already exists")
        
        stream = MetricStream(
            id=stream_id,
            name=name,
            query=query,
            interval_seconds=interval_seconds,
            buffer_size=buffer_size,
        )
        
        stream._data_callback = data_callback
        stream._error_callback = error_callback
        
        self._streams[stream_id] = stream
        logger.debug(f"Created stream: {stream_id}")
        
        return stream
    
    async def start_stream(self, stream_id: str) -> bool:
        """Inicia um stream."""
        stream = self._streams.get(stream_id)
        if not stream:
            return False
        
        if stream.status == StreamStatus.RUNNING:
            return True
        
        stream.status = StreamStatus.RUNNING
        stream.started_at = datetime.now()
        
        # Criar task de streaming
        task = asyncio.create_task(self._stream_loop(stream))
        self._tasks[stream_id] = task
        
        logger.info(f"Started stream: {stream_id}")
        return True
    
    async def stop_stream(self, stream_id: str) -> bool:
        """Para um stream."""
        stream = self._streams.get(stream_id)
        if not stream:
            return False
        
        stream.status = StreamStatus.STOPPED
        stream.stopped_at = datetime.now()
        
        # Cancelar task
        task = self._tasks.pop(stream_id, None)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        logger.info(f"Stopped stream: {stream_id}")
        return True
    
    async def pause_stream(self, stream_id: str) -> bool:
        """Pausa um stream."""
        stream = self._streams.get(stream_id)
        if not stream or stream.status != StreamStatus.RUNNING:
            return False
        
        stream.status = StreamStatus.PAUSED
        return True
    
    async def resume_stream(self, stream_id: str) -> bool:
        """Retoma um stream pausado."""
        stream = self._streams.get(stream_id)
        if not stream or stream.status != StreamStatus.PAUSED:
            return False
        
        stream.status = StreamStatus.RUNNING
        return True
    
    def delete_stream(self, stream_id: str) -> bool:
        """Remove um stream."""
        if stream_id not in self._streams:
            return False
        
        # Parar se estiver rodando
        asyncio.create_task(self.stop_stream(stream_id))
        
        del self._streams[stream_id]
        logger.debug(f"Deleted stream: {stream_id}")
        return True
    
    async def _stream_loop(self, stream: MetricStream):
        """Loop de streaming."""
        while stream.status == StreamStatus.RUNNING and self._running:
            try:
                # Executar query
                data = await self._execute_query(stream.query)
                
                if data is not None:
                    point = {
                        "timestamp": datetime.now().isoformat(),
                        "value": data,
                    }
                    
                    stream.add_point(point)
                    
                    # Callback de dados
                    if stream._data_callback:
                        try:
                            if asyncio.iscoroutinefunction(stream._data_callback):
                                await stream._data_callback(stream.id, point)
                            else:
                                stream._data_callback(stream.id, point)
                        except Exception as e:
                            logger.error(f"Error in data callback: {e}")
                
                # Esperar pelo próximo intervalo
                await asyncio.sleep(stream.interval_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                stream.errors += 1
                stream.last_error = str(e)
                
                if stream._error_callback:
                    try:
                        if asyncio.iscoroutinefunction(stream._error_callback):
                            await stream._error_callback(stream.id, e)
                        else:
                            stream._error_callback(stream.id, e)
                    except Exception:
                        pass
                
                # Esperar antes de tentar novamente
                await asyncio.sleep(stream.interval_seconds * 2)
    
    async def _execute_query(self, query: str) -> Any:
        """Executa query para obter dados."""
        if self._query_executor:
            if asyncio.iscoroutinefunction(self._query_executor):
                return await self._query_executor(query)
            else:
                return self._query_executor(query)
        
        # Mock data se não houver executor
        import random
        return random.random() * 100
    
    def get_stream(self, stream_id: str) -> Optional[MetricStream]:
        """Obtém stream por ID."""
        return self._streams.get(stream_id)
    
    def list_streams(self) -> List[MetricStream]:
        """Lista todos os streams."""
        return list(self._streams.values())
    
    def get_active_streams(self) -> List[MetricStream]:
        """Lista streams ativos."""
        return [
            s for s in self._streams.values()
            if s.status == StreamStatus.RUNNING
        ]
    
    async def subscribe_to_stream(
        self,
        stream_id: str,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Inscreve em um stream como AsyncGenerator.
        
        Uso:
            async for point in manager.subscribe_to_stream("stream1"):
                print(point)
        """
        stream = self._streams.get(stream_id)
        if not stream:
            return
        
        last_index = len(stream.buffer)
        
        while stream.status in [StreamStatus.RUNNING, StreamStatus.PAUSED]:
            # Verificar novos pontos
            if len(stream.buffer) > last_index:
                for i in range(last_index, len(stream.buffer)):
                    yield stream.buffer[i]
                last_index = len(stream.buffer)
            
            await asyncio.sleep(stream.interval_seconds / 2)
    
    def get_stats(self) -> Dict[str, Any]:
        """Estatísticas do gerenciador."""
        streams = list(self._streams.values())
        
        return {
            "totalStreams": len(streams),
            "runningStreams": len([s for s in streams if s.status == StreamStatus.RUNNING]),
            "pausedStreams": len([s for s in streams if s.status == StreamStatus.PAUSED]),
            "totalPointsEmitted": sum(s.points_emitted for s in streams),
            "totalErrors": sum(s.errors for s in streams),
        }


# Singleton
_manager: Optional[StreamManager] = None


def get_stream_manager() -> StreamManager:
    """Obtém gerenciador de streams."""
    global _manager
    if _manager is None:
        _manager = StreamManager()
    return _manager
