import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { AppProvider } from './context/AppContext';
import Header from './components/Layout/Header';
import Footer from './components/Layout/Footer';
import Home from './pages/Home';
import Upload from './pages/Upload';
import Generate from './pages/Generate';
import Process from './pages/Process';
import Edit from './pages/Edit';
import Preview from './pages/Preview';
import Analyze from './pages/Analyze';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AppProvider>
        <Router>
          <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
            <Header />
            <main style={{ flex: 1, padding: '20px' }}>
              <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/upload" element={<Upload />} />
                <Route path="/generate" element={<Generate />} />
                <Route path="/process" element={<Process />} />
                <Route path="/edit" element={<Edit />} />
                <Route path="/preview" element={<Preview />} />
                <Route path="/analyze" element={<Analyze />} />
              </Routes>
            </main>
            <Footer />
          </div>
        </Router>
      </AppProvider>
    </ThemeProvider>
  );
}

export default App;