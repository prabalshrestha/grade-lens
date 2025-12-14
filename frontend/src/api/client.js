import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Assignments
export const listAssignments = () => apiClient.get('/api/assignments');
export const getAssignment = (id) => apiClient.get(`/api/assignments/${id}`);
export const deleteAssignment = (id) => apiClient.delete(`/api/assignments/${id}`);
export const saveAssignmentConfig = (id, config) => 
  apiClient.post(`/api/assignments/${id}/config`, { config });

// File uploads
export const uploadAssignmentFiles = (formData) =>
  apiClient.post('/api/assignments/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });

export const generateConfig = (formData) =>
  apiClient.post('/api/assignments/generate-config', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });

// Submissions
export const uploadSubmissions = (id, formData) =>
  apiClient.post(`/api/assignments/${id}/submissions`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });

export const listSubmissions = (id) =>
  apiClient.get(`/api/assignments/${id}/submissions`);

// Grading
export const gradeAssignment = (id, gradingMode = 'full') =>
  apiClient.post(`/api/assignments/${id}/grade?grading_mode=${gradingMode}`);

export const getResults = (id, gradingMode = 'full') =>
  apiClient.get(`/api/assignments/${id}/results?grading_mode=${gradingMode}`);

export const downloadResults = (id, format = 'csv', gradingMode = 'full') =>
  `${API_BASE_URL}/api/assignments/${id}/results/download?format=${format}&grading_mode=${gradingMode}`;

export default apiClient;

