/**
 * API client for SmartHire backend
 */
import axios from 'axios';

// Create axios instance
const api = axios.create({
  baseURL: `/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Unauthorized - clear token and redirect to login
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  signup: (data) => api.post('/auth/signup', data),
  login: (data) => api.post('/auth/login', data),
  getCurrentUser: () => api.get('/auth/me'),
};

// Jobs API
export const jobsAPI = {
  create: (data) => api.post('/jobs', data),
  list: (params) => api.get('/jobs', { params }),
  get: (id) => api.get(`/jobs/${id}`),
  update: (id, data) => api.put(`/jobs/${id}`, data),
  delete: (id) => api.delete(`/jobs/${id}`),
  getStats: (id) => api.get(`/jobs/${id}/stats`),
  getLeaderboard: (id, limit = 10) => api.get(`/jobs/${id}/leaderboard`, { params: { limit } }),
};

// Resumes API
export const resumesAPI = {
  upload: (jobId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/jobs/${jobId}/resumes`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  list: (jobId, params) => api.get(`/jobs/${jobId}/resumes`, { params }),
  get: (id) => api.get(`/jobs/resumes/${id}`),
  getParsedData: (id) => api.get(`/resumes/${id}/parsed-data`),
  download: (id) => api.get(`/jobs/resumes/${id}/download`, { responseType: 'blob' }),
  delete: (id) => api.delete(`/jobs//resumes/${id}`),
};

// Parsing API
export const parsingAPI = {
  parseResume: (id) => api.post(`/resumes/${id}/parse`),
  parseAll: (jobId) => api.post(`/jobs/${jobId}/parse-all`),
};

// Scoring API
export const scoringAPI = {
  scoreResume: (id) => api.post(`/resumes/${id}/score`),
  scoreAll: (jobId) => api.post(`/jobs/${jobId}/score-all`),
};

// RAG Query API
export const ragAPI = {
  queryJob: (jobId, data) => api.post(`/jobs/${jobId}/query`, data),
  queryAll: (data) => api.post('/query', data),
  getVectorStats: (jobId) => api.get(`/jobs/${jobId}/vector-stats`),
};

export default api;
