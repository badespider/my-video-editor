import { useEffect, useRef, useState } from 'react';

interface WebSocketMessage {
  type: string;
  data?: any;
  error?: string;
  command?: string;
  parameters?: any;
}

interface UseWebSocketReturn {
  sendMessage: (message: WebSocketMessage) => void;
  lastMessage: WebSocketMessage | null;
  connectionStatus: 'Connecting' | 'Open' | 'Closing' | 'Closed';
  error: string | null;
}

// Dynamic WebSocket URL that works in different environments
const getWebSocketUrl = (path: string) => {
  if (process.env.REACT_APP_WS_BASE_URL) {
    return `${process.env.REACT_APP_WS_BASE_URL}${path}`;
  }
  
  // In webcontainer or proxied environments
  if (window.location.hostname.includes('webcontainer') || 
      window.location.hostname.includes('local-credentialless')) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // Replace the port number in the dynamic hostname (e.g., --3000-- to --8000--)
    const hostname = window.location.hostname.replace(/--3000--/, '--8000--');
    const wsUrl = `${protocol}//${hostname}${path}`;
    return `${wsUrl}${path}`;
  }
  
  // Default for local development
  return `ws://localhost:8000${path}`;
};

export const useWebSocket = (path: string, enabled: boolean = true): UseWebSocketReturn => {
  const [connectionStatus, setConnectionStatus] = useState<'Connecting' | 'Open' | 'Closing' | 'Closed'>('Closed');
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [error, setError] = useState<string | null>(null);
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!enabled) return;

    const url = getWebSocketUrl(path);
    
    const connect = () => {
      try {
        setConnectionStatus('Connecting');
        setError(null);
        
        ws.current = new WebSocket(url);

        ws.current.onopen = () => {
          setConnectionStatus('Open');
          console.log('WebSocket connected:', url);
        };

        ws.current.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            setLastMessage(message);
            console.log('WebSocket message received:', message);
          } catch (err) {
            console.error('Failed to parse WebSocket message:', event.data);
            setLastMessage({ type: 'error', error: 'Failed to parse message' });
          }
        };

        ws.current.onclose = (event) => {
          setConnectionStatus('Closed');
          console.log('WebSocket closed:', event.code, event.reason);
          
          // Attempt to reconnect after 3 seconds if not a normal closure
          if (event.code !== 1000 && enabled) {
            setTimeout(connect, 3000);
          }
        };

        ws.current.onerror = (event) => {
          console.error('WebSocket error:', event);
          setError('WebSocket connection error');
        };
      } catch (err) {
        console.error('Failed to create WebSocket:', err);
        setError('Failed to create WebSocket connection');
        setConnectionStatus('Closed');
      }
    };

    connect();

    return () => {
      if (ws.current) {
        setConnectionStatus('Closing');
        ws.current.close(1000, 'Component unmounting');
      }
    };
  }, [path, enabled]);

  const sendMessage = (message: WebSocketMessage) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      try {
        ws.current.send(JSON.stringify(message));
        console.log('WebSocket message sent:', message);
      } catch (err) {
        console.error('Failed to send WebSocket message:', err);
        setError('Failed to send message');
      }
    } else {
      console.warn('WebSocket is not open. Current state:', ws.current?.readyState);
      setError('WebSocket is not connected');
    }
  };

  return {
    sendMessage,
    lastMessage,
    connectionStatus,
    error,
  };
};