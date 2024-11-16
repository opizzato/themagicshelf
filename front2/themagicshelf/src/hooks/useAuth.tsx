"use client"

import { createContext, useContext, useMemo } from "react";
import { useLocalStorage } from "./useLocalStorage";
import { useRouter } from "next/navigation";

const AuthContext = createContext({
    token: null,
    user: null
});

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
    const [user, setUser] = useLocalStorage('user', null);
    const [token, setToken] = useLocalStorage('token', null);
    const router = useRouter();

    const login = async (data: { user: any, token: string }) => {
        setUser(data.user);
        setToken(data.token);
        router.push('/')
    };

    const logout = async () => {
        setUser(null);
        setToken(null);
        router.push('/login')
    };

    const setBodyProfile = async (body_profile: any) => {
        setUser({...user, body_profile: body_profile});
    };
    
    const value = useMemo(
        () => ({
            user,
            token,
            login,
            logout,
            setBodyProfile,
        }),
        [user, token]
    );
    return (
        <AuthContext.Provider value={value as any}>{children}</AuthContext.Provider>
    );
}

export const useAuth = () => {
    return useContext(AuthContext);
};
