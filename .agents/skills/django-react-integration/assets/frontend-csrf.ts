// gimnasioReact/src/api/csrf.ts

// CSRF token management for frontend

let csrfToken: string | null = null;

export function getCsrfToken(): string | null {
  // 1. Check memory
  if (csrfToken) return csrfToken;
  
  // 2. Check cookie (fallback)
  if (typeof document !== 'undefined') {
    const cookies = document.cookie.split(';');
    for (const cookie of cookies) {
      const [name, value] = cookie.trim().split('=');
      if (name === 'csrftoken') {
        csrfToken = value;
        return value;
      }
    }
  }
  
  return null;
}

export function setCsrfToken(token: string): void {
  csrfToken = token;
}

export function clearCsrfToken(): void {
  csrfToken = null;
}

/**
 * Initialize CSRF token on app startup
 * Call once in App.tsx or main.tsx
 */
export async function initializeCsrf(api: { get: (url: string) => Promise<{ data: { csrfToken: string } }> }): Promise<string> {
  try {
    const response = await api.get('/auth/csrf/');
    setCsrfToken(response.data.csrfToken);
    return response.data.csrfToken;
  } catch {
    // If CSRF endpoint fails, continue without it
    // Django will reject mutations without CSRF, but this allows graceful degradation
    return '';
  }
}