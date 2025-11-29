// API configuration that adapts to environment
const getApiBaseUrl = (): string => {
  // In Docker, use the service name; in development, use localhost
  if (import.meta.env.VITE_ENVIRONMENT === 'development') {
    return import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
  }
  // In Docker container, use the service name
  return 'http://backend:8000/api';
};

export const API_CONFIG = {
  BASE_URL: getApiBaseUrl(),
  ENDPOINTS: {
    UPLOAD: '/upload',
    VERSION: '/version',
    ANALYSIS: (sessionId: string) => `/analysis/${sessionId}`,
    STATUS: (sessionId: string) => `/status/${sessionId}`,
  },
  TIMEOUT: 30000, // 30 seconds
};

console.log('API Base URL:', API_CONFIG.BASE_URL);
console.log('Environment:', import.meta.env.VITE_ENVIRONMENT);