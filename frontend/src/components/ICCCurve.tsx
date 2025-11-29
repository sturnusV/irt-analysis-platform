import * as React from "react";
import {
  Box,
  CircularProgress,
  Alert,
  Paper,
  Typography,
} from "@mui/material";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

import { uploadService } from "../services/uploadService";

interface ICCCurveProps {
  sessionId: string;
  itemParameters: {
    item_id: string;
    difficulty: number;
    discrimination: number;
    guessing: number;
    se_difficulty?: number;
    se_discrimination?: number;
    se_guessing?: number;
    model_type?: string;
  }[];
  selectedItem: string;
}

interface ICCPoint {
  theta: number;
  probability: number;
  item_id: string;
}

const twoDecimalFormatter = (value: number | string): string => {
  return Number(value).toFixed(2);
};

const ICCCurve: React.FC<ICCCurveProps> = ({ sessionId, itemParameters, selectedItem }) => {
  const [iccData, setIccData] = React.useState<ICCPoint[]>([]);
  const [allItemsICC, setAllItemsICC] = React.useState<ICCPoint[]>([]);
  const [loading, setLoading] = React.useState<boolean>(false);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    loadICCData();
  }, [sessionId]);

  React.useEffect(() => {
    if (selectedItem && allItemsICC.length > 0) {
      filterICC(selectedItem, allItemsICC);
    }
  }, [selectedItem, allItemsICC]);

  const loadICCData = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await uploadService.getICCCurves(sessionId);

      if (response.status === "success" && response.icc_data) {
        const data = response.icc_data;
        setAllItemsICC(data);

        if (data.length > 0) {
          const first = data[0].item_id;
          filterICC(first, data);
        }
      } else {
        setError(response.error || "Failed to load ICC data.");
      }
    } catch (err) {
      console.error("ICC loading error:", err);
      setError(
        "Failed to load ICC curves. The IRT model may still be running."
      );
    } finally {
      setLoading(false);
    }
  };

  const filterICC = (itemId: string, data: ICCPoint[]) => {
    setIccData(data.filter((p) => p.item_id === itemId));
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height={300}>
        <CircularProgress />
        <Typography sx={{ ml: 2 }}>Loading ICC curves…</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mt: 2 }}>
        {error}
      </Alert>
    );
  }

  return (
    <Box>
      {/* ICC Chart */}
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Item Characteristic Curve — {selectedItem}
        </Typography>

        {iccData.length > 0 ? (
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={iccData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="theta"
                tickFormatter={twoDecimalFormatter}
                label={{ value: "Ability (θ)", position: "insideBottom", offset: -10 }}
              />
              <YAxis
                domain={[0, 1]}
                label={{ value: "Probability", angle: -90, position: "insideLeft" }}
              />
              <Tooltip
                formatter={(val: number) => [`${(val * 100).toFixed(1)}%`, "P(correct)"]}
                labelFormatter={twoDecimalFormatter}
              />
              <Legend wrapperStyle={{ paddingTop: 5 }} />
              <Line
                type="monotone"
                dataKey="probability"
                stroke="#1976d2"
                strokeWidth={3}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <Box display="flex" justifyContent="center" alignItems="center" height={300}>
            <Typography>No ICC data available.</Typography>
          </Box>
        )}
      </Paper>

      {/* Item Parameters Section - Enhanced Design */}
      {selectedItem && (
        <Paper sx={{ p: 2, mt: 2 }}>
          <Typography variant="h6" gutterBottom>
            Item Parameters
          </Typography>

          {(() => {
            const currentItem = itemParameters.find(item => item.item_id === selectedItem);

            if (!currentItem) {
              return (
                <Alert severity="warning">
                  <Typography variant="body2">
                    Parameter estimates for {selectedItem} are not available.
                    This item may have been removed during analysis due to extreme response patterns.
                  </Typography>
                </Alert>
              );
            }

            return (
              <Box
                display="grid"
                gridTemplateColumns="repeat(auto-fit, minmax(200px, 1fr))"
                gap={2}
              >
                {/* Row 1: Key Parameters */}
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">
                    Discrimination (a)
                  </Typography>
                  <Typography variant="h6">
                    {currentItem.discrimination.toFixed(4)}
                  </Typography>
                  {currentItem.se_discrimination && currentItem.se_discrimination > 0 && (
                    <Typography variant="caption" color="text.secondary">
                      SE: ±{currentItem.se_discrimination.toFixed(4)}
                    </Typography>
                  )}
                </Box>

                <Box>
                  <Typography variant="subtitle2" color="text.secondary">
                    Difficulty (b)
                  </Typography>
                  <Typography variant="h6">
                    {currentItem.difficulty.toFixed(4)}
                  </Typography>
                  {currentItem.se_difficulty && currentItem.se_difficulty > 0 && (
                    <Typography variant="caption" color="text.secondary">
                      SE: ±{currentItem.se_difficulty.toFixed(4)}
                    </Typography>
                  )}
                </Box>

                <Box>
                  <Typography variant="subtitle2" color="text.secondary">
                    Guessing (c)
                  </Typography>
                  <Typography variant="h6">
                    {currentItem.guessing.toFixed(4)}
                  </Typography>
                  {currentItem.se_guessing && currentItem.se_guessing > 0 && (
                    <Typography variant="caption" color="text.secondary">
                      SE: ±{currentItem.se_guessing.toFixed(4)}
                    </Typography>
                  )}
                </Box>

                {/* Row 2: Additional Info */}
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">
                    Model Type
                  </Typography>
                  <Typography variant="h6">
                    {currentItem.model_type || '3PL'}
                  </Typography>
                </Box>

                <Box>
                  <Typography variant="subtitle2" color="text.secondary">
                    Item ID
                  </Typography>
                  <Typography variant="h6">
                    {currentItem.item_id}
                  </Typography>
                </Box>

                {/* Empty cell to maintain grid alignment */}
                <Box></Box>
              </Box>
            );
          })()}

          {/* Interpretation Help */}
          {(() => {
            const currentItem = itemParameters.find(item => item.item_id === selectedItem);
            if (!currentItem) return null;

            let interpretation = "";
            if (currentItem.discrimination > 1.5) {
              interpretation += "High discrimination — excellent at distinguishing ability levels. ";
            } else if (currentItem.discrimination > 0.8) {
              interpretation += "Moderate discrimination — good at distinguishing ability levels. ";
            } else {
              interpretation += "Low discrimination — limited ability to distinguish between students. ";
            }

            if (currentItem.difficulty > 1.0) {
              interpretation += "Difficult item — best for high-ability students.";
            } else if (currentItem.difficulty < -1.0) {
              interpretation += "Easy item — most students can answer correctly.";
            } else {
              interpretation += "Moderate difficulty — appropriate for average students.";
            }

            return (
              <Box sx={{ mt: 2, p: 1, bgcolor: 'info.light', borderRadius: 1 }}>
                <Typography variant="body2">
                  <strong>💡 Interpretation:</strong> {interpretation}
                </Typography>
              </Box>
            );
          })()}
        </Paper>
      )}
    </Box>
  );
};

export default ICCCurve;