'use client';

import { useState, useEffect, useCallback, useRef } from 'react';

export type WebSocketStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

interface WebSocketMessage {
  type: string;
  channel?: string;
  data?: unknown;
  timestamp?: string;
}

interface UseWebSocketOptions {
  url: string;
  autoConnect?: boolean;
  reconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (error: Event) => void;
  onMessage?: (message: WebSocketMessage) => void;
}

interface UseWebSocketReturn {
  status: WebSocketStatus;
  lastMessage: WebSocketMessage | null;
  send: (data: WebSocketMessage) => void;
  subscribe: (channel: string) => void;
  unsubscribe: (channel: string) => void;
  connect: () => void;
  disconnect: () => void;
  isConnected: boolean;
}

export function useWebSocket(options: UseWebSocketOptions): UseWebSocketReturn {
  const {
    url,
    autoConnect = true,
    reconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    onOpen,
    onClose,
    onError,
    onMessage,
  } = options;

  const [status, setStatus] = useState<WebSocketStatus>('disconnected');
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const subscribedChannelsRef = useRef<Set<string>>(new Set());

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    setStatus('connecting');
    
    try {
      wsRef.current = new WebSocket(url);

      wsRef.current.onopen = () => {
        setStatus('connected');
        reconnectAttemptsRef.current = 0;
        
        // Re-subscribe to channels
        subscribedChannelsRef.current.forEach(channel => {
          wsRef.current?.send(JSON.stringify({
            type: 'subscribe',
            channel,
          }));
        });
        
        onOpen?.();
      };

      wsRef.current.onclose = () => {
        setStatus('disconnected');
        onClose?.();
        
        // Attempt reconnection
        if (reconnect && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        }
      };

      wsRef.current.onerror = (error) => {
        setStatus('error');
        onError?.(error);
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data) as WebSocketMessage;
          setLastMessage(message);
          onMessage?.(message);
        } catch {
          console.error('Failed to parse WebSocket message');
        }
      };
    } catch (error) {
      setStatus('error');
      console.error('WebSocket connection error:', error);
    }
  }, [url, reconnect, reconnectInterval, maxReconnectAttempts, onOpen, onClose, onError, onMessage]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setStatus('disconnected');
  }, []);

  const send = useCallback((data: WebSocketMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    } else {
      console.warn('WebSocket is not connected');
    }
  }, []);

  const subscribe = useCallback((channel: string) => {
    subscribedChannelsRef.current.add(channel);
    
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      send({ type: 'subscribe', channel });
    }
  }, [send]);

  const unsubscribe = useCallback((channel: string) => {
    subscribedChannelsRef.current.delete(channel);
    
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      send({ type: 'unsubscribe', channel });
    }
  }, [send]);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect) {
      connect();
    }
    
    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  // Ping/pong to keep connection alive
  useEffect(() => {
    if (status !== 'connected') return;

    const pingInterval = setInterval(() => {
      send({ type: 'ping' });
    }, 30000);

    return () => clearInterval(pingInterval);
  }, [status, send]);

  return {
    status,
    lastMessage,
    send,
    subscribe,
    unsubscribe,
    connect,
    disconnect,
    isConnected: status === 'connected',
  };
}

// Specialized hook for dashboard real-time updates
export function useDashboardWebSocket(dashboardId: string) {
  const baseUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
  
  const { status, lastMessage, subscribe, unsubscribe, isConnected } = useWebSocket({
    url: `${baseUrl}/ws/dashboard`,
    autoConnect: true,
    reconnect: true,
  });

  useEffect(() => {
    if (isConnected && dashboardId) {
      subscribe(`dashboard.${dashboardId}`);
      subscribe('dashboard.alerts');
    }
    
    return () => {
      unsubscribe(`dashboard.${dashboardId}`);
      unsubscribe('dashboard.alerts');
    };
  }, [isConnected, dashboardId, subscribe, unsubscribe]);

  return { status, lastMessage, isConnected };
}

// Specialized hook for metrics streaming
export function useMetricsStream(metricName: string, interval = 1) {
  const [data, setData] = useState<Array<{ timestamp: string; value: number }>>([]);
  const baseUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
  
  const { status, lastMessage, isConnected, send } = useWebSocket({
    url: `${baseUrl}/ws/metrics/${metricName}?interval=${interval}`,
    autoConnect: true,
    onMessage: (msg) => {
      if (msg.type === 'data' && msg.data) {
        setData(prev => [...prev.slice(-99), msg.data as { timestamp: string; value: number }]);
      }
    },
  });

  const pause = useCallback(() => send({ type: 'pause' }), [send]);
  const resume = useCallback(() => send({ type: 'resume' }), [send]);
  const clear = useCallback(() => setData([]), []);

  return { data, status, isConnected, pause, resume, clear };
}

// Specialized hook for alerts
export function useAlertsStream() {
  const [alerts, setAlerts] = useState<WebSocketMessage[]>([]);
  const baseUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
  
  const { status, isConnected } = useWebSocket({
    url: `${baseUrl}/ws/alerts`,
    autoConnect: true,
    onMessage: (msg) => {
      if (msg.type === 'alert') {
        setAlerts(prev => [msg, ...prev].slice(0, 100));
      }
    },
  });

  const clearAlerts = useCallback(() => setAlerts([]), []);

  return { alerts, status, isConnected, clearAlerts };
}

export default useWebSocket;
