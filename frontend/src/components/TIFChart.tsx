// TIFChart.tsx - updated with internal data loading
import * as React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
} from "recharts";
import { Box, Typography, CircularProgress, Alert } from "@mui/material";
import { uploadService } from "../services/uploadService";

interface TIFChartProps {
  sessionId: string;
}

interface TIFData {
  status: string;
  theta?: number[];
  tif?: number[];
  sem?: number[];
}

const TIFChart: React.FC<TIFChartProps> = ({ sessionId }) => {
  const [tifData, setTifData] = React.useState<TIFData | null>(null);
  const [loading, setLoading] = React.useState<boolean>(false);
  const [error, setError] = React.useState<string | null>(null);

  // Load TIF data when component mounts or sessionId changes
  React.useEffect(() => {
    const fetchTIFData = async () => {
      if (!sessionId) return;

      setLoading(true);
      setError(null);

      try {
        const tifResponse = await uploadService.getTIF(sessionId);
        if (tifResponse.status === 'success') {
          setTifData(tifResponse);
        } else {
          setError(tifResponse.error || 'Failed to load TIF data');
        }
      } catch (err: any) {
        console.error('TIF loading error:', err);
        setError('Failed to load test information function');
      } finally {
        setLoading(false);
      }
    };

    fetchTIFData();
  }, [sessionId]);

  if (loading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", alignItems: "center", height: 350 }}>
        <CircularProgress />
        <Typography sx={{ ml: 2 }}>Loading test information...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ textAlign: "center", p: 2 }}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  if (!tifData || !Array.isArray(tifData.theta) || !Array.isArray(tifData.tif)) {
    return (
      <Box sx={{ textAlign: "center", p: 2 }}>
        <Typography color="text.secondary">
          Test information data not available.
        </Typography>
      </Box>
    );
  }

  const data = tifData.theta.map((t, i) => ({
    theta: t,
    info: tifData.tif![i] ?? 0,
  }));

  return (
    <Box>
      <ResponsiveContainer width="100%" height={350}>
        <LineChart data={data} margin={{ top: 20, right: 30, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="theta"
            label={{ value: "Ability (θ)", position: "insideBottom", offset: -2 }}
          />
          <YAxis
            label={{ value: "Information", angle: -90, position: "insideLeft" }}
          />
          <Tooltip
            formatter={(value: number) => [value.toFixed(3), "Information"]}
            labelFormatter={(label) => `θ = ${Number(label).toFixed(2)}`}
          />
          <Line
            type="monotone"
            dataKey="info"
            stroke="#1976d2"
            strokeWidth={2}
            dot={false}
            name="Test Information"
          />
        </LineChart>
      </ResponsiveContainer>

      {/* Optional: Show SEM if available */}
      {tifData.sem && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="subtitle1" gutterBottom>
            Standard Error of Measurement
          </Typography>
          <Typography variant="body2" color="text.secondary">
            The test is most precise where information is highest (SEM lowest).
            Minimum SEM: {Math.min(...tifData.sem).toFixed(3)}
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default TIFChart;