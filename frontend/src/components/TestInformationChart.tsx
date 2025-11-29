import * as React from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { Box, Typography, Paper } from '@mui/material';

interface TestInformationChartProps {
  testInformation: {
    theta: number[];
    information: number[];
  } | any;
}

const twoDecimalFormatter = (value: number | string): string => {
  const num = Number(value);
  // Handle very small numbers and floating point issues
  if (Math.abs(num) < 0.001) return '0';
  if (Math.abs(num - Math.round(num)) < 0.001) return Math.round(num).toString();
  return num.toFixed(2);
};

const TestInformationChart: React.FC<TestInformationChartProps> = ({ testInformation }) => {
  if (!testInformation || !testInformation.theta || !testInformation.information) {
    return (
      <Paper sx={{ p: 2, textAlign: 'center' }}>
        <Typography color="text.secondary">
          Test information data not available
        </Typography>
      </Paper>
    );
  }

  // Clean the data at source
  const cleanData = testInformation.theta.map((theta: number, index: number) => ({
    // Force clean theta values by rounding to 2 decimals
    theta: Number(theta.toFixed(2)),
    information: Number((testInformation.information[index] || 0).toFixed(3))
  }));

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Test Information Function
      </Typography>
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={cleanData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="theta"
            tickFormatter={twoDecimalFormatter}
            label={{ value: 'Ability (θ)', position: 'insideBottom', offset: -10 }}
            domain={[-4, 4]}
          />
          <YAxis
            tickFormatter={twoDecimalFormatter}
            label={{ value: 'Information', angle: -90, position: 'insideLeft' }}
            domain={[0, 'dataMax + 0.1']}
          />
          <Tooltip
            formatter={(value: number) => [twoDecimalFormatter(value), "Information"]}
            labelFormatter={(label: number) => `θ = ${twoDecimalFormatter(label)}`}
          />
          <Legend wrapperStyle={{ paddingTop: 5 }}/>
          <Line
            type="monotone"
            dataKey="information"
            stroke="#1976d2"
            strokeWidth={3}
            dot={false}
            name="Test Information"
          />
        </LineChart>
      </ResponsiveContainer>
    </Paper>
  );
};

export default TestInformationChart;