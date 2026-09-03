import { useEffect, useState, useCallback } from 'react';
import { AuthContext } from './AuthContext';
import { login as loginApi } from '../api/users/authUser.api';
import { getAccessToken, setAccessToken, clearAccessToken } from '../utils/authStorage';
import { axiosPublic } from '../api/axios/axios.public';
import { refreshAccessToken } from '../api/axios/refreshToken.api';
import type { LoginUserDto } from '../model/dto/user.dto';
import type { UserRole } from '../components/sideBar/components/SideBarMenus';
import { AuthUser } from '../model/dto/user.dto';
import { getUserProfile } from '../api/users/users.api';

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    const initAuth = async () => {
      const token = getAccessToken();

      if (!token) {
        // Sin access token: intentar restaurar la sesión desde la cookie HttpOnly
        try {
          const newToken = await refreshAccessToken();
          setAccessToken(newToken);
          setIsAuthenticated(true);
          await loadUser();
        } catch {
          // Sin sesión válida: dejar loading en false (ProtectRoute redirige a /login)
          setLoading(false);
        }
        return;
      }

      setIsAuthenticated(true);
      await loadUser();
    };
    initAuth();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadUser = async (): Promise<AuthUser | null> => {
    setLoading(true);
    setError(null);

    try {
      const data = await getUserProfile();

      const avatarUrl = data.user.avatar instanceof File ? URL.createObjectURL(data.user.avatar) : data.user.avatar ?? '';

      let rolesArray: UserRole[] = [];

      if (data.user.roles) {
        const rawRoles = Array.isArray(data.user.roles)
          ? data.user.roles
          : [data.user.roles];

        rolesArray = rawRoles.filter((role): role is UserRole =>
          role === 'admin' || role === 'recepcion' || role === 'superadmin'
        );
      }

      const authUser: AuthUser = {
        name: data.user.name,
        lastname: data.user.lastname,
        email: data.user.email,
        avatar: avatarUrl,
        roles: rolesArray,
        gimnasio_id: data.user.gimnasio,
        gimnasio_name: data.user.gimnasio_name,
        must_change_password: data.user.must_change_password
      };
      
      // Si must_change_password y NO estamos en /cambiar-password → redirect
      if (authUser.must_change_password && !window.location.pathname.includes('/cambiar-password')) {
        window.location.href = '/cambiar-password';
        return null;
      }
      
      setUser(authUser);
      return authUser;

    } catch {
      setError('Datos de usuarios no encontrados');
      return null;
    } finally {
      setLoading(false);
    }
  };

  const performLogout = useCallback(async () => {
    try {
      // El server blacklistea el refresh (cookie HttpOnly) y limpia la cookie
      await axiosPublic.post('/auth/logout/');
    } catch {
      // Logout idempotente: continuar aunque falle el blacklist en el server
    }
    
    clearAccessToken();
    setUser(null);
    setIsAuthenticated(false);
  }, []);

  const login = async (credentials: LoginUserDto): Promise<AuthUser | null> => {
    setLoading(true);
    setError(null);

    try {
      const accessToken = await loginApi(credentials);
      setAccessToken(accessToken);
      setIsAuthenticated(true);
      const loadedUser = await loadUser();
      return loadedUser;
    } catch (error) {
      setError('Usuario o contraseña incorrectos');
      throw error;            
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    performLogout();
  };

  // Actualizar datos del usuario en el contexto (para reflejar cambios en el Header)
  const updateUserData = useCallback((data: Partial<AuthUser>) => {
    setUser(prev => prev ? { ...prev, ...data } : null);
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, isAuthenticated, loading, error, login, logout, updateUserData }}
    >
      {children}
    </AuthContext.Provider>
  );
};