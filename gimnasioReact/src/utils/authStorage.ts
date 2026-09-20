const ACCESS_TOKEN_KEY = 'gym_access_token';
const CSRF_TOKEN_KEY   = 'gym_csrf_token';

// Access token en sessionStorage (sobrevive a recargas, se borra al cerrar navegador)
export const getAccessToken = (): string | null => {
  return sessionStorage.getItem(ACCESS_TOKEN_KEY);
};

export const setAccessToken = (token: string): void => {
  sessionStorage.setItem(ACCESS_TOKEN_KEY, token);
};

export const clearAccessToken = (): void => {
  sessionStorage.removeItem(ACCESS_TOKEN_KEY);
};

// CSRF token en sessionStorage — necesario en producción cross-origin (Vercel → Render)
// donde document.cookie no puede leer cookies del dominio del backend.
export const setCsrfToken = (token: string): void => {
  sessionStorage.setItem(CSRF_TOKEN_KEY, token);
};

export const getCsrfToken = (): string | null => {
  return sessionStorage.getItem(CSRF_TOKEN_KEY);
};

export const clearCsrfToken = (): void => {
  sessionStorage.removeItem(CSRF_TOKEN_KEY);
};

/**
 * Returns the CSRF token for use in X-CSRF-Token header.
 * Priority: sessionStorage (works cross-origin) → document.cookie (same-origin fallback).
 */
export const getCsrfCookie = (_name: string): string | null => {
  // 1. Prefer sessionStorage — reliable in cross-origin deployments
  const fromStorage = getCsrfToken();
  if (fromStorage) return fromStorage;

  // 2. Fallback: read from document.cookie (works only when frontend and
  //    backend share the same domain, e.g. local development)
  if (typeof document === 'undefined') return null;
  const cookies = document.cookie.split(';');
  for (const cookie of cookies) {
    const trimmed  = cookie.trim();
    const eqIndex  = trimmed.indexOf('=');
    if (eqIndex === -1) continue;
    const cookieName  = trimmed.substring(0, eqIndex);
    const cookieValue = trimmed.substring(eqIndex + 1);
    if (cookieName === 'csrftoken') {
      return decodeURIComponent(cookieValue);
    }
  }
  return null;
};