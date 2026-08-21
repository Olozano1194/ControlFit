import axios, { AxiosError, InternalAxiosRequestConfig, AxiosResponse } from 'axios';
import { getAccessToken, setAccessToken, clearAccessToken } from '../../utils/authStorage';
import { refreshAccessToken } from './refreshToken.api';

const baseURL = import.meta.env.MODE === 'development' 
              ? import.meta.env.VITE_API_URL_DEV
              : import.meta.env.VITE_API_URL_PROD;

// Cliente público (sin token) - para login/register
export const axiosPublic = axios.create({   
    baseURL,
});

// Cliente privado (con token) - para endpoints protegidos
export const axiosPrivate = axios.create({   
    baseURL,
    withCredentials: true,  // Importante para enviar cookies
});

// ─── JWT helpers ───────────────────────────────────────────────
const decodeJwt = (token: string): Record<string, unknown> | null => {
  try {
    const payload = token.split('.')[1];
    return JSON.parse(atob(payload));
  } catch {
    return null;
  }
};

const isTokenExpiringSoon = (token: string, marginMs = 5 * 60 * 1000): boolean => {
  const decoded = decodeJwt(token);
  if (!decoded || typeof decoded.exp !== 'number') return false;
  return decoded.exp * 1000 - Date.now() < marginMs;
};

// ─── Refresh queue ────────────────────────────────────────────
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (error: Error) => void;
}> = [];

const processQueue = (error: Error | null, token: string | null = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token!);
    }
  });
  failedQueue = [];
};

// Request interceptor: refresh proactivo + access token
axiosPrivate.interceptors.request.use(
  async (config) => {
    const token = getAccessToken();
    
    if (token) {
      // Si el token está por expirar (menos de 5 min), refrescarlo antes
      if (isTokenExpiringSoon(token)) {
        try {
          const newToken = await refreshAccessToken();
          setAccessToken(newToken);
          config.headers.Authorization = `Bearer ${newToken}`;
          return config;
        } catch {
          // Si falla el refresh, igual mandamos el token actual
          // y el response interceptor se encarga del 401
          config.headers.Authorization = `Bearer ${token}`;
          return config;
        }
      }
      
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: manejar 401 y auto-refresh
axiosPrivate.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Si el error no es 401 o ya se intentó retry, rechazar
    if (error.response?.status !== 401 || originalRequest._retry) {
      return Promise.reject(error);
    }

    if (isRefreshing) {
      // Ya hay un refresh en progreso, agregar este request a la cola
      return new Promise((resolve, reject) => {
        failedQueue.push({
          resolve: (token: string) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            resolve(axiosPrivate(originalRequest));
          },
          reject: (err: Error) => {
            reject(err);
          },
        });
      });
    }

    originalRequest._retry = true;
    isRefreshing = true;

    try {
      // Intentar refresh
      const newAccessToken = await refreshAccessToken();
      setAccessToken(newAccessToken);
      
      // Procesar cola de requests pendientes
      processQueue(null, newAccessToken);
      
      // Reintentar request original con nuevo token
      if (originalRequest.headers) {
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
      }
      return axiosPrivate(originalRequest);
    } catch (refreshError) {
      // Refresh falló, limpiar todo
      processQueue(refreshError as Error, null);
      
      // Limpiar tokens
      clearAccessToken();
      
      // Redirigir a login
      window.location.href = '/login';
      
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  }
);

// ─── Silent refresh ────────────────────────────────────────────
// Refresca el access token cada 20 min para que no expire
// mientras el usuario tenga la app abierta, incluso si no hace requests.
let silentRefreshInterval: ReturnType<typeof setInterval> | null = null;

export const startSilentRefresh = (intervalMs = 20 * 60 * 1000): void => {
  stopSilentRefresh();
  silentRefreshInterval = setInterval(async () => {
    const token = getAccessToken();
    if (!token) return; // No hay sesión activa

    try {
      const newToken = await refreshAccessToken();
      setAccessToken(newToken);
    } catch {
      // Si falla el refresh silencioso, no hacemos nada.
      // El response interceptor se encargará si llega un request real.
    }
  }, intervalMs);
};

export const stopSilentRefresh = (): void => {
  if (silentRefreshInterval !== null) {
    clearInterval(silentRefreshInterval);
    silentRefreshInterval = null;
  }
};