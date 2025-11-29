import * as React from "react";
import {
    Box,
    Paper,
    Typography,
    Alert,
    CircularProgress,
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

interface ItemIIFData {
    [item_id: string]: {
        theta: number[];
        info: number[];
    };
}

interface IIFResponse {
    status: string;
    iif_data?: {
        theta: number;
        iif: number;
        item_id: string;
    }[];
    error?: string;
}

interface IIFStateData {
    [item_id: string]: {
        theta: number[];
        info: number[];
    };
}

interface ChartDataPoint {
    theta: number;
    info: number;
}

interface IIFChartProps {
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

const twoDecimalFormatter = (value: number | string): string => {
    return Number(value).toFixed(2);
};

const processIIFResponse = (data: IIFResponse['iif_data']): IIFStateData => {
    if (!data) return {};

    // Group the long format data by item_id
    const groupedData: IIFStateData = {};

    data.forEach(point => {
        const itemId = point.item_id;
        if (!groupedData[itemId]) {
            groupedData[itemId] = { theta: [], info: [] };
        }
        groupedData[itemId].theta.push(point.theta);
        groupedData[itemId].info.push(point.iif);
    });

    return groupedData;
};

const transformForChart = (itemData: { theta: number[]; info: number[] }): ChartDataPoint[] => {
    return itemData.theta.map((theta, index) => ({
        theta: theta,
        info: itemData.info[index],
    }));
};

const IIFChart: React.FC<IIFChartProps> = ({ sessionId, itemParameters, selectedItem }) => {
    const [allIifData, setAllIifData] = React.useState<IIFStateData | null>(null);
    const [loading, setLoading] = React.useState<boolean>(false);
    const [error, setError] = React.useState<string | null>(null);
    const [chartData, setChartData] = React.useState<ChartDataPoint[]>([]);

    React.useEffect(() => {
        const fetchIIFData = async () => {
            if (!sessionId) return;

            setLoading(true);
            setError(null);

            try {
                const iifResponse: IIFResponse = await uploadService.getIIF(sessionId);

                if (iifResponse.status === 'success' && iifResponse.iif_data) {
                    const processedData = processIIFResponse(iifResponse.iif_data);
                    setAllIifData(processedData);

                    const itemIds = Object.keys(processedData);
                    if (itemIds.length > 0) {
                        const firstItem = itemIds[0];
                        setChartData(transformForChart(processedData[firstItem]));
                    }
                } else {
                    setError(iifResponse.error || 'Failed to load Item Information data');
                }
            } catch (err: any) {
                console.error('IIF loading error:', err);
                setError('Failed to load item information function');
            } finally {
                setLoading(false);
            }
        };

        fetchIIFData();
    }, [sessionId]);

    React.useEffect(() => {
        if (selectedItem && allIifData && allIifData[selectedItem]) {
            setChartData(transformForChart(allIifData[selectedItem]));
        }
    }, [selectedItem, allIifData]);

    if (loading) {
        return (
            <Box sx={{ display: "flex", justifyContent: "center", alignItems: "center", height: 350 }}>
                <CircularProgress />
                <Typography sx={{ ml: 2 }}>Loading item information...</Typography>
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

    // Fix: Handle null case for allIifData
    const availableItemIds = allIifData ? Object.keys(allIifData) : [];

    // Fix: Check if allIifData is null OR empty
    if (!allIifData || availableItemIds.length === 0) {
        return (
            <Box sx={{ textAlign: "center", p: 2 }}>
                <Typography color="text.secondary">
                    Item information data not available.
                </Typography>
            </Box>
        );
    }

    if (chartData.length === 0) {
        return (
            <Alert severity="info" sx={{ mt: 2 }}>
                Please select an item to view its Item Information Function.
            </Alert>
        );
    }

    const maxIIF = chartData.reduce((max, p) => Math.max(max, p.info), 0);
    const maxInfoPoint = chartData.reduce((max, point) =>
        point.info > max.info ? point : max, chartData[0]
    );

    return (
        <Box>
            {/* IIF Chart */}
            <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                    Item Information Function (IIF) — {selectedItem}
                </Typography>

                {chartData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={400}>
                        <LineChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis
                                dataKey="theta"
                                tickFormatter={twoDecimalFormatter}
                                label={{ value: "Ability (θ)", position: "insideBottom", offset: -10 }}
                            />
                            <YAxis
                                domain={[0, maxIIF * 1.05]}
                                label={{ value: "Information", angle: -90, position: "insideLeft" }}
                            />
                            <Tooltip
                                formatter={(val: number) => [twoDecimalFormatter(val), "Information"]}
                                labelFormatter={twoDecimalFormatter}
                            />
                            <Legend wrapperStyle={{ paddingTop: 5 }} />
                            <Line
                                type="monotone"
                                dataKey="info"
                                name="Item Information"
                                stroke="#ff9800"
                                strokeWidth={3}
                                dot={false}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                ) : (
                    <Box display="flex" justifyContent="center" alignItems="center" height={300}>
                        <Typography>No IIC data available.</Typography>
                    </Box>
                )}
            </Paper>

            {/* Item Parameters Section - Enhanced but same layout */}
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
                                {/* Information and Model */}
                                <Box>
                                    <Typography variant="subtitle2" color="text.secondary">
                                        Max Information
                                    </Typography>
                                    <Typography variant="h6">
                                        {maxIIF.toFixed(3)}
                                    </Typography>
                                    <Typography variant="caption" color="text.secondary">
                                        at θ = {maxInfoPoint.theta.toFixed(2)}
                                    </Typography>
                                </Box>
                            </Box>
                        );
                    })()}

                    {/* Missing Items Notice - Only show if needed */}
                    {availableItemIds.length < itemParameters.length && (
                        <Alert severity="info" sx={{ mt: 2 }}>
                            <Typography variant="body2">
                                Showing {availableItemIds.length} of {itemParameters.length} items.
                                Some items were excluded due to estimation issues or extreme response patterns.
                            </Typography>
                        </Alert>
                    )}
                </Paper>
            )}
        </Box>
    );
};

export default IIFChart;