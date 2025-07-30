import React, { useState, useEffect } from 'react';
import { Container, Typography, TextField, Button, Box, Paper, Alert, List, ListItem, ListItemText } from '@mui/material';
import { useAppContext } from '../context/AppContext';
import { apiService } from '../services/api';

const Edit: React.FC = () => {
  const [inputSessionId, setInputSessionId] = useState('');
  const [command, setCommand] = useState('');
  const [messages, setMessages] = useState<string[]>([]);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { sessionId, setSessionId } = useAppContext();
  const [ws, setWs] = useState<WebSocket | null>(null);

  const currentSessionId = sessionId || inputSessionId;

  useEffect(() => {
    if (currentSessionId && !ws) {
      connectWebSocket();
    }
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [currentSessionId]);

  const connectWebSocket = () => {
    if (!currentSessionId) return;

    const websocket = new WebSocket(`ws://localhost:8000/ws/edit/${currentSessionId}`);
    
    websocket.onopen = () => {
      setConnected(true);
      setError(null);
      setMessages(prev => [...prev, 'Connected to editing session']);
    };

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setMessages(prev => [...prev, `Server: ${JSON.stringify(data)}`]);
    };

    websocket.onclose = () => {
      setConnected(false);
      setMessages(prev => [...prev, 'Disconnected from editing session']);
    };

    websocket.onerror = (error) => {
      setError('WebSocket connection failed');
      setConnected(false);
    };

    setWs(websocket);
  };

  const sendCommand = () => {
    if (!ws || !command.trim()) return;

    const message = {
      command: command,
      parameters: {}
    };

    ws.send(JSON.stringify(message));
    setMessages(prev => [...prev, `You: ${command}`]);
    setCommand('');
  };

  const handleApplyEdits = async () => {
    if (!currentSessionId) return;

    try {
      const edits = [
        {
          command: command,
          parameters: {}
        }
      ];
      
      const response = await apiService.applyEdits(currentSessionId, { edits });
      setMessages(prev => [...prev, `Applied edits: ${JSON.stringify(response)}`]);
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to apply edits');
    }
  };

  return (
    <Container maxWidth="lg">
      <Typography variant="h4" component="h1" gutterBottom>
        Real-time Video Editing
      </Typography>

      <Paper sx={{ p: 4, mt: 3 }}>
        {!sessionId && (
          <TextField
            fullWidth
            label="Session ID"
            placeholder="Enter session ID to start editing..."
            value={inputSessionId}
            onChange={(e) => setInputSessionId(e.target.value)}
            sx={{ mb: 3 }}
          />
        )}

        {sessionId && (
          <Alert severity="info" sx={{ mb: 3 }}>
            Editing session: {sessionId}
          </Alert>
        )}

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
          <Typography variant="body2">
            Status: {connected ? '🟢 Connected' : '🔴 Disconnected'}
          </Typography>
          {!connected && currentSessionId && (
            <Button variant="outlined" size="small" onClick={connectWebSocket}>
              Reconnect
            </Button>
          )}
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
          <TextField
            fullWidth
            label="Edit Command"
            placeholder="Enter editing command (e.g., 'trim video from 10s to 30s')"
            value={command}
            onChange={(e) => setCommand(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendCommand()}
          />
          <Button
            variant="contained"
            onClick={sendCommand}
            disabled={!connected || !command.trim()}
          >
            Send
          </Button>
          <Button
            variant="outlined"
            onClick={handleApplyEdits}
            disabled={!currentSessionId || !command.trim()}
          >
            Apply
          </Button>
        </Box>

        <Paper sx={{ p: 2, maxHeight: 400, overflow: 'auto', backgroundColor: 'grey.50' }}>
          <Typography variant="h6" gutterBottom>
            Chat Log
          </Typography>
          <List dense>
            {messages.map((message, index) => (
              <ListItem key={index}>
                <ListItemText
                  primary={message}
                  primaryTypographyProps={{
                    variant: 'body2',
                    style: { fontFamily: 'monospace' }
                  }}
                />
              </ListItem>
            ))}
          </List>
        </Paper>
      </Paper>
    </Container>
  );
};

export default Edit;