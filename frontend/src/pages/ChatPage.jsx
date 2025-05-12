import React, { useState, useEffect, useRef, useReducer } from "react";
import { Button } from "../components/ui/button";
import { Send, FileDown, User, Bot, Loader2, BookmarkIcon } from "lucide-react";
import { chatApi, reportsApi } from "../services/api";
import { useApi } from "../hooks/useApi";
import { useWebSocket } from "../hooks/useWebSocket";
import { useParams, useNavigate } from "react-router-dom";
import ReactMarkdown from 'react-markdown';
import { GraphComponent } from "../components/ui/GraphComponent";
import { toast } from "../components/ui/use-toast";

// Code block component with syntax highlighting
const CodeBlock = ({ children, className }) => {
  // Extract language from className (format: language-*)
  const language = className ? className.replace('language-', '') : '';
  const codeRef = useRef(null);

  return (
    <div className="relative rounded-md overflow-hidden my-2">
      {language && (
        <div className="absolute top-0 right-0 bg-muted px-2 py-0.5 text-xs rounded-bl-md">
          {language}
        </div>
      )}
      <pre className={`${className} bg-muted p-3 overflow-x-auto text-sm`}>
        <code ref={codeRef} className="font-mono">
          {children}
        </code>
      </pre>
      <button
        onClick={() => {
          if (codeRef.current) {
            navigator.clipboard.writeText(codeRef.current.textContent);
          }
        }}
        className="absolute top-2 right-2 p-1 bg-background/80 hover:bg-background rounded-md text-xs"
        title="Copy code"
      >
        Copy
      </button>
    </div>
  );
};

