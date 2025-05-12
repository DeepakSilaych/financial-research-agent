import { useState, useEffect, useRef, useCallback } from 'react';
import { v4 as uuidv4 } from 'uuid';

/**
 * Custom hook for WebSocket connections
 * @param {Function} connectionFactory - Function that creates a WebSocket connection
 * @param {Array} dependencies - Dependencies to re-create the connection
 * @returns {Object} - Object with messages, sendMessage, and connection status
 */
export const useWebSocket = (connectionFactory, dependencies = []) => {
  const [messages, setMessages] = useState([]);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const connectionRef = useRef(null);
  const sessionIdRef = useRef(null);

  // Generate a unique session ID if not already set
  if (!sessionIdRef.current) {
    sessionIdRef.current = uuidv4();
  }

  // Setup connection and event handlers
  useEffect(() => {
    // Create connection
    try {
      const sessionId = sessionIdRef.current;
      // Pass the session ID to the connection factory
      const connection = connectionFactory(sessionId);

      // If connection factory returned null, don't proceed with setup
      if (!connection) {
        setConnectionStatus('disconnected');
        return;
      }

      connectionRef.current = connection;
      setConnectionStatus('connecting');

      // Connection opened
      connection.socket.onopen = () => {
        setConnectionStatus('connected');
      };

      // Listen for messages
      connection.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('Raw WebSocket data received:', data);

          // Handle different message formats
          if (data.type === 'message') {
            // Standard format from our backend
            const messageSessionId = data.session_id;
            const isFromCurrentSession = !messageSessionId || messageSessionId === sessionId;

            const messageWithSessionInfo = {
              ...data.data,
              uuid: data.data.uuid || `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
              isFromCurrentSession,
              sessionId: messageSessionId || null,
              workspaceId: data.workspace_id || null,
              messageType: data.message_type || (data.data?.is_from_user ? 'user' : 'bot')
            };

            setMessages((prevMessages) => {
              // Skip adding if a message with the same UUID already exists or if it has a temp UUID
              if ((messageWithSessionInfo.uuid && prevMessages.some(msg => msg.uuid === messageWithSessionInfo.uuid)) ||
                (messageWithSessionInfo.uuid && messageWithSessionInfo.uuid.startsWith('temp-'))) {
                return prevMessages;
              }
              return [...prevMessages, messageWithSessionInfo];
            });
          } else if (data.content) {
            // Direct message format: {"content":"message","session_id":"id","workspace_id":"id"}
            const messageSessionId = data.session_id;
            const isFromCurrentSession = !messageSessionId || messageSessionId === sessionId;

            const messageWithSessionInfo = {
              id: Date.now(), // Generate a temporary ID
              uuid: data.uuid || `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
              user: isFromCurrentSession ? "You" : "Other User",
              format: data.format || "txt",
              content: data.content,
              is_from_user: messageSessionId === sessionId, // If from current session, it's a user message
              chat_id: null, // We might not have this info
              created_at: new Date().toISOString(),
              isFromCurrentSession,
              sessionId: messageSessionId || null,
              workspaceId: data.workspace_id || null,
              messageType: data.message_type || (messageSessionId === sessionId ? 'user' : 'other')
            };

            setMessages((prevMessages) => {
              // Skip adding if a message with the same UUID already exists or if it has a temp UUID
              if ((messageWithSessionInfo.uuid && prevMessages.some(msg => msg.uuid === messageWithSessionInfo.uuid)) ||
                (messageWithSessionInfo.uuid && messageWithSessionInfo.uuid.startsWith('temp-'))) {
                return prevMessages;
              }
              return [...prevMessages, messageWithSessionInfo];
            });
          }
        } catch (err) {
          console.error('Error parsing message', err, event.data);
        }
      };

      // Connection closed
      connection.socket.onclose = () => {
        setConnectionStatus('disconnected');
      };

      // Connection error
      connection.socket.onerror = (error) => {
        console.error('WebSocket error', error);
        setConnectionStatus('error');
      };

      // Cleanup on unmount
      return () => {
        if (connectionRef.current) {
          connectionRef.current.close();
        }
      };
    } catch (err) {
      console.error('Failed to establish WebSocket connection', err);
      setConnectionStatus('error');
    }
  }, dependencies); // eslint-disable-line react-hooks/exhaustive-deps

  // Send message function
  const sendMessage = useCallback((content) => {
    if (connectionRef.current && connectionStatus === 'connected') {
      try {
        connectionRef.current.sendMessage(content);
        return true;
      } catch (err) {
        console.error('Error sending message', err);
        return false;
      }
    }
    return false;
  }, [connectionStatus]);

  return {
    messages,
    sendMessage,
    connectionStatus,
    sessionId: sessionIdRef.current
  };
};

export default useWebSocket; 