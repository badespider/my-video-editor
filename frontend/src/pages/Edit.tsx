import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Button,
  TextField,
  Paper,
  Grid,
  Card,
  CardContent,
  Chip,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Send,
  ContentCut,
  Save,
  Refresh,
  Settings,
  PlayArrow,
  Stop,
} from '@mui/icons-material';
import { useAppContext } from '../context/AppContext';
import { useWebSocket } from '../hooks/useWebSocket';
import ApiService from '../services/api';
import ErrorAlert from '../components/Common/ErrorAlert';
import LoadingSpinner from '../components/Common/LoadingSpinner';
import { SessionInfo, EditCommand, TrimRequest } from '../types/api';

const Edit: React.FC = () => {
  const { state } = useAppContext();
  const [sessionId, setSessionId] = useState(state.currentSessionId || '');
  const [sessionInfo, setSessionInfo] = useState<SessionInfo | null>(null);
  const [command, setCommand] = useState('');
  const [messages, setMessages] = useState<Array<{ type: 'sent' | 'received'; content: string; timestamp: Date }>>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [trimDialogOpen, setTrimDialogOpen] = useState(false);
  const [trimStart, setTrimStart] = useState('00:00:00');
  const [trimEnd, setTrimEnd] = useState('00:00:30');

  const wsUrl = sessionId ? `ws://localhost:8000/ws/edit/${sessionId}` : '';
  const { sendMessage, lastMessage, connectionStatus, error: wsError } = useWebSocket(wsUrl, !!sessionId);

  useEffect(() => {
    if (sessionId) {
      loadSessionInfo();
    }
  }, [sessionId]);

  useEffect(() => {
    if (lastMessage) {
      setMessages(prev => [...prev, {
        type: 'received',
        content: JSON.stringify(lastMessage, null, 2),
        timestamp: new Date(),
      }]);
    }
  }, [lastMessage]);

  const loadSessionInfo = async () => {
    try {
      setLoading(true);
      const info = await ApiService.getSessionInfo(sessionId);
      setSessionInfo(info);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load session info');
    } finally {
      setLoading(false);
    }
  };

  const handleSendCommand = () => {
    if (!command.trim() || connectionStatus !== 'Open') return;

    const message = {
      type: 'command',
      command: command.trim(),
      timestamp: new Date().toISOString(),
    };

    sendMessage(message);
    setMessages(prev => [...prev, {
      type: 'sent',
      content: command,
      timestamp: new Date(),
    }]);
    setCommand('');
  };

  const handleTrimVideo = async () => {
    if (!sessionId) return;

    try {
      setLoading(true);
      const trimRequest: TrimRequest = {
        start_time: trimStart,
        end_time: trimEnd,
        preview_only: true,
        quality: 'medium',
      };

      await ApiService.trimVideo(sessionId, trimRequest);
      setTrimDialogOpen(false);
      await loadSessionInfo(); // Refresh session info
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to trim video');
    } finally {
      setLoading(false);
    }
  };

  const handleApplyBatchEdits = async () => {
    if (!sessionId) return;

    const edits: EditCommand[] = [
      {
        command: 'trim',
        parameters: { start_time: trimStart, end_time: trimEnd },
      },
    ];

    try {
      setLoading(true);
      await ApiService.applyEdits(sessionId, edits);
      await loadSessionInfo();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to apply edits');
    } finally {
      setLoading(false);
    }
  };

  const getConnectionStatusColor = (status: string) => {
    switch (status) {
      case 'Open':
        return 'success';
      case 'Connecting':
        return 'warning';
      case 'Closed':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Edit Session
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Real-time video editing with AI assistance and WebSocket communication.
      </Typography>

      {error && <ErrorAlert error={error} onClose={() => setError(null)} />}
      {wsError && <ErrorAlert error={wsError} title="WebSocket Error" />}

      <Grid container spacing={4}>
        {/* Session Setup */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Session Setup
              </Typography>
              
              <TextField
                fullWidth
                label="Session ID"
                value={sessionId}
                onChange={(e) => setSessionId(e.target.value)}
                sx={{ mb: 2 }}
                placeholder="Enter session ID or upload a video first"
              />

              <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                <Chip
                  label={`WebSocket: ${connectionStatus}`}
                  color={getConnectionStatusColor(connectionStatus) as any}
                  size="small"
                />
              </Box>

              {sessionInfo && (
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Session Info
                  </Typography>
                  <Typography variant="body2">
                    <strong>File:</strong> {sessionInfo.filename}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Edits:</strong> {sessionInfo.edits_count}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Status:</strong> {sessionInfo.finalized ? 'Finalized' : 'Active'}
                  </Typography>
                </Box>
              )}

              <Box sx={{ mt: 2, display: 'flex', gap: 1, flexDirection: 'column' }}>
                <Button
                  variant="outlined"
                  startIcon={<Refresh />}
                  onClick={loadSessionInfo}
                  disabled={!sessionId || loading}
                  size="small"
                >
                  Refresh Info
                </Button>
                
                <Button
                  variant="outlined"
                  startIcon={<ContentCut />}
                  onClick={() => setTrimDialogOpen(true)}
                  disabled={!sessionId}
                  size="small"
                >
                  Trim Video
                </Button>
                
                <Button
                  variant="outlined"
                  startIcon={<Settings />}
                  onClick={handleApplyBatchEdits}
                  disabled={!sessionId || loading}
                  size="small"
                >
                  Apply Batch Edits
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Real-time Chat Interface */}
        <Grid item xs={12} md={8}>
          <Card sx={{ height: 600, display: 'flex', flexDirection: 'column' }}>
            <CardContent sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
              <Typography variant="h6" gutterBottom>
                Real-time Editing Commands
              </Typography>

              {/* Messages Area */}
              <Paper
                sx={{
                  flexGrow: 1,
                  p: 2,
                  mb: 2,
                  overflow: 'auto',
                  bgcolor: 'grey.50',
                  maxHeight: 400,
                }}
              >
                {messages.length === 0 ? (
                  <Typography variant="body2" color="text.secondary" textAlign="center">
                    No messages yet. Try sending a command like "trim video from 10s to 30s"
                  </Typography>
                ) : (
                  <List dense>
                    {messages.map((message, index) => (
                      <ListItem
                        key={index}
                        sx={{
                          flexDirection: 'column',
                          alignItems: message.type === 'sent' ? 'flex-end' : 'flex-start',
                          mb: 1,
                        }}
                      >
                        <Paper
                          sx={{
                            p: 1,
                            maxWidth: '80%',
                            bgcolor: message.type === 'sent' ? 'primary.light' : 'grey.200',
                            color: message.type === 'sent' ? 'primary.contrastText' : 'text.primary',
                          }}
                        >
                          <Typography variant="body2">
                            {message.content}
                          </Typography>
                          <Typography variant="caption" sx={{ opacity: 0.7 }}>
                            {message.timestamp.toLocaleTimeString()}
                          </Typography>
                        </Paper>
                      </ListItem>
                    ))}
                  </List>
                )}
              </Paper>

              {/* Command Input */}
              <Box sx={{ display: 'flex', gap: 1 }}>
                <TextField
                  fullWidth
                  label="Enter editing command"
                  placeholder="e.g., trim video from 10s to 30s, enhance brightness, add fade effect"
                  value={command}
                  onChange={(e) => setCommand(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSendCommand();
                    }
                  }}
                  disabled={connectionStatus !== 'Open'}
                  multiline
                  maxRows={3}
                />
                <IconButton
                  color="primary"
                  onClick={handleSendCommand}
                  disabled={!command.trim() || connectionStatus !== 'Open'}
                  sx={{ alignSelf: 'flex-end' }}
                >
                  <Send />
                </IconButton>
              </Box>

              <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
                WebSocket Status: {connectionStatus}
                {connectionStatus === 'Open' && ' - Ready to send commands'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Trim Dialog */}
      <Dialog open={trimDialogOpen} onClose={() => setTrimDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Trim Video</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
            <TextField
              label="Start Time"
              value={trimStart}
              onChange={(e) => setTrimStart(e.target.value)}
              placeholder="00:00:00"
              helperText="Format: HH:MM:SS"
            />
            <TextField
              label="End Time"
              value={trimEnd}
              onChange={(e) => setTrimEnd(e.target.value)}
              placeholder="00:00:30"
              helperText="Format: HH:MM:SS"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTrimDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleTrimVideo} variant="contained" disabled={loading}>
            {loading ? 'Trimming...' : 'Trim Video'}
          </Button>
        </DialogActions>
      </Dialog>

      {loading && <LoadingSpinner message="Processing..." />}
    </Container>
  );
};

export default Edit;