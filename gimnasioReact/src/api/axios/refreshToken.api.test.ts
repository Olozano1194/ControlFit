import { describe, it, expect, vi, beforeEach } from 'vitest';
import { axiosPrivate } from '../axios/axios.private';

// Mock axiosPrivate
vi.mock('../axios/axios.private', () => ({
    axiosPrivate: {
        get: vi.fn(),
    },
}));

// Import after mock
import { verifyToken } from './refreshToken.api';

describe('verifyToken', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('calls GET /token/verify/ and returns valid response', async () => {
        const mockResponse = { data: { valid: true, exp: 1234567890 } };
        vi.mocked(axiosPrivate.get).mockResolvedValue(mockResponse);

        const result = await verifyToken();

        expect(axiosPrivate.get).toHaveBeenCalledWith('/token/verify/');
        expect(result).toEqual({ valid: true, exp: 1234567890 });
    });

    it('throws when token is invalid (401 response)', async () => {
        const error = new Error('Unauthorized');
        error.response = { status: 401 };
        vi.mocked(axiosPrivate.get).mockRejectedValue(error);

        await expect(verifyToken()).rejects.toThrow('Unauthorized');
        expect(axiosPrivate.get).toHaveBeenCalledWith('/token/verify/');
    });

    it('throws on network error', async () => {
        const error = new Error('Network Error');
        error.request = {};
        vi.mocked(axiosPrivate.get).mockRejectedValue(error);

        await expect(verifyToken()).rejects.toThrow('Network Error');
    });
});