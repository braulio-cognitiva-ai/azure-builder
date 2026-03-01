'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';

interface User {
  id: string;
  name: string;
  email: string;
}

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check for stored auth on mount
    const token = localStorage.getItem('azure_builder_token');
    const storedUser = localStorage.getItem('azure_builder_user');
    
    if (token && storedUser) {
      setUser(JSON.parse(storedUser));
    }
    setIsLoading(false);
  }, []);

  const login = async (email: string, password: string) => {
    // Demo: accept any credentials
    const demoUser: User = {
      id: '1',
      name: email.split('@')[0],
      email,
    };
    
    const fakeToken = 'demo-jwt-token-' + Date.now();
    localStorage.setItem('azure_builder_token', fakeToken);
    localStorage.setItem('azure_builder_user', JSON.stringify(demoUser));
    setUser(demoUser);
  };

  const register = async (name: string, email: string, password: string) => {
    // Demo: accept any credentials
    const demoUser: User = {
      id: '1',
      name,
      email,
    };
    
    const fakeToken = 'demo-jwt-token-' + Date.now();
    localStorage.setItem('azure_builder_token', fakeToken);
    localStorage.setItem('azure_builder_user', JSON.stringify(demoUser));
    setUser(demoUser);
  };

  const logout = () => {
    localStorage.removeItem('azure_builder_token');
    localStorage.removeItem('azure_builder_user');
    setUser(null);
  };

  if (isLoading) {
    return null;
  }

  return (
    <AuthContext.Provider value={{ user, login, register, logout, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
