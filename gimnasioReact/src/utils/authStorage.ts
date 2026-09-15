const ACCESS_TOKEN_KEY = 'gym_access_token';

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

/**
 * Reads a cookie by name and returns its URL-decoded value.
 * Returns null if the cookie is not found.
 */
export const getCsrfCookie = (name: string): string | null => {
  if (typeof document === 'undefined') return null;
  
  const cookies = document.cookie.split(';');
  
  for (const cookie of cookies) {
    const trimmed = cookie.trim();
    const eqIndex = trimmed.indexOf('=');
    if (eqIndex === -1) continue;
    
    const cookieName = trimmed.substring(0, eqIndex);
    const cookieValue = trimmed.substring(eqIndex + 1);
    
    if (cookieName === name) {
      return decodeURIComponent(cookieValue);
    }
  }
  
  return null;
};