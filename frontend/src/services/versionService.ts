import apiClient from './api';
import { API_CONFIG } from '../config/api';

// Export the interface as it is correct
export interface VersionInfo {
    version: string;
    name: string;
    description: string;
    build_date: string;
    commit_hash: string;
    environment: string;
}

export class VersionService {
    // Refactor to use apiClient and API_CONFIG
    static async getVersion(): Promise<VersionInfo> {
        // Use the GET method from apiClient (Axios) with the defined endpoint
        const response = await apiClient.get<VersionInfo>(API_CONFIG.ENDPOINTS.VERSION);
        
        // Axios wraps the data in a 'data' property
        return response.data;
    }
}