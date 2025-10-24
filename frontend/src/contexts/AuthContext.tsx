import React, { createContext, useContext, useState, ReactNode } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  type Body_login_login_access_token as AccessToken,
  LoginService,
  type UserPublic,
  type UserRegister,
  UsersService,
} from '@/client';

interface AuthContextType {
  user: UserPublic | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (data: AccessToken) => Promise<void>;
  register: (data: UserRegister) => Promise<void>;
  logout: () => void;
  error: string | null;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

const isLoggedIn = () => {
  return localStorage.getItem('access_token') !== null;
};

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [error, setError] = useState<string | null>(null);
  const queryClient = useQueryClient();

  // Fetch current user
  const { data: user, isLoading: userLoading } = useQuery<UserPublic | null, Error>({
    queryKey: ['currentUser'],
    queryFn: UsersService.readUserMe,
    enabled: isLoggedIn(),
    retry: false,
  });

  // Register mutation
  const registerMutation = useMutation({
    mutationFn: (data: UserRegister) =>
      UsersService.registerUser({ requestBody: data }),
    onSuccess: () => {
      window.location.href = '/login';
      setError(null);
    },
    onError: (err: any) => {
      setError(err.body?.detail || 'Registration failed');
    },
  });

  // Login mutation
  const loginMutation = useMutation({
    mutationFn: async (data: AccessToken) => {
      const response = await LoginService.loginAccessToken({
        formData: data,
      });
      localStorage.setItem('access_token', response.access_token);
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['currentUser'] });
      window.location.href = '/';
      setError(null);
    },
    onError: (err: any) => {
      setError(err.body?.detail || 'Login failed');
    },
  });

  const login = async (data: AccessToken) => {
    await loginMutation.mutateAsync(data);
  };

  const register = async (data: UserRegister) => {
    await registerMutation.mutateAsync(data);
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    queryClient.clear();
    window.location.href = '/login';
  };

  const clearError = () => setError(null);

  const value: AuthContextType = {
    user: user || null,
    isLoading: userLoading || loginMutation.isPending || registerMutation.isPending,
    isAuthenticated: !!user,
    login,
    register,
    logout,
    error,
    clearError,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
