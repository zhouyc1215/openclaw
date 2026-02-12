#!/usr/bin/env node

import WebSocket from 'ws';

const ws = new WebSocket('ws://127.0.0.1:18789');

ws.on('open', () => {
  console.log('Connected to gateway');
  
  // Send wake request
  const request = {
    jsonrpc: '2.0',
    id: 'manual-wake',
    method: 'wake',
    params: {
      mode: 'now',
      text: 'Execute pending cron tasks'
    }
  };
  
  console.log('Sending wake request:', JSON.stringify(request));
  ws.send(JSON.stringify(request));
});

ws.on('message', (data) => {
  console.log('Received:', data.toString());
  ws.close();
});

ws.on('error', (error) => {
  console.error('WebSocket error:', error);
  process.exit(1);
});

ws.on('close', () => {
  console.log('Connection closed');
  process.exit(0);
});

setTimeout(() => {
  console.log('Timeout - closing connection');
  ws.close();
  process.exit(1);
}, 5000);
