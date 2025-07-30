import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box } from '@mui/material';
import { AppProvider, useAppContext } from './context/AppContext';
import Header from './components/Layout/Header';
import Footer from './components/Layout/Footer';
import Home from './pages/Home';
import Upload from './pages/Upload';
import Generate from './pages/Generate';
import Process from './pages/Process';
import Edit from './pages/Edit';
import Preview from './pages/Preview';
import Analyze from './pages/Analyze';

const AppContent: React.FC = () => {
  const { theme } = useAppContext();

  const muiTheme = createTheme({
    palette: {
      mode: theme,
    },
  });

  return (
    <ThemeProvider theme={muiTheme}>
      <CssBaseline />
      <Router>
        <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
          <Header />
          <Box component="main" sx={{ flexGrow: 1, py: 3 }}>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/upload" element={<Upload />} />
              <Route path="/generate" element={<Generate />} />
              <Route path="/process" element={<Process />} />
              <Route path="/edit" element={<Edit />} />
              <Route path="/preview" element={<Preview />} />
              <Route path="/analyze" element={<Analyze />} />
            </Routes>
          </Box>
          <Footer />
        </Box>
      </Router>
    </ThemeProvider>
  );
};

const App: React.FC = () => {
  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  );
};

export default App;