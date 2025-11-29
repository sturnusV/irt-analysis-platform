import * as React from 'react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  CardContent,
  Typography,
  Button,
  Box,
  Alert,
  CircularProgress,
  Paper,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  Container,
  Divider,
} from '@mui/material';
import {
  CloudUpload,
  Description,
  CheckCircle,
  TableChart,
  Psychology,
  Analytics,
  PlayArrow,
  RemoveCircleOutline,
  Info,
} from '@mui/icons-material';
import { uploadService } from '../services/uploadService';
import { alpha, styled } from '@mui/material/styles';

const VisuallyHiddenInput = styled('input')({
  clip: 'rect(0 0 0 0)',
  clipPath: 'inset(50%)',
  height: 1,
  overflow: 'hidden',
  position: 'absolute',
  bottom: 0,
  left: 0,
  whiteSpace: 'nowrap',
  width: 1,
});

const UploadArea = styled(Paper)(({ theme }) => ({
  border: `2px dashed ${theme.palette.primary.main}`,
  borderRadius: theme.spacing(2),
  padding: theme.spacing(4),
  textAlign: 'center',
  backgroundColor: theme.palette.primary.light + '08',
  cursor: 'pointer',
  transition: 'all 0.3s ease',
  '&:hover': {
    backgroundColor: theme.palette.primary.light + '12',
    borderColor: theme.palette.primary.dark,
  },
}));

