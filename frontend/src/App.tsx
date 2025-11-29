import * as React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Box } from '@mui/material';
import ThemeProvider from './providers/ThemeProvider';
import Navbar from './components/NavBar';
import FileUpload from './components/FileUpload';
import AnalysisDashboard from './components/AnalysisDashboard';

import './App.css';

function App() {
  return (
    <ThemeProvider>
      <Router>
        <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
          <Navbar />
          <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
            <Routes>
              <Route path="/" element={<FileUpload />} />
              <Route path="/analysis/:sessionId" element={<AnalysisDashboard />} />
            </Routes>
          </Box>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;
