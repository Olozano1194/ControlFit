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