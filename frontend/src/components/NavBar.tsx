import * as React from 'react';
import {
  AppBar,
  Toolbar,
  Box,
  Chip,
  useTheme,
  useMediaQuery,
  Typography, // Needed for VersionDisplay adjustments if inline
} from '@mui/material';
import {
  Home
} from '@mui/icons-material';

import { useNavigate, useLocation } from 'react-router-dom';
// Import the VersionDisplay component
import { VersionDisplay } from './VersionDisplay'; // Adjust path as needed

const navItems = [
  { label: "IRT AnalyzeR", short: "IRT", icon: <Home />, path: "/" },
];

const Navbar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));

  return (
    <AppBar
      position="static"
      elevation={2}
      sx={{
        backgroundColor: "white",
        color: "text.primary",
        borderBottom: `1px solid ${theme.palette.divider}`,
      }}
    >
      <Toolbar>
        {/* VERSION DISPLAY (LEFT ALIGNED) */}
        {/* We use the version display and wrap it to adjust for the navbar's vertical padding */}
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <VersionDisplay />
        </Box>

        {/* TOP NAV BUTTONS (RIGHT ALIGNED) */}
        {/* ml: "auto" pushes this box to the far right */}
        <Box sx={{ display: "flex", gap: 1, ml: "auto" }}>
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;

            return (
              <Chip
                key={item.path}
                icon={item.icon}
                label={isMobile ? item.short : item.label}
                onClick={() => navigate(item.path)}
                clickable
                color={isActive ? "primary" : "default"}
                variant={isActive ? "filled" : "outlined"}
                sx={{
                  fontWeight: 500,
                  borderRadius: 2,
                  // Ensure gradient is applied only when active/filled for better UX
                  ...(isActive ? {
                    background: 'linear-gradient(45deg, #667eea 0%, #764ba2 100%)',
                    '&:hover': {
                      background: 'linear-gradient(45deg, #5a6fd8 0%, #6a4190 100%)',
                    }
                  } : {
                    // Apply default/outlined styles if not active
                    background: 'none',
                    '&:hover': {
                      backgroundColor: theme.palette.action.hover,
                    }
                  }),
                }}
              />
            );
          })}
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Navbar;