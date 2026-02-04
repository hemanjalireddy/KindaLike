// Use localhost in development, relative URLs in production (Docker)
const API_BASE_URL = import.meta.env.MODE === 'development'
  ? 'http://localhost:5000'
  : '';

// Helper function to get auth token from localStorage
const getAuthToken = () => {
  return localStorage.getItem('token');
};

// Helper function to make API requests
const apiRequest = async (endpoint, options = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;
  const config = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  };

  try {
    const response = await fetch(url, config);

    // Check if response is JSON before parsing
    const contentType = response.headers.get('content-type');
    if (!contentType || !contentType.includes('application/json')) {
      throw new Error('Backend server is not responding. Please make sure the backend is running on port 5000.');
    }

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'Something went wrong');
    }

    return data;
  } catch (error) {
    console.error('API Error:', error);
    // If it's a network error or the error message is about JSON parsing
    if (error.message.includes('JSON') || error.name === 'TypeError') {
      throw new Error('Cannot connect to backend server. Please make sure it is running on port 5000.');
    }
    throw error;
  }
};

// Authentication APIs
export const signup = async (username, password) => {
  const data = await apiRequest('/api/auth/signup', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });

  // Store token and user info
  localStorage.setItem('token', data.access_token);
  localStorage.setItem('user', JSON.stringify(data.user));

  return data;
};

export const login = async (username, password) => {
  const data = await apiRequest('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });

  // Store token and user info
  localStorage.setItem('token', data.access_token);
  localStorage.setItem('user', JSON.stringify(data.user));

  return data;
};

export const logout = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
};

// Helper to check if user is authenticated
export const isAuthenticated = () => {
  return !!getAuthToken();
};

// Helper to get current user
export const getCurrentUser = () => {
  const userStr = localStorage.getItem('user');
  return userStr ? JSON.parse(userStr) : null;
};

// Chat APIs
export const sendChatMessage = async (messageData) => {
  const token = getAuthToken();

  if (!token) {
    throw new Error('No authentication token found');
  }

  const data = await apiRequest('/api/chat/message', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(messageData),
  });

  return data;
};

export const getChatSessions = async () => {
  const token = getAuthToken();

  if (!token) {
    throw new Error('No authentication token found');
  }

  const data = await apiRequest('/api/chat/sessions', {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  return data;
};

export const getSessionMessages = async (sessionId) => {
  const token = getAuthToken();

  if (!token) {
    throw new Error('No authentication token found');
  }

  const data = await apiRequest(`/api/chat/sessions/${sessionId}/messages`, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  return data;
};

export const createNewSession = async () => {
  const token = getAuthToken();

  if (!token) {
    throw new Error('No authentication token found');
  }

  const data = await apiRequest('/api/chat/sessions/new', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  return data;
};

// Phase 3: Preference Extraction APIs

export const searchRestaurants = async (name, location) => {
  const token = getAuthToken();

  if (!token) {
    throw new Error('No authentication token found');
  }

  const data = await apiRequest('/api/preferences/search-restaurant', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ name, location }),
  });

  // Backend returns an array of transformed restaurant objects
  return data;
};

export const submitOnboarding = async (restaurants) => {
  const token = getAuthToken();

  if (!token) {
    throw new Error('No authentication token found');
  }

  const data = await apiRequest('/api/preferences/onboarding', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ restaurants }),
  });

  return data;
};

export const startExtraction = async (forceRefresh = false) => {
  const token = getAuthToken();

  if (!token) {
    throw new Error('No authentication token found');
  }

  const data = await apiRequest('/api/preferences/extract', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ force_refresh: forceRefresh }),
  });

  return data;
};

export const getExtractionStatus = async () => {
  const token = getAuthToken();

  if (!token) {
    throw new Error('No authentication token found');
  }

  const data = await apiRequest('/api/preferences/extraction-status', {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  return data;
};

export const getQuestionnaire = async () => {
  const token = getAuthToken();

  if (!token) {
    throw new Error('No authentication token found');
  }

  const data = await apiRequest('/api/preferences/questionnaire', {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  return data;
};

export const submitQuestionnaire = async (answers) => {
  const token = getAuthToken();

  if (!token) {
    throw new Error('No authentication token found');
  }

  const data = await apiRequest('/api/preferences/questionnaire', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ answers }),
  });

  return data;
};

export const getPreferenceProfile = async () => {
  const token = getAuthToken();

  if (!token) {
    throw new Error('No authentication token found');
  }

  const data = await apiRequest('/api/preferences/profile', {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  return data;
};

// Legacy survey preferences (for backwards compatibility with Survey.jsx)
export const savePreferences = async (preferences) => {
  const token = getAuthToken();

  if (!token) {
    throw new Error('No authentication token found');
  }

  // Convert legacy survey format to questionnaire format
  const answers = Object.entries(preferences).map(([key, value]) => ({
    question_id: `legacy_${key}`,
    answer_value: value
  }));

  const data = await apiRequest('/api/preferences/questionnaire', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ answers }),
  });

  return data;
};

// Check if user has already completed preference extraction
export const hasCompletedPreferences = async () => {
  try {
    const status = await getExtractionStatus();
    return status.status === 'completed';
  } catch {
    return false;
  }
};
