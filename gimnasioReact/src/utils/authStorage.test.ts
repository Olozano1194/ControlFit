import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { getCsrfCookie } from './authStorage';

describe('getCsrfCookie', () => {
    const originalCookie = document.cookie;

    beforeEach(() => {
        // Clear all cookies by expiring them
        document.cookie.split(';').forEach(cookie => {
            const name = cookie.split('=')[0].trim();
            document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/`;
        });
    });

    afterEach(() => {
        // Restore original cookies
        document.cookie.split(';').forEach(cookie => {
            const name = cookie.split('=')[0].trim();
            document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/`;
        });
        // Re-set original cookies
        if (originalCookie) {
            originalCookie.split(';').forEach(cookie => {
                const [name, ...valueParts] = cookie.trim().split('=');
                const value = valueParts.join('=');
                document.cookie = `${name}=${value}; path=/`;
            });
        }
    });

    it('returns decoded value when cookie exists', () => {
        document.cookie = 'csrftoken=abc%2F123; path=/';

        const result = getCsrfCookie('csrftoken');

        expect(result).toBe('abc/123');
    });

    it('returns null when cookie does not exist', () => {
        document.cookie = 'other=cookie; path=/';

        const result = getCsrfCookie('csrftoken');

        expect(result).toBeNull();
    });

    it('returns null when cookie string is empty', () => {
        document.cookie = '';

        const result = getCsrfCookie('csrftoken');

        expect(result).toBeNull();
    });

    it('handles multiple cookies correctly', () => {
        // Set cookies individually (jsdom/browser limitation)
        document.cookie = 'session=abc; path=/';
        document.cookie = 'csrftoken=xyz%3Dvalue; path=/';
        document.cookie = 'theme=dark; path=/';

        const result = getCsrfCookie('csrftoken');

        expect(result).toBe('xyz=value');
    });

    it('returns null for partial name match', () => {
        document.cookie = 'csrftoken_extra=value; path=/';

        const result = getCsrfCookie('csrftoken');

        expect(result).toBeNull();
    });
});