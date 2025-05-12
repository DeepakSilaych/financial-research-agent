// API URLs
const API_BASE_URL = 'http://localhost:8000';
const WS_BASE_URL = 'ws://localhost:8000';

// Helper function to get the auth token
const getToken = () => {
  const user = JSON.parse(localStorage.getItem('user') || 'null');
  return user ? user.access_token : null;
};

// Helper function for API requests with auth
const fetchWithAuth = async (url, options = {}) => {
  const token = getToken();

  const headers = {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` }),
    ...options.headers,
  };

  const config = {
    ...options,
    headers,
  };

  const response = await fetch(`${API_BASE_URL}${url}`, config);

  if (!response.ok) {
    // Handle specific HTTP errors
    if (response.status === 401) {
      // Clear user data on authentication error
      localStorage.removeItem('user');
      window.location.href = '/login';
      throw new Error('Session expired. Please login again.');
    }

    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Error ${response.status}: ${response.statusText}`);
  }

  // Handle empty responses for 204 No Content
  if (response.status === 204) {
    return null;
  }

  return response.json();
};

// Authentication API
export const authApi = {
  // Register a new user
  register: async (userData) => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Error ${response.status}: ${response.statusText}`);
      }

      // Store the username to display after login
      localStorage.setItem('registered_username', userData.username);

      return response.json();
    } catch (error) {
      throw error;
    }
  },

  // Login user
  login: async (credentials) => {
    const formData = new URLSearchParams();
    formData.append('username', credentials.email);
    formData.append('password', credentials.password);

    const response = await fetch(`${API_BASE_URL}/auth/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Error ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();

    // Try to get the username from registration
    const registeredUsername = localStorage.getItem('registered_username') || '';

    // Store in localStorage with username
    const user = {
      access_token: data.access_token,
      token_type: data.token_type,
      username: registeredUsername || credentials.email.split('@')[0],
    };

    // Clear the registered username after using it
    localStorage.removeItem('registered_username');

    localStorage.setItem('user', JSON.stringify(user));

    return user;
  },

  // Logout user (client-side only)
  logout: () => {
    localStorage.removeItem('user');
  },
};

// Workspace API
export const workspaceApi = {
  // Get all workspaces
  getAll: async () => {
    return fetchWithAuth('/workspaces');
  },

  // Get a specific workspace
  getById: async (id) => {
    return fetchWithAuth(`/workspaces/${id}`);
  },

  // Create a new workspace
  create: async (workspace) => {
    return fetchWithAuth('/workspaces', {
      method: 'POST',
      body: JSON.stringify(workspace),
    });
  },

  // Update a workspace
  update: async (id, workspace) => {
    return fetchWithAuth(`/workspaces/${id}`, {
      method: 'PUT',
      body: JSON.stringify(workspace),
    });
  },

  // Delete a workspace
  delete: async (id) => {
    return fetchWithAuth(`/workspaces/${id}`, {
      method: 'DELETE',
    });
  },

  // Add a member to a workspace
  addMember: async (workspaceId, userId) => {
    return fetchWithAuth(`/workspaces/${workspaceId}/members`, {
      method: 'POST',
      body: JSON.stringify({ user_id: userId }),
    });
  },

  // Remove a member from a workspace
  removeMember: async (workspaceId, userId) => {
    return fetchWithAuth(`/workspaces/${workspaceId}/members/${userId}`, {
      method: 'DELETE',
    });
  },
};