const ChatMessage = ({ message, isUser, isFromCurrentSession, sessionId, workspaceId, onSaveReport }) => {
  // Determine message source and style
  const isMine = typeof isFromCurrentSession !== 'undefined' ? isFromCurrentSession : isUser;
  const isBotMessage = message.messageType === 'bot' || (!message.is_from_user && !message.messageType);
  const isUserMessage = message.messageType === 'user' || (message.is_from_user && !message.messageType);
  const [isSaving, setIsSaving] = useState(false);

  // Get display name from message or fallback to defaults
  const displayName = message.user || (isBotMessage ? "AI Assistant" : isMine ? "You" : "Other User");

  // Get message format
  const format = message.format || (isBotMessage ? "md" : "txt");

  // Choose the right styles
  const containerStyles = `mb-4 flex ${isMine ? "justify-end" : "justify-start"}`;
  const messageStyles = `max-w-[80%] rounded-lg p-4 ${isBotMessage ? "bg-secondary text-foreground" :
    isMine ? "bg-primary text-primary-foreground" :
      "bg-muted text-muted-foreground"
    }`;

  // Check if the message has visualizations
  const hasVisualizations = message.visualizations &&
    (message.visualizations.tables?.length > 0 || message.visualizations.graphs?.length > 0);

  // Handle save as report
  const handleSaveReport = async () => {
    if (!workspaceId || isSaving) return;

    setIsSaving(true);
    try {
      const reportTitle = `Chat response - ${new Date().toLocaleDateString()}`;
      const reportData = {
        title: reportTitle,
        description: "Generated from chat response",
        content: message.content,
        report_type: "chat_export",
        status: "Published",
        workspace_id: parseInt(workspaceId)
      };

      await onSaveReport(reportData, message.visualizations || {});
      toast({
        title: "Report saved",
        description: "Your report has been saved successfully",
        status: "success"
      });
    } catch (error) {
      console.error("Error saving report:", error);
      toast({
        title: "Error saving report",
        description: "There was an error saving your report. Please try again.",
        status: "error"
      });
    } finally {
      setIsSaving(false);
    }
  };

  // Render a simple table from the data
  const renderTable = (table) => {
    if (!table || !table.data || !Array.isArray(table.data) || table.data.length === 0) {
      return null;
    }

    // Ensure the headers row exists
    const headers = Array.isArray(table.data[0]) ? table.data[0] : [];

    return (
      <div className="my-3 overflow-x-auto" key={table.title || 'table'}>
        <h4 className="text-sm font-semibold mb-1">{table.title || 'Table'}</h4>
        {table.description && <p className="text-xs mb-2 opacity-70">{table.description}</p>}
        <table className="min-w-full border border-border">
          <thead>
            <tr className="bg-muted/30">
              {headers.map((header, i) => (
                <th key={i} className="border border-border p-1 text-xs font-medium">
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {table.data.slice(1).filter(row => Array.isArray(row)).map((row, rowIdx) => (
              <tr key={rowIdx} className={rowIdx % 2 === 0 ? 'bg-background' : 'bg-muted/20'}>
                {row.map((cell, cellIdx) => (
                  <td key={cellIdx} className="border border-border p-1 text-xs">
                    {String(cell || '')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  // Message content rendering - either markdown or plain text
  const renderContent = () => {
    if (format === "md" || isBotMessage) {
      return (
        <div className="markdown-content prose prose-sm dark:prose-invert max-w-none break-words">
          <ReactMarkdown
            components={{
              code({ node, inline, className, children, ...props }) {
                const match = /language-(\w+)/.exec(className || '');
                return !inline && match ? (
                  <CodeBlock className={className}>
                    {String(children).replace(/\n$/, '')}
                  </CodeBlock>
                ) : (
                  <code className={className} {...props}>
                    {children}
                  </code>
                );
              },
              // Override table to use our own styling
              table({ node, children, ...props }) {
                return (
                  <div className="overflow-x-auto my-3">
                    <table className="min-w-full border border-border" {...props}>
                      {children}
                    </table>
                  </div>
                );
              },
              thead({ node, children, ...props }) {
                return <thead className="bg-muted/30" {...props}>{children}</thead>;
              },
              tr({ node, children, ...props }) {
                return <tr className="hover:bg-muted/10" {...props}>{children}</tr>;
              },
              th({ node, children, ...props }) {
                return <th className="border border-border p-1.5 text-xs font-medium" {...props}>{children}</th>;
              },
              td({ node, children, ...props }) {
                return <td className="border border-border p-1.5 text-xs" {...props}>{children}</td>;
              }
            }}
          >
            {message.content}
          </ReactMarkdown>
        </div>
      );
    } else {
      return <div className="break-words">{message.content}</div>;
    }
  };

  // Render visualizations if available
  const renderVisualizations = () => {
    // Safely check if visualizations exist and contain data
    if (!hasVisualizations) return null;

    // Get tables and graphs safely
    const tables = (message.visualizations?.tables && Array.isArray(message.visualizations.tables))
      ? message.visualizations.tables
      : [];

    const graphs = (message.visualizations?.graphs && Array.isArray(message.visualizations.graphs))
      ? message.visualizations.graphs
      : [];

    // If no valid visualizations after checking, return null
    if (tables.length === 0 && graphs.length === 0) return null;

    return (
      <div className="mt-4 border-t border-border pt-3">
        <h3 className="text-sm font-medium mb-2">Visualizations</h3>

        {/* Render tables */}
        {tables.length > 0 && (
          <div className="tables-container">
            {tables.map((table, index) => renderTable(table) || null)}
          </div>
        )}

        {/* Render graphs */}
        {graphs.length > 0 && (
          <div className="graphs-container">
            {graphs.map((graph, index) => (
              <GraphComponent key={index} graph={graph} />
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className={containerStyles} data-uuid={message.uuid}>
      <div className={messageStyles}>
        <div className="mb-1 font-medium flex items-center gap-2">
          <span>{displayName}</span>
          {format && <span className="text-xs px-1.5 py-0.5 rounded bg-muted-foreground/20">{format}</span>}

          {/* Add Save Report button for AI messages */}
          {isBotMessage && workspaceId && (
            <Button
              variant="ghost"
              size="sm"
              className="ml-auto p-1 h-7"
              onClick={handleSaveReport}
              disabled={isSaving}
              title="Save as report"
            >
              {isSaving ? (
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
              ) : (
                <BookmarkIcon className="h-4 w-4" />
              )}
            </Button>
          )}

          {sessionId && !isMine && !isBotMessage && (
            <span className="ml-auto text-xs opacity-60">
              ({sessionId.substring(0, 6)})
            </span>
          )}
        </div>
        {renderContent()}
        {renderVisualizations()}
        <div className="mt-1 flex justify-between items-center text-xs opacity-60">
          {message.uuid && (
            <span className="text-xs opacity-60">ID: {message.uuid.substring(0, 8)}</span>
          )}
          {message.created_at && (
            <span className="ml-auto">
              {new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

// Chat state reducer
const chatReducer = (state, action) => {
  switch (action.type) {
    case 'SET_CHATS':
      return {
        ...state,
        chats: action.payload,
        chatsLoaded: true
      };
    case 'SET_CURRENT_CHAT':
      return {
        ...state,
        currentChatId: action.payload,
        messages: state.messagesByChat[action.payload] || []
      };
    case 'SET_MESSAGES':
      return {
        ...state,
        messages: action.payload,
        messagesByChat: {
          ...state.messagesByChat,
          [state.currentChatId]: action.payload
        }
      };
    case 'ADD_MESSAGE':
      // Check if the message with the same UUID already exists
      if (action.payload.uuid && state.messages.some(msg => msg.uuid === action.payload.uuid)) {
        // Skip adding duplicate message
        return state;
      }
      const updatedMessages = [...state.messages, action.payload];
      return {
        ...state,
        messages: updatedMessages,
        messagesByChat: {
          ...state.messagesByChat,
          [state.currentChatId]: updatedMessages
        }
      };
    case 'ADD_MESSAGES':
      // Filter out messages with UUIDs that already exist in the current state
      const uniqueMessages = action.payload.filter(
        newMsg => !newMsg.uuid || !state.messages.some(existingMsg => existingMsg.uuid === newMsg.uuid)
      );

      // If there are no unique messages to add, return the current state
      if (uniqueMessages.length === 0) {
        return state;
      }

      // First remove any temporary messages that have the same content as incoming messages
      const filteredExistingMessages = state.messages.filter(
        existingMsg => !(existingMsg.uuid && existingMsg.uuid.startsWith('temp-') &&
          uniqueMessages.some(newMsg => newMsg.content === existingMsg.content))
      );

      const newMessages = [...filteredExistingMessages, ...uniqueMessages];
      return {
        ...state,
        messages: newMessages,
        messagesByChat: {
          ...state.messagesByChat,
          [state.currentChatId]: newMessages
        }
      };
    case 'ADD_CHAT':
      return {
        ...state,
        chats: [action.payload, ...state.chats],
        currentChatId: action.payload.id,
        messages: [],
        messagesByChat: {
          ...state.messagesByChat,
          [action.payload.id]: []
        }
      };
    default:
      return state;
  }
};

// Initial chat state
const initialChatState = {
  chats: [],
  chatsLoaded: false,
  currentChatId: null,
  messages: [],
  messagesByChat: {}
};

export function ChatPage() {
  // Use reducer for chat state management
  const [chatState, dispatch] = useReducer(chatReducer, initialChatState);
  const { chats, chatsLoaded, currentChatId, messages } = chatState;

  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messageContainerRef = useRef(null);

  // Get URL parameters at the component top level
  const params = useParams();
  const navigate = useNavigate();
  const [workspaceId, setWorkspaceId] = useState(params.workspaceId || null);

  // If chatId is in URL params, use it
  useEffect(() => {
    if (params.chatId && params.chatId !== currentChatId) {
      dispatch({ type: 'SET_CURRENT_CHAT', payload: parseInt(params.chatId) });
    }

    // If workspaceId is in params, use it and store in localStorage
    if (params.workspaceId) {
      setWorkspaceId(params.workspaceId);
      localStorage.setItem('selectedWorkspaceId', params.workspaceId);
    } else if (!workspaceId && localStorage.getItem("selectedWorkspaceId")) {
      setWorkspaceId(localStorage.getItem("selectedWorkspaceId"));
    }
  }, [params.chatId, params.workspaceId, currentChatId, workspaceId]);

  // API hooks
  const {
    loading: chatsLoading,
    error: chatsError,
    execute: fetchChats
  } = useApi(chatApi.getAll);

  const {
    loading: creatingChat,
    error: createChatError,
    execute: createChat
  } = useApi(chatApi.create);

  const {
    loading: messagesLoading,
    error: messagesError,
    execute: fetchMessages
  } = useApi(chatApi.getMessages);

  // WebSocket for real-time messaging
  const {
    messages: wsMessages,
    sendMessage,
    connectionStatus,
    sessionId
  } = useWebSocket(
    (sid) => {
      if (currentChatId) {
        console.log(`Creating WebSocket connection for chat ${currentChatId}`);
        try {
          return chatApi.createWebSocketConnection(currentChatId, sid, workspaceId);
        } catch (error) {
          console.error('Error in WebSocket connection factory:', error);
          return null;
        }
      }
      console.log('No chat selected, not creating WebSocket connection');
      return null;
    },
    [currentChatId, workspaceId]
  );

  // Log connection status changes for debugging
  useEffect(() => {
    console.log(`WebSocket connection status: ${connectionStatus}`);
  }, [connectionStatus]);

  // Initial load of chats
  useEffect(() => {
    const loadInitialChats = async () => {
      try {
        const chatsData = await fetchChats(workspaceId);
        if (chatsData) {
          dispatch({ type: 'SET_CHATS', payload: chatsData });

          // If we have a current chat ID from URL params, load its messages
          if (params.chatId) {
            const chatId = parseInt(params.chatId);
            dispatch({ type: 'SET_CURRENT_CHAT', payload: chatId });
            const messagesData = await fetchMessages(chatId);
            if (messagesData) {
              dispatch({ type: 'SET_MESSAGES', payload: messagesData });
            }
          }
        }
      } catch (error) {
        console.error('Error loading initial data:', error);
      }
    };

    if (!chatsLoaded) {
      loadInitialChats();
    }
  }, [chatsLoaded, fetchChats, fetchMessages, params.chatId, workspaceId]);

  // Handle WebSocket messages
  useEffect(() => {
    if (wsMessages && Array.isArray(wsMessages) && wsMessages.length > 0) {
      console.log('Received WebSocket messages:', wsMessages);
      try {
        const processedMessages = wsMessages.map(msg => {
          // Ensure msg is an object before processing
          if (!msg || typeof msg !== 'object') {
            console.warn('Received invalid WebSocket message:', msg);
            return null;
          }

          // Create a base processed message
          let processedMsg = {
            ...msg,
            workspaceId: msg.workspaceId || workspaceId
          };

          // Process visualizations if they exist in the message
          if (msg.data && typeof msg.data === 'object') {
            // If visualizations are in msg.data.visualizations
            if (msg.data.visualizations) {
              processedMsg.visualizations = msg.data.visualizations;
            }

            // Handle case where visualizations might be directly in msg.data
            if (msg.data.tables || msg.data.graphs) {
              processedMsg.visualizations = {
                tables: msg.data.tables || [],
                graphs: msg.data.graphs || []
              };
            }
          }

          return processedMsg;
        }).filter(Boolean); // Remove any null messages

        if (processedMessages.length > 0) {
          dispatch({ type: 'ADD_MESSAGES', payload: processedMessages });
        }

        // Turn off loading when we receive a message from the bot
        const hasAiMessage = wsMessages.some(msg => msg && !msg.is_from_user);
        if (hasAiMessage) {
          setIsLoading(false);
        }
      } catch (error) {
        console.error('Error processing WebSocket messages:', error);
        setIsLoading(false);
      }
    }
  }, [wsMessages, workspaceId]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (messageContainerRef.current) {
      messageContainerRef.current.scrollTop = messageContainerRef.current.scrollHeight;
    }
  }, [messages]);

  // When a chat is selected, load its messages if they're not already in state
  const handleChatSelect = async (chatId) => {
    // Update URL to reflect the selected chat
    if (workspaceId) {
      navigate(`/workspace/${workspaceId}/chat/${chatId}`);
    } else {
      navigate(`/chat/${chatId}`);
    }

    dispatch({ type: 'SET_CURRENT_CHAT', payload: chatId });

    // Only fetch messages if we don't already have them in state
    if (!chatState.messagesByChat[chatId]) {
      const messagesData = await fetchMessages(chatId);
      if (messagesData) {
        dispatch({ type: 'SET_MESSAGES', payload: messagesData });
      }
    }
  };

  // Create a new chat
  const handleNewChat = async () => {
    const chatData = {
      title: "New Chat",
    };

    // If in a workspace context, associate the chat with the workspace
    if (workspaceId) {
      chatData.workspace_id = parseInt(workspaceId);
    }

    const newChat = await createChat(chatData);

    if (newChat) {
      dispatch({ type: 'ADD_CHAT', payload: newChat });

      // Update URL
      if (workspaceId) {
        navigate(`/workspace/${workspaceId}/chat/${newChat.id}`);
      } else {
        navigate(`/chat/${newChat.id}`);
      }
    }
  };

  // Send a message
  const handleSendMessage = () => {
    if (!input.trim() || isLoading) return;

    // Set loading state
    setIsLoading(true);

    // Clear input immediately for a responsive feel
    const messageContent = input;
    setInput("");

    // If no chat is selected, create one first
    if (!currentChatId) {
      const chatData = { title: "New Chat" };

      // If in a workspace context, associate the chat with the workspace
      if (workspaceId) {
        chatData.workspace_id = parseInt(workspaceId);
      }

      createChat(chatData).then((newChat) => {
        if (newChat) {
          dispatch({ type: 'ADD_CHAT', payload: newChat });

          // Update URL
          if (workspaceId) {
            navigate(`/workspace/${workspaceId}/chat/${newChat.id}`);
          } else {
            navigate(`/chat/${newChat.id}`);
          }

          setTimeout(() => {
            const visualizationOptions = {
              include_tables: true,
              include_graphs: true,
              preferred_graph_types: ["line", "bar", "pie"],
              max_tables: 5,
              max_graphs: 3
            };
            sendMessage(messageContent, visualizationOptions);
          }, 500); // Small delay to ensure WebSocket is connected
        } else {
          setIsLoading(false);
        }
      }).catch(() => {
        setIsLoading(false);
      });
      return;
    }

    // Send via WebSocket if available
    if (connectionStatus === 'connected') {
      // Include visualization options when sending the message
      const visualizationOptions = {
        include_tables: true,
        include_graphs: true,
        preferred_graph_types: ["line", "bar", "pie"],
        max_tables: 5,
        max_graphs: 3
      };

      // Send via WebSocket - loading state will be turned off when bot response is received
      sendMessage(messageContent, visualizationOptions);
    } else {
      setIsLoading(false);
      console.error('WebSocket connection not available');
    }
  };

  // API hooks for saving reports
  const {
    loading: savingReport,
    error: saveReportError,
    execute: saveReport
  } = useApi(reportsApi.create);

  // Function to handle saving a report
  const handleSaveReport = async (reportData, visualizations) => {
    try {
      // Create report with the basic data
      const newReport = await saveReport(reportData);

      // If there are visualizations, we could potentially save them as part of the report
      // This depends on how your backend handles report data storage

      return newReport;
    } catch (error) {
      console.error("Error saving report:", error);
      throw error;
    }
  };

  return (
    <div className="flex h-full flex-col">
      <div className="flex flex-1 gap-4 overflow-hidden">
        {/* Chat history sidebar */}
        <div className="w-52 overflow-y-auto rounded-md bg-card py-4 px-2">
          <h2 className="text-xl font-semibold pb-3 text-center">
            {workspaceId ? "Workspace Chats" : "Personal Chats"}
          </h2>

          <Button
            variant="default"
            size="sm"
            className="mb-3 w-full"
            onClick={handleNewChat}
            disabled={creatingChat}
          >
            New Chat
          </Button>

          <div className="space-y-2">
            {chatsLoading ? (
              <div className="text-center text-sm text-muted-foreground">Loading chats...</div>
            ) : chatsError ? (
              <div className="text-center text-sm text-destructive">Error loading chats</div>
            ) : chats.length > 0 ? (
              chats.map((chat) => (
                <div
                  key={chat.id}
                  className={`cursor-pointer rounded-md p-2 text-sm transition-colors ${currentChatId === chat.id
                    ? "bg-secondary"
                    : "hover:bg-secondary/50"
                    }`}
                  onClick={() => handleChatSelect(chat.id)}
                >
                  {chat.title}
                </div>
              ))
            ) : (
              <div className="text-center text-sm text-muted-foreground">
                No chats yet. Start a new conversation!
              </div>
            )}
          </div>
        </div>

        {/* Main chat area */}
        <div className="flex flex-1 flex-col rounded-md border bg-card">
          <div ref={messageContainerRef} className="flex-1 overflow-y-auto p-4">
            {currentChatId ? (
              messages.length > 0 ? (
                messages
                  .filter(message => !message.uuid || !message.uuid.startsWith('temp-'))
                  .map((message) => (
                    <ChatMessage
                      key={message.id || `msg-${Date.now()}-${Math.random()}`}
                      message={message}
                      isUser={message.is_from_user}
                      isFromCurrentSession={message.isFromCurrentSession}
                      sessionId={message.sessionId}
                      workspaceId={workspaceId}
                      onSaveReport={handleSaveReport}
                    />
                  ))
              ) : messagesLoading ? (
                <div className="flex h-full items-center justify-center">
                  <div className="text-center text-muted-foreground">
                    <div className="mb-2 h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent mx-auto"></div>
                    Loading messages...
                  </div>
                </div>
              ) : (
                <div className="flex h-full items-center justify-center">
                  <div className="text-center text-muted-foreground">
                    No messages yet. Start the conversation!
                  </div>
                </div>
              )
            ) : (
              <div className="flex h-full items-center justify-center">
                <div className="text-center text-muted-foreground">
                  Please select a chat or create a new one to start.
                </div>
              </div>
            )}
          </div>

          <div className="border-t p-4">
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Type your message here..."
                className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                disabled={isLoading || (!currentChatId && !workspaceId)}
              />
              <Button
                type="submit"
                size="icon"
                onClick={handleSendMessage}
                disabled={isLoading || !input.trim() || (!currentChatId && !workspaceId)}
              >
                {isLoading ? (
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
            </div>
            {isLoading && (
              <div className="mt-2 text-xs text-center text-muted-foreground">
                AI is thinking...
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 