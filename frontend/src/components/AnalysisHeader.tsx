import * as React from 'react';
import {
    Box,
    Typography,
    Card,
    CardContent,
    Chip,
    CircularProgress,
    Alert,
} from '@mui/material';

interface AnalysisHeaderProps {
    title?: string;
    subtitle?: string;
    loading?: boolean;
    pollCount?: number;
    showExport?: boolean;
    exportComponent?: React.ReactNode;
    results?: any;
    compact?: boolean;
}

const AnalysisHeader: React.FC<AnalysisHeaderProps> = ({
    title = "IRT Analysis Dashboard",
    subtitle = "Advanced Psychometric Analysis Powered by R",
    loading = false,
    pollCount = 0,
    showExport = false,
    exportComponent,
    results,
    compact = false,
}) => {
    return (
        <Box sx={{ mb: compact ? 2 : 4 }}>
            {/* Main Header with Enhanced Design */}
            <Card
                elevation={compact ? 1 : 2}
                sx={{
                    mb: compact ? 1 : 2,
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    color: 'white',
                    position: 'relative',
                    overflow: 'hidden',
                    '&::before': {
                        content: '""',
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        right: 0,
                        bottom: 0,
                        background: 'rgba(255,255,255,0.1)',
                        pointerEvents: 'none',
                    }
                }}
            >
                <CardContent sx={{
                    position: 'relative',
                    zIndex: 1,
                    p: compact ? 2 : 3
                }}>
                    <Box sx={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: compact ? 'center' : 'flex-start',
                        flexDirection: compact ? 'row' : 'row'
                    }}>
                        <Box sx={{ flex: 1 }}>
                            <Typography
                                variant={compact ? "h5" : "h3"}
                                component="h1"
                                gutterBottom
                                sx={{
                                    fontWeight: 800,
                                    fontSize: compact ? '1.5rem' : { xs: '2rem', md: '2.5rem' },
                                    textShadow: '0 2px 4px rgba(0,0,0,0.1)',
                                    background: 'linear-gradient(45deg, #fff 30%, #f8f9fa 90%)',
                                    backgroundClip: 'text',
                                    WebkitBackgroundClip: 'text',
                                    color: 'transparent',
                                    mb: compact ? 0.5 : 2
                                }}
                            >
                                {title}
                            </Typography>
                            {!compact && (
                                <Typography
                                    variant="h6"
                                    sx={{
                                        fontWeight: 300,
                                        opacity: 0.9,
                                        fontSize: { xs: '1rem', md: '1.2rem' },
                                        mb: 1
                                    }}
                                >
                                    {subtitle}
                                </Typography>
                            )}
                            <Box sx={{
                                display: 'flex',
                                flexWrap: 'wrap',
                                gap: 1,
                                mt: compact ? 0 : 2
                            }}>
                                <Chip
                                    label="mirt"
                                    size="small"
                                    sx={{
                                        backgroundColor: 'rgba(255,255,255,0.2)',
                                        color: 'white',
                                        fontWeight: 600,
                                        backdropFilter: 'blur(10px)',
                                        fontSize: compact ? '0.7rem' : '0.8125rem'
                                    }}
                                />
                                <Chip
                                    label="3PL/2PL Models"
                                    size="small"
                                    sx={{
                                        backgroundColor: 'rgba(255,255,255,0.2)',
                                        color: 'white',
                                        fontWeight: 600,
                                        backdropFilter: 'blur(10px)',
                                        fontSize: compact ? '0.7rem' : '0.8125rem'
                                    }}
                                />
                                <Chip
                                    label="ICC Curves"
                                    size="small"
                                    sx={{
                                        backgroundColor: 'rgba(255,255,255,0.2)',
                                        color: 'white',
                                        fontWeight: 600,
                                        backdropFilter: 'blur(10px)',
                                        fontSize: compact ? '0.7rem' : '0.8125rem'
                                    }}
                                />
                                <Chip
                                    label="Test Information"
                                    size="small"
                                    sx={{
                                        backgroundColor: 'rgba(255,255,255,0.2)',
                                        color: 'white',
                                        fontWeight: 600,
                                        backdropFilter: 'blur(10px)',
                                        fontSize: compact ? '0.7rem' : '0.8125rem'
                                    }}
                                />
                            </Box>
                        </Box>
                        {showExport && exportComponent && (
                            <Box sx={{ ml: 2 }}>
                                {exportComponent}
                            </Box>
                        )}
                    </Box>
                </CardContent>
            </Card>

            {/* Enhanced Processing Alert */}
            {loading && (
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
                    <CardContent sx={{ p: compact ? 2 : 3 }}>
                        <Box sx={{
                            display: 'flex',
                            flexDirection: { xs: 'column', sm: 'row' },
                            alignItems: 'center',
                            justifyContent: 'center',
                            textAlign: 'center',
                            gap: 2
                        }}>
                            <Box sx={{ position: 'relative', display: 'inline-flex' }}>
                                <CircularProgress
                                    size={compact ? 36 : 48}
                                    thickness={4}
                                    sx={{
                                        color: 'primary.main',
                                        animation: 'pulse 2s infinite ease-in-out'
                                    }}
                                />
                                <Box
                                    sx={{
                                        top: 0,
                                        left: 0,
                                        bottom: 0,
                                        right: 0,
                                        position: 'absolute',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                    }}
                                >
                                    <Typography
                                        variant="caption"
                                        component="div"
                                        color="primary.main"
                                        sx={{
                                            fontWeight: 'bold',
                                            fontSize: compact ? '0.6rem' : '0.75rem'
                                        }}
                                    >
                                        {Math.min(pollCount * 20, 100)}%
                                    </Typography>
                                </Box>
                            </Box>

                            <Box sx={{ textAlign: 'center' }}>
                                <Box
                                    sx={{
                                        display: 'inline-flex',
                                        alignItems: 'center',
                                        gap: 1,
                                        mb: 1
                                    }}
                                >
                                    <Box
                                        component="span"
                                        sx={{
                                            width: 8,
                                            height: 8,
                                            borderRadius: '50%',
                                            backgroundColor: 'primary.main',
                                            animation: 'blink 1.5s infinite'
                                        }}
                                    />
                                    <Typography
                                        variant={compact ? "subtitle1" : "h6"}
                                        color="primary.main"
                                        sx={{
                                            fontWeight: 600,
                                            m: 0,
                                            lineHeight: 1.2
                                        }}
                                    >
                                        Finalizing IRT Analysis
                                    </Typography>
                                </Box>

                                {!compact && (
                                    <Typography
                                        variant="body2"
                                        color="text.secondary"
                                        sx={{
                                            maxWidth: 400,
                                            mx: 'auto'
                                        }}
                                    >
                                        Running advanced psychometric analysis using R's mirt package...
                                        {pollCount > 0 && ` (${pollCount * 5}s elapsed)`}
                                    </Typography>
                                )}

                                {!compact && (
                                    <Box sx={{
                                        display: 'flex',
                                        gap: 1,
                                        mt: 1,
                                        justifyContent: 'center',
                                        flexWrap: 'wrap'
                                    }}>
                                        <Chip
                                            label="✓ Data Validation"
                                            size="small"
                                            color="success"
                                            variant="outlined"
                                        />
                                        <Chip
                                            label={pollCount > 2 ? "✓ Model Fitting" : "◯ Model Fitting"}
                                            size="small"
                                            color={pollCount > 2 ? "success" : "default"}
                                            variant="outlined"
                                        />
                                        <Chip
                                            label={pollCount > 4 ? "✓ Parameter Estimation" : "◯ Parameter Estimation"}
                                            size="small"
                                            color={pollCount > 4 ? "success" : "default"}
                                            variant="outlined"
                                        />
                                        <Chip
                                            label={pollCount > 6 ? "✓ ICC Generation" : "◯ ICC Generation"}
                                            size="small"
                                            color={pollCount > 6 ? "success" : "default"}
                                            variant="outlined"
                                        />
                                    </Box>
                                )}
                            </Box>
                        </Box>

                        {/* R Package Info */}
                        {!compact && (
                            <Box
                                sx={{
                                    mt: 3,
                                    pt: 2,
                                    borderTop: '1px solid',
                                    borderColor: 'divider',
                                    textAlign: 'center'
                                }}
                            >
                                <Typography
                                    variant="caption"
                                    color="text.secondary"
                                    sx={{ fontStyle: 'italic' }}
                                >
                                    Powered by R's <strong>mirt</strong> package • Multidimensional Item Response Theory •
                                    Advanced model fitting with fallback strategies
                                </Typography>
                            </Box>
                        )}
                    </CardContent>
                </Card>
            )}
        </Box>
    );
};

export default AnalysisHeader;