import * as React from 'react';
import { Button, Menu, MenuItem, Box } from '@mui/material';
import { Download, PictureAsPdf, TableChart } from '@mui/icons-material';
import { API_CONFIG } from '../config/api';

interface ExportButtonProps {
  sessionId: string;
}

const ExportButton: React.FC<ExportButtonProps> = ({ sessionId }) => {
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);

  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  // Remove /api from base URL for export endpoints
  const baseUrlWithoutApi = API_CONFIG.BASE_URL.replace('/api', '');

  const exportCSV = () => {
    window.open(`${baseUrlWithoutApi}/api/export/csv/${sessionId}`, '_blank');
    handleClose();
  };

  const exportPDF = () => {
    window.open(`${baseUrlWithoutApi}/api/export/pdf/${sessionId}`, '_blank');
    handleClose();
  };

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        height: '100%',
      }}
    >
      <Button
        variant="outlined"
        startIcon={<Download />}
        onClick={handleClick}
        sx={{
          fontWeight: 500,
          borderRadius: 2,
          background: 'linear-gradient(45deg, #A8A8A8 0%, #707070 100%)',
          color: 'white',
          borderColor: '#707070',
          '&:hover': {
            background: 'linear-gradient(45deg, #8C8C8C 0%, #545454 100%)',
            borderColor: '#545454',
          }
        }}
      >
        Export Results
      </Button>
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleClose}
      >
        <MenuItem onClick={exportCSV}>
          <TableChart sx={{ mr: 1 }} />
          Export as CSV
        </MenuItem>
        <MenuItem onClick={exportPDF}>
          <PictureAsPdf sx={{ mr: 1 }} />
          Export as PDF
        </MenuItem>
      </Menu>
    </Box>
  );
};

export default ExportButton;