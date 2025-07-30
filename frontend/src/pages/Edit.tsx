import React, { useState, useEffect } from 'react';
import { Container, Typography, TextField, Button, Box, Paper, Alert, List, ListItem, ListItemText } from '@mui/material';
import { useAppContext } from '../context/AppContext';
import { apiService } from '../services/api';
import { useWebSocket } from '../hooks/useWebSocket';

const Edit: React.FC = () => {
  const [inputSessionId, setInputSessionId] = useState('');
  const [command, setCommand] = useState('');
  const [messages, setMessages] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const { sessionId, setSessionId } = useAppContext();

  const currentSessionId = sessionId || inputSessionId;
  
  const { sendMessage, lastMessage, connectionStatus } = useWebSocket(
    `/ws/edit/${currentSessionId}`,
    !!currentSessionId
  );

  useEffect(() => {
    if (lastMessage) {
      setMessages(prev => [...prev, `Server: ${JSON.stringify(lastMessage)}`]);
    }
  }, [lastMessage]);

  const handleSendCommand = () => {
    if (!command.trim()) return;

    const message = {
      type: 'command',
      command,
      parameters: {}
    };

    sendMessage(message);
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
            Status: {connectionStatus === 'Open' ? '🟢 Connected' : '🔴 Disconnected'}
          </Typography>
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
            onKeyPress={(e) => e.key === 'Enter' && handleSendCommand()}
          />
          <Button
            variant="contained"
            onClick={handleSendCommand}
            disabled={connectionStatus !== 'Open' || !command.trim()}
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