const FeatureChip = styled(Chip)(({ theme }) => ({
  backgroundColor: alpha(theme.palette.primary.main, 0.1),
  color: theme.palette.primary.dark,
  fontWeight: 600,
  border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`,
  '& .MuiChip-icon': {
    color: theme.palette.primary.main,
  },
}));

const FileUpload: React.FC = () => {
  const [isUploading, setIsUploading] = useState(false);
  const [isLoadingSample, setIsLoadingSample] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const navigate = useNavigate();

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.name.endsWith('.csv')) {
      setError('Please upload a CSV file');
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
    setError(null);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setError(null);

    try {
      const response = await uploadService.uploadFile(selectedFile);
      console.log('Upload response:', response);

      // Navigate to analysis page
      navigate(`/analysis/${response.session_id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Upload failed. Please try again.');
      console.error('Upload error:', err);
    } finally {
      setIsUploading(false);
    }
  };

  const handleSampleData = async () => {
    setIsLoadingSample(true);
    setError(null);

    const sampleFilePath = '/simulated_3pl_responses.csv';

    try {
      // 1. Fetch the CSV content from the public folder
      const response = await fetch(sampleFilePath);

      if (!response.ok) {
        throw new Error(`Failed to fetch sample data: ${response.status} ${response.statusText}`);
      }

      // 2. Get the raw text content
      const csvText = await response.text();

      // 3. Create a Blob and File object from the fetched content
      const blob = new Blob([csvText], { type: 'text/csv' });
      const sampleFile = new File([blob], 'simulated_3pl_responses.csv', { type: 'text/csv' });

      // 4. Upload the sample file via your existing service
      const uploadResponse = await uploadService.uploadFile(sampleFile);
      console.log('Sample data upload response:', uploadResponse);

      // 5. Navigate to analysis page
      navigate(`/analysis/${uploadResponse.session_id}`);
    } catch (err: any) {
      setError(err.message || err.response?.data?.detail || 'Failed to load sample data. Please try again.');
      console.error('Sample data error:', err);
    } finally {
      setIsLoadingSample(false);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: { xs: 2, md: 4 } }}>
      <Box sx={{ maxWidth: 800, mx: 'auto', mt: 4 }}>

        {/* Enhanced Processing Alert */}
        <Card
          elevation={1}
          sx={{
            border: '1px solid',
            borderColor: 'primary.light',
            background: 'linear-gradient(45deg, #f8f9ff 0%, #f0f2ff 100%)',
            position: 'relative',
            overflow: 'hidden'
          }}
        >
          <CardContent sx={{ position: 'relative', zIndex: 1, p: { xs: 4, md: 6 } }}>
            <Box sx={{ textAlign: 'center', mb: 0 }}>
              <Typography
                variant="h2"
                component="h1"
                gutterBottom
                sx={{
                  fontWeight: 800,
                  background: 'linear-gradient(45deg, #667eea 0%, #764ba2 100%)',
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  color: 'transparent',
                  fontSize: { xs: '2rem', sm: '2.5rem', md: '3.5rem' },
                }}
              >
                Advanced IRT Analysis
              </Typography>
              <Typography
                variant="h5"
                sx={{
                  mb: 3,
                  maxWidth: 600,
                  mx: 'auto',
                  fontWeight: 300,
                  fontSize: { xs: '1.1rem', sm: '1.3rem', md: '1.5rem' },
                  opacity: 0.9,
                }}
              >
                Professional-grade Item Response Theory analysis powered by R
              </Typography>

              {/* Feature Chips */}
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap', mb: 3 }}>
                <FeatureChip icon={<Psychology />} label="3PL/2PL Models" />
                <FeatureChip icon={<Analytics />} label="ICC Curves" />
                <FeatureChip icon={<TableChart />} label="Test Information" />
              </Box>

              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ fontStyle: 'italic' }}
              >
                Powered by R's <strong>mirt</strong> package • Multidimensional Item Response Theory •
                Advanced model fitting with fallback strategies
              </Typography>
            </Box>

          </CardContent>
        </Card>

      </Box>

      <Box sx={{ maxWidth: 800, mx: 'auto', mt: 4 }}>
        <Card elevation={3}>
          <CardContent sx={{ p: 4 }}>
            {/* Upload Area */}
            <Box sx={{ mb: 4 }}>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                Upload Test Data
              </Typography>

              <label htmlFor="file-upload">
                <VisuallyHiddenInput
                  id="file-upload"
                  type="file"
                  accept=".csv"
                  onChange={handleFileSelect}
                  disabled={isUploading || isLoadingSample}
                />
                <UploadArea>
                  <CloudUpload sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
                  <Typography variant="h6" gutterBottom>
                    {selectedFile ? 'File Selected' : 'Choose CSV File'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {selectedFile
                      ? selectedFile.name
                      : 'Click to browse or drag and drop your test data file'
                    }
                  </Typography>
                  <Button
                    variant="contained"
                    component="span"
                    startIcon={<CloudUpload />}
                    disabled={isUploading || isLoadingSample}
                  >
                    Browse Files
                  </Button>
                  <Box sx={{ mt: 0, mb: 0, alignItems: 'center', justifyContent: 'center', textAlign: 'center' }}>
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 2, mb: 2 }}>
                      or
                    </Typography>

                    <Button
                      variant="contained"
                      component="span"
                      onClick={handleSampleData}
                      disabled={isUploading || isLoadingSample}
                      startIcon={isLoadingSample ? <CircularProgress size={20} /> : <PlayArrow />}
                    >
                      {isLoadingSample ? 'Loading...' : 'Sample Data'}
                    </Button>
                  </Box>
                </UploadArea>
              </label>

              {selectedFile && (
                <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Chip
                    icon={<Description />}
                    label={selectedFile.name}
                    variant="outlined"
                    color="primary"
                    onDelete={() => setSelectedFile(null)}
                  />
                </Box>
              )}
            </Box>

            {/* Error Display */}
            {error && (
              <Alert severity="error" sx={{ mb: 3 }}>
                {error}
              </Alert>
            )}

            {/* Action Buttons */}
            <Box sx={{ textAlign: 'center', mb: 4 }}>
              <Button
                variant="contained"
                size="large"
                onClick={handleUpload}
                disabled={!selectedFile || isUploading || isLoadingSample}
                startIcon={isUploading ? <CircularProgress size={20} /> : <CloudUpload />}
                sx={{
                  px: 1.5,
                  py: 1.5,
                  minWidth: 200
                }}
              >
                {isUploading ? 'Analyzing...' : 'Start IRT Analysis'}
              </Button>
            </Box>

            {/* File Format Requirements */}
            <Card variant="outlined">
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                  <TableChart sx={{ mr: 1 }} />
                  Expected CSV Format
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemIcon>
                      <CheckCircle color="success" />
                    </ListItemIcon>
                    <ListItemText
                      primary="Data must contain ONLY item response columns"
                      secondary="Each column represents an item, and each row represents a student's responses."
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <CheckCircle color="success" />
                    </ListItemIcon>
                    <ListItemText
                      primary="Responses must be strictly Binary (0 or 1)"
                      secondary="0 for incorrect/not answered, 1 for correct/answered."
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <RemoveCircleOutline color="error" />
                    </ListItemIcon>
                    <ListItemText
                      primary="Do NOT include a Student ID or any other non-response column"
                      secondary="The R analysis service processes all columns as item responses."
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <Info color="info" />
                    </ListItemIcon>
                    <ListItemText
                      primary="Missing Responses (Optional)"
                      secondary="Missing data (NA/empty cells) is acceptable but requires sufficient complete data for analysis."
                    />
                  </ListItem>
                </List>

                <Typography variant="subtitle1" sx={{ mt: 2, mb: 1 }}>
                  Example Format:
                </Typography>
                <Box sx={{ p: 1, backgroundColor: 'grey.100', overflowX: 'auto' }}>
                  <pre>
                    {`Item_1,Item_2,Item_3,Item_4
1,0,1,1
0,1,0,0
1,1,1,0
0,0,1,1
...`}
                  </pre>
                </Box>
              </CardContent>
            </Card>
          </CardContent>
        </Card>
      </Box>
    </Container>
  );
};

export default FileUpload;