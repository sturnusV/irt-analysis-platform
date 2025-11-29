import apiClient from './api';
import { API_CONFIG } from '../config/api';

export interface UploadResponse {
  task_id: string;
  session_id: string;
  status: string;
  message: string;
}

interface ItemIIFData {
  theta: number[];
  info: number[];
}

export interface AnalysisResults {
  session_id: string;
  status: string;
  item_parameters: any[];
  iif: { [item_id: string]: ItemIIFData };
  test_information: any;
  item_information: any;
  model_fit: any;
  created_at: string;
}

export const uploadService = {
  // Upload CSV file
  async uploadFile(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post(API_CONFIG.ENDPOINTS.UPLOAD, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  },

  // Get analysis results
  async getAnalysisResults(sessionId: string): Promise<AnalysisResults> {
    const response = await apiClient.get(API_CONFIG.ENDPOINTS.ANALYSIS(sessionId));
    return response.data;
  },

  // Get analysis status
  async getAnalysisStatus(sessionId: string): Promise<{ status: string; message: string }> {
    const response = await apiClient.get(API_CONFIG.ENDPOINTS.STATUS(sessionId));
    return response.data;
  },

  async getICCCurves(sessionId: string): Promise<any> {
    const response = await apiClient.get(`/icc/${sessionId}`);
    return response.data;
  },

  async getTIF(sessionId: string): Promise<any> {
    const response = await apiClient.get(`/tif/${sessionId}`);
    return response.data;
  },

  async getIIF(sessionId: string): Promise<any> {
    const response = await apiClient.get(`/iif/${sessionId}`);
    return response.data;
  }
};