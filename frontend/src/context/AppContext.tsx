import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface AppContextType {
  sessionId: string | null;
  setSessionId: (id: string | null) => void;
  apiStatus: string;
  setApiStatus: (status: string) => void;
  theme: 'light' | 'dark';
  toggleTheme: () => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
};

interface AppProviderProps {
  children: ReactNode;
}

export const AppProvider: React.FC<AppProviderProps> = ({ children }) => {
  const [sessionId, setSessionIdState] = useState<string | null>(null);
  const [apiStatus, setApiStatus] = useState<string>('Checking...');
  const [theme, setTheme] = useState<'light' | 'dark'>('light');

  // Load session ID from localStorage on mount
  useEffect(() => {
    const savedSessionId = localStorage.getItem('videoEditor_sessionId');
    if (savedSessionId) {
      setSessionIdState(savedSessionId);
    }

    const savedTheme = localStorage.getItem('videoEditor_theme') as 'light' | 'dark';
    if (savedTheme) {
      setTheme(savedTheme);
    }
  }, []);

  const setSessionId = (id: string | null) => {
    setSessionIdState(id);
    if (id) {
      localStorage.setItem('videoEditor_sessionId', id);
    } else {
      localStorage.removeItem('videoEditor_sessionId');
    }
  };

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    localStorage.setItem('videoEditor_theme', newTheme);
  };

  return (
    <AppContext.Provider value={{
      sessionId,
      setSessionId,
      apiStatus,
      setApiStatus,
      theme,
      toggleTheme,
    }}>
      {children}
    </AppContext.Provider>
  );
};