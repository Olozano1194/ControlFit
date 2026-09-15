import { render, screen, waitFor, fireEvent, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('../api/users/users.api', () => ({
    getUserProfile: vi.fn(),
}));
vi.mock('../api/users/authUser.api', () => ({
    login: vi.fn(),
}));
vi.mock('../utils/authStorage', () => ({
    getAccessToken: vi.fn(() => null),
    setAccessToken: vi.fn(),
    clearAccessToken: vi.fn(),
    getCsrfCookie: vi.fn(),
}));
vi.mock('../api/axios/refreshToken.api', () => ({
    refreshAccessToken: vi.fn(() => Promise.reject(new Error('no session'))),
    verifyToken: vi.fn(),
}));

import { AuthProvider } from './AuthProvider';
import { useAuth } from './useAuth';
import { getUserProfile } from '../api/users/users.api';
import { login as loginApi } from '../api/users/authUser.api';
import { verifyToken, refreshAccessToken } from '../api/axios/refreshToken.api';
import { getAccessToken, setAccessToken, clearAccessToken } from '../utils/authStorage';
import type { AuthUser } from '../model/dto/user.dto';

const profileResponse = {
    user: {
        name: 'Super',
        lastname: 'Admin',
        email: 'super@test.com',
        avatar: '',
        roles: 'superadmin',
        gimnasio: null,
        gimnasio_name: null,
    },
} as unknown as Awaited<ReturnType<typeof getUserProfile>>;

const Probe = ({ onResult }: { onResult: (user: AuthUser | null) => void }) => {
    const { login } = useAuth();
    return (
        <button
            onClick={async () => {
                const loggedUser = await login({ email: 'super@test.com', password: 'pass123' });
                onResult(loggedUser);
            }}
        >
            do-login
        </button>
    );
};

describe('AuthProvider', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        vi.mocked(getAccessToken).mockReturnValue(null);
    });

    describe('verifyToken on mount', () => {
        it('calls verifyToken when access token exists', async () => {
            vi.mocked(getAccessToken).mockReturnValue('valid-token');
            vi.mocked(verifyToken).mockResolvedValue({ valid: true, exp: 1234567890 });
            vi.mocked(getUserProfile).mockResolvedValue(profileResponse);

            render(<AuthProvider><div>App</div></AuthProvider>);

            await waitFor(() => {
                expect(verifyToken).toHaveBeenCalledTimes(1);
            });
        });

        it('redirects to login when verifyToken returns invalid', async () => {
            vi.mocked(getAccessToken).mockReturnValue('expired-token');
            vi.mocked(verifyToken).mockResolvedValue({ valid: false });
            const originalLocation = window.location;
            delete (window as any).location;
            window.location = { href: '', assign: vi.fn() } as any;

            render(<AuthProvider><div>App</div></AuthProvider>);

            await waitFor(() => {
                expect(window.location.href).toBe('/login');
            });

            window.location = originalLocation;
        });

        it('redirects to login when verifyToken throws 401', async () => {
            vi.mocked(getAccessToken).mockReturnValue('expired-token');
            const error = new Error('Unauthorized');
            error.response = { status: 401 };
            vi.mocked(verifyToken).mockRejectedValue(error);
            const originalLocation = window.location;
            delete (window as any).location;
            window.location = { href: '', assign: vi.fn() } as any;

            render(<AuthProvider><div>App</div></AuthProvider>);

            await waitFor(() => {
                expect(window.location.href).toBe('/login');
            });

            window.location = originalLocation;
        });

        it('does NOT redirect on network error', async () => {
            vi.mocked(getAccessToken).mockReturnValue('valid-token');
            const error = new Error('Network Error');
            error.request = {};
            vi.mocked(verifyToken).mockRejectedValue(error);
            const originalLocation = window.location;
            delete (window as any).location;
            window.location = { href: '/dashboard', assign: vi.fn() } as any;

            render(<AuthProvider><div>App</div></AuthProvider>);

            await waitFor(() => {
                expect(window.location.href).toBe('/dashboard');
            });

            window.location = originalLocation;
        });

        it('does NOT call verifyToken when no access token', async () => {
            vi.mocked(getAccessToken).mockReturnValue(null);
            vi.mocked(refreshAccessToken).mockRejectedValue(new Error('no session'));

            render(<AuthProvider><div>App</div></AuthProvider>);

            await waitFor(() => {
                expect(verifyToken).not.toHaveBeenCalled();
            });
        });
    });

    describe('login', () => {
        it('login devuelve el usuario cargado con sus roles (para decidir redirección)', async () => {
            vi.mocked(loginApi).mockResolvedValue('token-fake');
            vi.mocked(getUserProfile).mockResolvedValue(profileResponse);

            let capturedUser: AuthUser | null = null;
            render(
                <AuthProvider>
                    <Probe onResult={(user) => { capturedUser = user; }} />
                </AuthProvider>
            );

            fireEvent.click(screen.getByText('do-login'));

            await waitFor(() => {
                expect(capturedUser).not.toBeNull();
                expect(capturedUser?.email).toBe('super@test.com');
                expect(capturedUser?.roles).toContain('superadmin');
            });
        });
    });
});
