import { createContext } from "react";
import { AuthUser } from "../model/dto/user.dto";


export interface AuthContextType {
    user: AuthUser | null;
    isAuthenticated: boolean;
    loading: boolean;
    error: string | null;
    login: (credentials: {
        email: string;
        password: string;
    }) => Promise<AuthUser | null>;
    logout: () => void;
    updateUserData: (data: Partial<AuthUser>) => void;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);