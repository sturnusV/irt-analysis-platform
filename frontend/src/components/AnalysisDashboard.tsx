import * as React from 'react';
import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import {
  Box,
  Typography,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  Grid,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  MenuItem,
  Select,
  FormControl,
  useTheme,
  useMediaQuery,
  InputLabel,
  SelectChangeEvent,
} from '@mui/material';
import {
  Analytics,
  TableChart,
  ShowChart,
  Assessment,
} from '@mui/icons-material';
import { uploadService } from '../services/uploadService';
import ExportButton from './ExportButton';
import ICCCurve from './ICCCurve';
import IIFChart from './IIFChart';
import TIFChart from './TIFChart';
import AnalysisHeader from './AnalysisHeader';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

interface AnalysisResults {
  session_id: string;
  status: string;
  item_parameters: any[];
  iif: { [item_id: string]: { theta: number[]; info: number[] } };
  test_information: any;
  item_information: any;
  model_fit: any;
  created_at: string;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index, ...other }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`analysis-tabpanel-${index}`}
      aria-labelledby={`analysis-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
};

const safeToFixed = (value: any, decimals: number = 3): string => {
  if (value === null || value === undefined) return 'N/A';
  const num = Number(value);
  return isNaN(num) ? 'N/A' : num.toFixed(decimals);
};

const safeNumber = (value: any): number => {
  if (value === null || value === undefined) return 0;
  const num = Number(value);
  return isNaN(num) ? 0 : num;
};

const ItemParametersTable: React.FC<{ parameters: any[] }> = ({ parameters }) => {
  return (
    <TableContainer component={Paper}>
      <Table sx={{ minWidth: 650 }} aria-label="item parameters table">
        <TableHead>
          <TableRow>
            <TableCell>Item ID</TableCell>
            <TableCell align="right">Difficulty</TableCell>
            <TableCell align="right">Discrimination</TableCell>
            <TableCell align="right">Guessing</TableCell>
            <TableCell align="right">SE Difficulty</TableCell>
            <TableCell align="right">SE Discrimination</TableCell>
            <TableCell align="right">SE Guessing</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {parameters.map((item) => (
            <TableRow key={item.item_id}>
              <TableCell component="th" scope="row">
                {item.item_id}
              </TableCell>
              <TableCell align="right">{item.difficulty}</TableCell>
              <TableCell align="right">{item.discrimination}</TableCell>
              <TableCell align="right">{item.guessing}</TableCell>
              <TableCell align="right">{item.se_difficulty || 'N/A'}</TableCell>
              <TableCell align="right">{item.se_discrimination || 'N/A'}</TableCell>
              <TableCell align="right">{item.se_guessing || 'N/A'}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

const ItemAnalysisSummary: React.FC<{ parameters: any[] }> = ({ parameters }) => {
  const difficulties = parameters.map(item => item.difficulty);
  const discriminations = parameters.map(item => item.discrimination);
  const guessing = parameters.map(item => item.guessing);

  const avgDifficulty = difficulties.reduce((a, b) => a + b, 0) / difficulties.length;
  const avgDiscrimination = discriminations.reduce((a, b) => a + b, 0) / discriminations.length;
  const avgGuessing = guessing.reduce((a, b) => a + b, 0) / guessing.length;

  return (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom color="primary">
          Item Analysis Summary
        </Typography>
        <Grid container spacing={2} sx={{ mt: 1 }}>
          <Grid item xs={12} sm={4}>
            <Typography variant="body2"><strong>Average Difficulty:</strong> {safeToFixed(avgDifficulty, 3)}</Typography>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Typography variant="body2"><strong>Average Discrimination:</strong> {safeToFixed(avgDiscrimination, 3)}</Typography>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Typography variant="body2"><strong>Average Guessing:</strong> {safeToFixed(avgGuessing, 3)}</Typography>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

// Define tab list once for both Tabs and Select menu
const TAB_DEFINITIONS = [
  { label: 'Item Parameters', icon: <TableChart />, value: 0 },
  { label: 'Characteristic Curves & Information', icon: <ShowChart />, value: 1 },
  { label: 'Test Information', icon: <Assessment />, value: 2 },
  { label: 'Model Diagnostics', icon: <Analytics />, value: 3 },
];

const AnalysisDashboard: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [results, setResults] = useState<AnalysisResults | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [pollCount, setPollCount] = useState(0);
  const [isPolling, setIsPolling] = useState(true);
  const [selectedItem, setSelectedItem] = useState('');

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const fetchResults = useCallback(async () => {
    if (!sessionId || !isPolling) return;

    try {
      const analysisResults = await uploadService.getAnalysisResults(sessionId);
      setResults(analysisResults);
      setError(null);

      if (analysisResults.status === 'completed') {
        setLoading(false);
        setIsPolling(false);
      } else if (analysisResults.status === 'error') {
        setError('Analysis failed. Please try again.');
        setLoading(false);
        setIsPolling(false);
      }
    } catch (err: any) {
      // 404 is normal while processing - don't show error
      if (err.response?.status === 404) {
        // Continue polling, this is expected
        console.log('Results not ready yet, continuing to poll...');
      } else {
        // Show real errors
        setError(err.response?.data?.detail || 'Failed to load analysis results');
        console.error('Error fetching results:', err);
      }

      // Stop polling after 2 minutes (24 attempts × 5 seconds)
      if (pollCount >= 24) {
        setError('Analysis timed out. Please try uploading the file again.');
        setLoading(false);
        setIsPolling(false);
      }
    }
  }, [sessionId, isPolling, pollCount]);

  useEffect(() => {
    if (results && results.item_parameters && results.item_parameters.length > 0) {
      setSelectedItem(results.item_parameters[0].item_id);
    }
  }, [results]);

  useEffect(() => {
    if (!sessionId) return;

    // Initial fetch
    fetchResults();

    // Set up polling if still needed
    if (isPolling) {
      const interval = setInterval(() => {
        setPollCount(prev => prev + 1);
        fetchResults();
      }, 5000); // Poll every 5 seconds

      return () => clearInterval(interval);
    }
  }, [sessionId, isPolling, fetchResults]);

  const is3PLFallback =
    results?.item_parameters?.some(
      (it) =>
        it.guessing === 0 ||
        it.guessing === null ||
        it.guessing === undefined
    ) || false;

  // 2. Use the existing state setter for the Tabs logic
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  // 3. Define the new select handler
  const handleSelectChange = (event: SelectChangeEvent<number>) => {
    const newTabValue = Number(event.target.value);
    setTabValue(newTabValue);
  };

  // Show loading state
  if (loading && !results) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mt: 8 }}>
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ mt: 2 }}>
          Analyzing Test Data...
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          This may take a few moments. {pollCount > 0 && `Waiting: ${pollCount * 5} seconds...`}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Please don't close this page.
        </Typography>
        {pollCount > 10 && (
          <Alert severity="info" sx={{ mt: 2, maxWidth: 400 }}>
            Analysis is taking longer than expected. This is normal for larger datasets.
          </Alert>
        )}
      </Box>
    );
  }

  // Show error state
  if (error && !results) {
    return (
      <Box sx={{ maxWidth: 600, mx: 'auto', mt: 4 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
        <Alert severity="info">
          You can try uploading the file again or check the server logs for more details.
        </Alert>
      </Box>
    );
  }

  // Show no results state (shouldn't normally happen with proper polling)
  if (!results) {
    return (
      <Box sx={{ maxWidth: 600, mx: 'auto', mt: 4 }}>
        <Alert severity="warning">
          No analysis results found. The analysis may still be processing or may have failed.
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto' }}>
      {/* Header */}
      <AnalysisHeader
        loading={loading}
        pollCount={pollCount}
        showExport={!!results}
        exportComponent={results && <ExportButton sessionId={results.session_id} />}
        compact={false}
      />

      {/* Summary Cards (remain the same) */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="primary.main" gutterBottom>
                {results.item_parameters?.length || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Items Analyzed
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="success.main" gutterBottom>
                {safeToFixed(results.model_fit?.reliability, 3)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Test Reliability
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="info.main" gutterBottom>
                {safeToFixed(results.model_fit?.m2, 3)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Model Fit (M2)
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color={loading ? "warning.main" : "success.main"} gutterBottom>
                {loading ? 'Processing' : 'Ready'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Analysis Status
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Conditional Tab/Select Rendering */}
      <Card>
        <CardContent sx={{ p: 0 }}>
          {isMobile ? (
            <Box sx={{ p: 2 }}>
              <FormControl fullWidth>
                <InputLabel id="analysis-section-select-label">Select Analysis Section</InputLabel>
                <Select
                  labelId="analysis-section-select-label"
                  value={tabValue}
                  label="Select Analysis Section"
                  onChange={handleSelectChange}
                >
                  {TAB_DEFINITIONS.map((tab) => (
                    <MenuItem key={tab.value} value={tab.value}>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        {tab.icon}
                        <Typography sx={{ ml: 1 }}>{tab.label}</Typography>
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Box>
          ) : (
            // Desktop Tabs: Horizontal display
            <Tabs
              value={tabValue}
              onChange={handleTabChange}
              aria-label="analysis tabs"
              sx={{ borderBottom: 1, borderColor: 'divider' }}
            >
              {TAB_DEFINITIONS.map((tab) => (
                <Tab
                  key={tab.value}
                  icon={tab.icon}
                  label={tab.label}
                  iconPosition="start"
                />
              ))}
            </Tabs>
          )}

          {/* TabPanel Contents */}
          <TabPanel value={tabValue} index={0}>
            <Typography variant="h6" gutterBottom>
              Item Parameter Estimates
            </Typography>
            {is3PLFallback && (
              <Alert severity="warning" sx={{ mb: 2 }}>
                Some items could not be estimated with the 3PL model.
                The system automatically used the 2PL model for those items.
              </Alert>
            )}
            {results.item_parameters && results.item_parameters.length > 0 ? (
              <>
                <ItemAnalysisSummary parameters={results.item_parameters} />
                <ItemParametersTable parameters={results.item_parameters} />
              </>
            ) : (
              <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                <Typography color="text.secondary">
                  No item parameters available
                </Typography>
              </Paper>
            )}
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <Typography variant="h6" gutterBottom>
              Item Characteristic Curves & Information
            </Typography>
            {is3PLFallback && (
              <Alert severity="info" sx={{ mb: 2 }}>
                Guessing parameters were unavailable for some items.
                ICC curves for those items are shown using the 2PL model.
              </Alert>
            )}
            {results.item_parameters && results.item_parameters.length > 0 ? (
              <>
                {/* Shared Item Selector - MOVED INSIDE THE TABPANEL */}
                <Paper sx={{ p: 2, mb: 3 }}>
                  <FormControl fullWidth>
                    <InputLabel>Select Item</InputLabel>
                    <Select
                      value={selectedItem}
                      label="Select Item"
                      onChange={(e) => setSelectedItem(e.target.value)}
                    >
                      {results?.item_parameters?.map((item) => (
                        <MenuItem key={item.item_id} value={item.item_id}>
                          {item.item_id} — a={item.discrimination.toFixed(4)} | b={item.difficulty.toFixed(4)} | c={item.guessing.toFixed(4)}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Paper>

                {/* Charts */}
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <ICCCurve
                      sessionId={results.session_id}
                      itemParameters={results.item_parameters}
                      selectedItem={selectedItem}
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <IIFChart
                      sessionId={results.session_id}
                      itemParameters={results.item_parameters}
                      selectedItem={selectedItem}
                    />
                  </Grid>
                </Grid>
              </>
            ) : (
              <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                <Typography color="text.secondary">
                  No item parameters available for ICC visualization
                </Typography>
              </Paper>
            )}
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            <Typography variant="h6" gutterBottom>
              Test Information Function
            </Typography>
            {is3PLFallback && (
              <Alert severity="info" sx={{ mb: 2 }}>
                Test information was computed using a hybrid model (3PL where available, 2PL fallback where needed).
              </Alert>
            )}
            {results ? (
              <TIFChart sessionId={results.session_id} />
            ) : (
              <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                <Typography color="text.secondary">
                  No analysis results available
                </Typography>
              </Paper>
            )}
          </TabPanel>

          <TabPanel value={tabValue} index={3}>
            <Typography variant="h6" gutterBottom>
              Model Fit Diagnostics
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom color="primary">
                      Fit Statistics
                    </Typography>
                    <Box sx={{ mt: 2 }}>
                      <Typography><strong>M2 Statistic:</strong> {results.model_fit?.m2 || 'N/A'}</Typography>
                      <Typography><strong>M2 p-value:</strong> {results.model_fit?.m2_p || 'N/A'}</Typography>
                      <Typography><strong>Reliability:</strong> {results.model_fit?.reliability || 'N/A'}</Typography>
                      <Typography><strong>Log-Likelihood:</strong> {results.model_fit?.log_likelihood || 'N/A'}</Typography>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom color="primary">
                      Interpretation
                    </Typography>
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="body2">
                        <strong>Reliability {results.model_fit?.reliability > 0.8 ? '✓' : '⚠'}:</strong> {
                          results.model_fit?.reliability > 0.9 ? 'Excellent' :
                            results.model_fit?.reliability > 0.8 ? 'Good' :
                              results.model_fit?.reliability > 0.7 ? 'Acceptable' : 'Poor'
                        } test reliability
                      </Typography>
                      <Typography variant="body2" sx={{ mt: 1 }}>
                        <strong>Model Fit {results.model_fit?.m2_p > 0.05 ? '✓' : '⚠'}:</strong> {
                          results.model_fit?.m2_p > 0.05 ? 'Good model fit (p > 0.05)' :
                            'Potential model fit issues (p < 0.05)'
                        }
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </TabPanel>
        </CardContent>
      </Card>
    </Box>
  );
};

export default AnalysisDashboard;