// Chat API
export const chatApi = {
  // Get all chats
  getAll: async (workspaceId = null) => {
    const url = workspaceId ? `/chats?workspace_id=${workspaceId}` : '/chats';
    return fetchWithAuth(url);
  },

  // Get a specific chat
  getById: async (id) => {
    return fetchWithAuth(`/chats/${id}`);
  },

  // Create a new chat
  create: async (chat) => {
    return fetchWithAuth('/chats', {
      method: 'POST',
      body: JSON.stringify(chat),
    });
  },

  // Delete a chat
  delete: async (id) => {
    return fetchWithAuth(`/chats/${id}`, {
      method: 'DELETE',
    });
  },

  // Get messages for a chat
  getMessages: async (chatId) => {
    return fetchWithAuth(`/chats/${chatId}/messages`);
  },

  // Send a message (REST API)
  sendMessage: async (chatId, message) => {
    return fetchWithAuth(`/chats/${chatId}/messages`, {
      method: 'POST',
      body: JSON.stringify(message),
    });
  },

  // Create WebSocket connection
  createWebSocketConnection: (chatId, sessionId = null, workspaceId = null) => {
    // Check for required parameters
    if (!chatId) {
      console.error('chatId is required for WebSocket connection');
      return null;
    }

    try {
      const token = getToken();
      if (!token) {
        console.error('Not authenticated');
        return null;
      }

      // Build WebSocket URL with query parameters
      let wsUrl = `${WS_BASE_URL}/chats/ws/${chatId}?token=${token}`;

      // Add session ID if provided
      if (sessionId) {
        wsUrl += `&session_id=${sessionId}`;
      }

      // Add workspace ID if provided
      if (workspaceId) {
        wsUrl += `&workspace_id=${workspaceId}`;
      }

      const socket = new WebSocket(wsUrl);

      return {
        socket,

        // Send message via WebSocket
        sendMessage: (content, visualizationOptions = {}) => {
          if (socket.readyState === WebSocket.OPEN) {
            // Basic message data
            const messageData = {
              content,
              format: "txt",
              session_id: sessionId,
              workspace_id: workspaceId,
              visualization_options: {
                include_tables: true,
                include_graphs: true,
                ...visualizationOptions
              }
            };

            console.log('Sending WebSocket message:', messageData);
            socket.send(JSON.stringify(messageData));
          } else {
            throw new Error('WebSocket connection is not open');
          }
        },

        // Close WebSocket connection
        close: () => {
          if (socket && socket.readyState !== WebSocket.CLOSED) {
            socket.close();
          }
        },
      };
    } catch (error) {
      console.error('Error creating WebSocket connection:', error);
      return null;
    }
  },
};

// Upload API
export const uploadApi = {
  // Get all uploads, optionally filtered by workspace
  getAll: async (workspaceId = null) => {
    const url = workspaceId ? `/uploads?workspace_id=${workspaceId}` : '/uploads';
    return fetchWithAuth(url);
  },

  // Get a specific upload
  getById: async (id) => {
    return fetchWithAuth(`/uploads/${id}`);
  },

  // Upload a file
  upload: async (file, description = '', workspaceId = null) => {
    const token = getToken();

    const formData = new FormData();
    formData.append('file', file);

    if (description) {
      formData.append('description', description);
    }

    if (workspaceId) {
      formData.append('workspace_id', workspaceId);
    }

    const response = await fetch(`${API_BASE_URL}/uploads`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Error ${response.status}: ${response.statusText}`);
    }

    return response.json();
  },

  // Delete an upload
  delete: async (id) => {
    return fetchWithAuth(`/uploads/${id}`, {
      method: 'DELETE',
    });
  },

  // Get download URL
  getDownloadUrl: async (id) => {
    const data = await fetchWithAuth(`/uploads/download/${id}`);
    return `${API_BASE_URL}${data.download_url}`;
  },
};

// Reports API
export const reportsApi = {
  // Get all reports
  getAll: async (workspaceId = null, filters = {}) => {
    let queryParams = Object.entries(filters)
      .filter(([_, value]) => value !== null && value !== undefined)
      .map(([key, value]) => `${key}=${encodeURIComponent(value)}`);

    // Add workspace_id to query params if provided
    if (workspaceId) {
      queryParams.push(`workspace_id=${workspaceId}`);
    }

    const queryString = queryParams.join('&');
    const url = queryString ? `/reports?${queryString}` : '/reports';
    return fetchWithAuth(url);
  },

  // Get a specific report
  getById: async (id) => {
    return fetchWithAuth(`/reports/${id}`);
  },

  // Create a new report
  create: async (report) => {
    return fetchWithAuth('/reports', {
      method: 'POST',
      body: JSON.stringify(report),
    });
  },

  // Update a report
  update: async (id, report) => {
    return fetchWithAuth(`/reports/${id}`, {
      method: 'PUT',
      body: JSON.stringify(report),
    });
  },

  // Delete a report
  delete: async (id) => {
    return fetchWithAuth(`/reports/${id}`, {
      method: 'DELETE',
    });
  },

  // Generate a report
  generate: async (type, documentIds) => {
    return fetchWithAuth('/reports/generate', {
      method: 'POST',
      body: JSON.stringify({
        report_type: type,
        document_ids: documentIds
      }),
    });
  },

  // Get documents that can be used for report generation
  getDocuments: async () => {
    return fetchWithAuth('/uploads');
  },
};

// Export all APIs
export default {
  auth: authApi,
  workspaces: workspaceApi,
  chats: chatApi,
  uploads: uploadApi,
  reports: reportsApi,
}; 