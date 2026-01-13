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
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'Something went wrong');
    }

    return data;
  } catch (error) {
    console.error('API Error:', error);
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

// Preferences APIs
export const savePreferences = async (preferences) => {
  const token = getAuthToken();

  if (!token) {
    throw new Error('No authentication token found');
  }

  const data = await apiRequest('/api/preferences/', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(preferences),
  });

  return data;
};

export const getPreferences = async () => {
  const token = getAuthToken();

  if (!token) {
    throw new Error('No authentication token found');
  }

  const data = await apiRequest('/api/preferences/', {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  return data;
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
