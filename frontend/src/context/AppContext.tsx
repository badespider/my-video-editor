import React, { createContext, useContext, useReducer, ReactNode } from 'react';

interface AppState {
  currentSessionId: string | null;
  apiStatus: 'online' | 'offline' | 'checking';
  user: any | null;
  theme: 'light' | 'dark';
}

type AppAction =
  | { type: 'SET_SESSION_ID'; payload: string | null }
  | { type: 'SET_API_STATUS'; payload: 'online' | 'offline' | 'checking' }
  | { type: 'SET_USER'; payload: any | null }
  | { type: 'SET_THEME'; payload: 'light' | 'dark' };

const initialState: AppState = {
  currentSessionId: localStorage.getItem('currentSessionId'),
  apiStatus: 'checking',
  user: null,
  theme: 'light',
};

const AppContext = createContext<{
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
} | null>(null);

const appReducer = (state: AppState, action: AppAction): AppState => {
  switch (action.type) {
    case 'SET_SESSION_ID':
      if (action.payload) {
        localStorage.setItem('currentSessionId', action.payload);
      } else {
        localStorage.removeItem('currentSessionId');
      }
      return { ...state, currentSessionId: action.payload };
    case 'SET_API_STATUS':
      return { ...state, apiStatus: action.payload };
    case 'SET_USER':
      return { ...state, user: action.payload };
    case 'SET_THEME':
      return { ...state, theme: action.payload };
    default:
      return state;
  }
};

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, initialState);

  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  );
};

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
};