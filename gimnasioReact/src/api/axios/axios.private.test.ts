import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';

// Mock all authStorage exports
vi.mock('../../utils/authStorage', () => ({
    getAccessToken: vi.fn(),
    setAccessToken: vi.fn(),
    clearAccessToken: vi.fn(),
    getCsrfCookie: vi.fn(),
}));

import { getCsrfCookie } from '../../utils/authStorage';
import { getAccessToken } from '../../utils/authStorage';
import { axiosPrivate } from './axios.private';

describe('axiosPrivate CSRF interceptor', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        // Reset interceptors by recreating the axios instance
        // We test by checking the request config passed to the interceptor
    });

    const createMockConfig = (method: string, headers: Record<string, string> = {}) => ({
        method,
        headers,
        url: '/test',
    });

    it('adds X-CSRF-Token header for POST requests', async () => {
        vi.mocked(getCsrfCookie).mockReturnValue('abc123');
        
        const config = createMockConfig('post');
        
        // Get the request interceptor
        const interceptor = axiosPrivate.interceptors.request.handlers[0];
        const result = await interceptor.fulfilled(config);
        
        expect(getCsrfCookie).toHaveBeenCalledWith('csrftoken');
        expect(result.headers['X-CSRF-Token']).toBe('abc123');
    });

    it('adds X-CSRF-Token header for PUT requests', async () => {
        vi.mocked(getCsrfCookie).mockReturnValue('abc123');
        
        const config = createMockConfig('put');
        
        const interceptor = axiosPrivate.interceptors.request.handlers[0];
        const result = await interceptor.fulfilled(config);
        
        expect(result.headers['X-CSRF-Token']).toBe('abc123');
    });

    it('adds X-CSRF-Token header for PATCH requests', async () => {
        vi.mocked(getCsrfCookie).mockReturnValue('abc123');
        
        const config = createMockConfig('patch');
        
        const interceptor = axiosPrivate.interceptors.request.handlers[0];
        const result = await interceptor.fulfilled(config);
        
        expect(result.headers['X-CSRF-Token']).toBe('abc123');
    });

    it('adds X-CSRF-Token header for DELETE requests', async () => {
        vi.mocked(getCsrfCookie).mockReturnValue('abc123');
        
        const config = createMockConfig('delete');
        
        const interceptor = axiosPrivate.interceptors.request.handlers[0];
        const result = await interceptor.fulfilled(config);
        
        expect(result.headers['X-CSRF-Token']).toBe('abc123');
    });

    it('does NOT add X-CSRF-Token header for GET requests', async () => {
        vi.mocked(getCsrfCookie).mockReturnValue('abc123');
        
        const config = createMockConfig('get');
        
        const interceptor = axiosPrivate.interceptors.request.handlers[0];
        const result = await interceptor.fulfilled(config);
        
        expect(getCsrfCookie).not.toHaveBeenCalled();
        expect(result.headers['X-CSRF-Token']).toBeUndefined();
    });

    it('sends empty X-CSRF-Token when cookie is missing', async () => {
        vi.mocked(getCsrfCookie).mockReturnValue(null);
        
        const config = createMockConfig('post');
        
        const interceptor = axiosPrivate.interceptors.request.handlers[0];
        const result = await interceptor.fulfilled(config);
        
        expect(result.headers['X-CSRF-Token']).toBe('');
    });

    it('preserves existing headers', async () => {
        vi.mocked(getCsrfCookie).mockReturnValue('abc123');
        
        const config = createMockConfig('post', { 'Custom-Header': 'custom-value' });
        
        const interceptor = axiosPrivate.interceptors.request.handlers[0];
        const result = await interceptor.fulfilled(config);
        
        expect(result.headers['Custom-Header']).toBe('custom-value');
        expect(result.headers['X-CSRF-Token']).toBe('abc123');
    });

    it('handles case-insensitive method names', async () => {
        vi.mocked(getCsrfCookie).mockReturnValue('abc123');
        
        const config = createMockConfig('Post');
        
        const interceptor = axiosPrivate.interceptors.request.handlers[0];
        const result = await interceptor.fulfilled(config);
        
        expect(result.headers['X-CSRF-Token']).toBe('abc123');
    });
});