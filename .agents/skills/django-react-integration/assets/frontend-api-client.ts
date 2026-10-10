// gimnasioReact/src/api/client.ts

import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { getCsrfToken, setCsrfToken } from './csrf';

// ============================================
// TYPES
// ============================================

export interface ApiError {
  detail?: string;
  errors?: Record<string, string[]>;
  statusCode: number;
}

export interface User {
  id: string;
  email: string;
  name: string;
  gym_id: string | null;
  is_superuser: boolean;
}

export interface LoginResponse {
  user: User;
}

export interface RefreshResponse {
  access: string;
  refresh?: string; // rotated
}

export interface CsrfResponse {
  csrfToken: string;
}


// ============================================
// AXIOS INSTANCE
// ============================================

const api: AxiosInstance = axios.create({
  baseURL: '/api',
  withCredentials: true, // CRITICAL: sends/receives cookies
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});


// ============================================
// REQUEST INTERCEPTOR
// ============================================

let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value: unknown) => void;
  reject: (reason: unknown) => void;
}> = [];

const processQueue = (error: AxiosError | null, token: string | null = null) => {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error);
    } else {
      resolve(token);
    }
  });
  failedQueue = [];
};

api.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    // Attach CSRF token for mutating requests
    const method = config.method?.toUpperCase();
    if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method || '')) {
      const csrfToken = getCsrfToken();
      if (csrfToken) {
        config.headers['X-CSRFToken'] = csrfToken;
      }
    }
    
    // Attach Gym ID if available
    const gymId = localStorage.getItem('gymId') || sessionStorage.getItem('gymId');
    if (gymId) {
      config.headers['X-Gym-ID'] = gymId;
    }
    
    return config;
  },
  (error) => Promise.reject(error)
);


// ============================================
// RESPONSE INTERCEPTOR (auto-refresh on 401)
// ============================================

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiError>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    
    // Only handle 401 on non-auth endpoints
    if (
      error.response?.status === 401 &&
      !originalRequest.url?.includes('/auth/') &&
      !originalRequest._retry
    ) {
      if (isRefreshing) {
        // Queue this request until refresh completes
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then(() => api(originalRequest))
          .catch((err) => Promise.reject(err));
      }
      
      originalRequest._retry = true;
      isRefreshing = true;
      
      try {
        // Call refresh endpoint
        const response = await axios.post<RefreshResponse>(
          '/api/auth/refresh/',
          {},
          { withCredentials: true }
        );
        
        // Update CSRF token from response headers if present
        const newCsrf = response.headers['x-csrftoken'];
        if (newCsrf) {
          setCsrfToken(newCsrf);
        }
        
        processQueue(null, response.data.access);
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError as AxiosError, null);
        
        // Redirect to login on refresh failure
        if (typeof window !== 'undefined') {
          window.location.href = '/login?expired=1';
        }
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }
    
    return Promise.reject(error);
  }
);


// ============================================
// AUTH API
// ============================================

export const authApi = {
  /**
   * GET /api/auth/csrf/
   * Fetch CSRF token before first mutation
   */
  getCsrfToken: async (): Promise<string> => {
    const response = await api.get<CsrfResponse>('/auth/csrf/');
    setCsrfToken(response.data.csrfToken);
    return response.data.csrfToken;
  },
  
  /**
   * POST /api/auth/login/
   * Body: { email, password }
   * Sets HttpOnly cookies automatically
   */
  login: async (email: string, password: string): Promise<LoginResponse> => {
    const response = await api.post<LoginResponse>('/auth/login/', { email, password });
    return response.data;
  },
  
  /**
   * POST /api/auth/refresh/
   * Reads refresh from cookie, returns new access + sets cookies
   */
  refresh: async (): Promise<RefreshResponse> => {
    const response = await api.post<RefreshResponse>('/auth/refresh/');
    return response.data;
  },
  
  /**
   * POST /api/auth/logout/
   * Clears cookies, blacklists refresh
   */
  logout: async (): Promise<void> => {
    await api.post('/auth/logout/');
  },
  
  /**
   * GET /api/auth/me/
   * Returns current user (validates access token)
   */
  me: async (): Promise<User> => {
    const response = await api.get<User>('/auth/me/');
    return response.data;
  },
};


// ============================================
// GENERIC API HELPERS
// ============================================

export const apiClient = {
  get: <T>(url: string, params?: Record<string, unknown>) => 
    api.get<T>(url, { params }).then((r) => r.data),
  
  post: <T>(url: string, data?: unknown) => 
    api.post<T>(url, data).then((r) => r.data),
  
  put: <T>(url: string, data?: unknown) => 
    api.put<T>(url, data).then((r) => r.data),
  
  patch: <T>(url: string, data?: unknown) => 
    api.patch<T>(url, data).then((r) => r.data),
  
  delete: <T>(url: string) => 
    api.delete<T>(url).then((r) => r.data),
};


// ============================================
// ERROR HANDLING HELPER
// ============================================

export function handleApiError(error: unknown): ApiError {
  if (axios.isAxiosError(error)) {
    const response = error.response;
    return {
      detail: response?.data?.detail || error.message,
      errors: response?.data?.errors,
      statusCode: response?.status || 0,
    };
  }
  return {
    detail: error instanceof Error ? error.message : 'Error desconocido',
    statusCode: 0,
  };
}


export default api;