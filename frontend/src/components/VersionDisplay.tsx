import * as React from 'react';
import { useEffect, useState } from 'react';
import { VersionService, VersionInfo } from '../services/versionService';
import { Typography, Box, Chip } from '@mui/material';

export const VersionDisplay: React.FC = () => {
    const [versionInfo, setVersionInfo] = useState<VersionInfo | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        VersionService.getVersion()
            .then(setVersionInfo)
            .catch(console.error)
            .finally(() => setLoading(false));
    }, []);

    if (loading) return null;

    return (
        // 1. Outer Box: Stacks content vertically and removes incorrect vertical padding/margins
        <Box sx={{
            textAlign: 'left',
            mr: 2,
            display: 'flex',
            flexDirection: 'column', // Stacks children vertically
            justifyContent: 'center',
            // IMPORTANT: Remove mt/mb to fit cleanly within the Toolbar
        }}>

            {/* 2. TOP LINE: Version Number and Environment Chip */}
            <Box sx={{ display: 'flex', alignItems: 'baseline', height: '20px' }}>
                {/* Display only the version number */}
                <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{ fontWeight: 600, lineHeight: 1, mr: 0.5 }} // Compact line height
                >
                    v{versionInfo?.version}
                </Typography>

                {versionInfo?.environment !== 'production' && (
                    <Chip
                        label={versionInfo?.environment}
                        size="small"
                        color="warning"
                        sx={{
                            height: '16px', // Smaller height for clean fit
                            fontSize: '0.6rem', // Smaller font size
                            lineHeight: 1
                        }}
                    />
                )}
            </Box>

            {/* 3. BOTTOM LINE: Build and Commit Hash (Smaller text) 
            <Typography
                variant="caption"
                color="text.secondary"
                sx={{ lineHeight: 1, mt: 0.2 }} // Small margin to separate from the top line
            >
                Build: {versionInfo?.build_date} • Commit: {versionInfo?.commit_hash?.substring(0, 7)}
            </Typography>*/}

        </Box>
    );
};