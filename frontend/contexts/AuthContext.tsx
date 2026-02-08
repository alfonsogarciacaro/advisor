"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import {
    login as apiLogin,
    logout as apiLogout,
    setAuth,
    getAuthToken,
    setOnUnauthorized,
    refreshToken
} from "@/lib/api-client";
import { jwtDecode } from "jwt-decode";
import { useRouter } from "next/navigation";
import { LoginModal } from "@/components/auth/LoginModal";

// Define User type based on token payload
export interface User {
    username: string;
    role: string;
    // Add other fields from token if needed
}

interface AuthContextType {
    user: User | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    login: (username: string, password: string) => Promise<void>;
    logout: () => void;
    register: (username: string, password: string) => Promise<void>;
    showLoginModal: boolean;
    setShowLoginModal: (show: boolean) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [showLoginModal, setShowLoginModal] = useState(false);
    const router = useRouter();

    // Helper to decode token and set user
    const handleToken = (token: string | null) => {
        if (!token) {
            setUser(null);
            return;
        }
        try {
            const decoded: any = jwtDecode(token);
            // Check expiry
            if (decoded.exp * 1000 < Date.now()) {
                setUser(null);
                return;
            }
            setUser({
                username: decoded.sub,
                role: decoded.role || 'user'
            });
        } catch (e) {
            setUser(null);
        }
    };

    // Initialize auth state
    useEffect(() => {
        const initAuth = async () => {
            // Try to restore session via cookie refresh
            const token = getAuthToken();
            if (token) {
                handleToken(token);
            } else {
                // Try silent refresh
                try {
                    const success = await refreshToken();
                    if (success) {
                        handleToken(getAuthToken());
                    }
                } catch (e) {
                    // stays unauth
                }
            }
            setIsLoading(false);
        };

        initAuth();

        // Register callback for 401 events
        setOnUnauthorized(() => {
            setUser(null);
            setShowLoginModal(true);
        });
    }, []);

    const login = async (username: string, password: string) => {
        setIsLoading(true);
        try {
            const success = await apiLogin(username, password);
            if (success) {
                const token = getAuthToken();
                handleToken(token);
                setShowLoginModal(false);
            } else {
                throw new Error("Invalid username or password");
            }
        } finally {
            setIsLoading(false);
        }
    };

    const register = async (username: string, password: string) => {
        setIsLoading(true);
        try {
            const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
            const response = await fetch(`${API_URL}/api/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || "Registration failed");
            }

            // Auto login after register
            await login(username, password);

        } finally {
            setIsLoading(false);
        }
    };

    const logout = async () => {
        await apiLogout();
        setUser(null);
        router.push("/");
    };

    return (
        <AuthContext.Provider value={{
            user,
            isAuthenticated: !!user,
            isLoading,
            login,
            logout,
            register,
            showLoginModal,
            setShowLoginModal
        }}>
            {children}
            <LoginModal />
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
}
