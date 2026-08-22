import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

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
}));
vi.mock('../api/axios/refreshToken.api', () => ({
    refreshAccessToken: vi.fn(() => Promise.reject(new Error('no session'))),
}));

import { AuthProvider } from './AuthProvider';
import { useAuth } from './useAuth';
import { getUserProfile } from '../api/users/users.api';
import { login as loginApi } from '../api/users/authUser.api';
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

describe('AuthProvider.login', () => {
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
