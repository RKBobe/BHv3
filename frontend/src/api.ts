import axios from 'axios';

// Create an axios instance with a base URL matching our proxy
const api = axios.create({
  baseURL: '/api',
});

// Add a request interceptor to include the JWT token if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
