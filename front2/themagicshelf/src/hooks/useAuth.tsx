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
    const [apiKey, setApiKey] = useLocalStorage('api_key', null);
    const [runId, setRunId] = useLocalStorage('run_id', null);
    const router = useRouter();

    const login = async (data: { user: any, token: string, api_key: string }) => {
        setUser(data.user);
        setToken(data.token);
        setApiKey(data.user.api_key);
        setRunId(data.user.run_id);
        router.push('/')
    };

    const logout = async () => {
        setUser(null);
        setToken(null);
        setApiKey(null);
        setRunId(null);
        router.push('/login')
    };

    const value = useMemo(
        () => ({
            user,
            token,
            apiKey,
            runId,
            login,
            logout,
            setApiKey,
            setToken
        }),
        [user, token, apiKey, runId]
    );
    return (
        <AuthContext.Provider value={value as any}>{children}</AuthContext.Provider>
    );
}

export const useAuth = () => {
    return useContext(AuthContext);
};
