import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api/v1';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 120000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.client.interceptors.request.use(
      (config) => {
        const requestId = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        config.headers['X-Request-ID'] = requestId;
        return config;
      },
      (error) => Promise.reject(error)
    );

    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('API Error:', error.response?.data || error.message);
        return Promise.reject(error);
      }
    );
  }

  async query(data: {
    query: string;
    session_id: string;
    user_id?: string;
    use_memory?: boolean;
    use_reranking?: boolean;
    temperature?: number;
    max_tokens?: number;
  }) {
    const response = await this.client.post('/query', data);
    return response.data;
  }

  async uploadFile(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    const response = await this.client.post('/ingest/file', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      maxContentLength: 50 * 1024 * 1024,
    });
    return response.data;
  }

  async ingestPDF(data: {
    file_path: string;
    metadata?: Record<string, any>;
    chunk_size?: number;
    chunk_overlap?: number;
  }) {
    const response = await this.client.post('/ingest/pdf', data);
    return response.data;
  }

  async ingestURL(data: {
    url: string;
    metadata?: Record<string, any>;
    chunk_size?: number;
    chunk_overlap?: number;
  }) {
    const response = await this.client.post('/ingest/url', data);
    return response.data;
  }

  async ingestText(data: {
    text: string;
    source: string;
    metadata?: Record<string, any>;
    chunk_size?: number;
    chunk_overlap?: number;
  }) {
    const response = await this.client.post('/ingest/text', data);
    return response.data;
  }

  async search(type: 'vector' | 'bm25' | 'hybrid', data: any) {
    const response = await this.client.post(`/search/${type}`, data);
    return response.data;
  }

  async getShortTermMemory(sessionId: string, limit?: number) {
    const response = await this.client.get(`/memory/short/${sessionId}`, {
      params: limit ? { limit } : {},
    });
    return response.data;
  }

  async addShortTermMemory(data: {
    session_id: string;
    role: string;
    content: string;
    metadata?: Record<string, any>;
  }) {
    const response = await this.client.post('/memory/short/add', data);
    return response.data;
  }

  async getLongTermMemory(userId: string, category?: string) {
    const response = await this.client.get(`/memory/long/${userId}`, {
      params: category ? { category } : {},
    });
    return response.data;
  }

  async storeLongTermFact(data: {
    user_id: string;
    key: string;
    value: string;
    category?: string;
    confidence?: number;
    source?: string;
  }) {
    const response = await this.client.post('/memory/long/fact', data);
    return response.data;
  }

  async getEpisodicMemory(userId: string, limit?: number, days?: number) {
    const response = await this.client.get(`/memory/episodic/${userId}`, {
      params: { ...(limit && { limit }), ...(days && { days }) },
    });
    return response.data;
  }

  async getMemoryStats(userId: string) {
    const response = await this.client.get(`/memory/stats/${userId}`);
    return response.data;
  }

  async clearShortTermMemory(sessionId: string) {
    const response = await this.client.delete(`/memory/short/${sessionId}`);
    return response.data;
  }

  async summarizeSession(data: { user_id: string; session_id: string }) {
    const response = await this.client.post('/memory/episodic/summarize', data);
    return response.data;
  }

  async healthCheck() {
    if (API_BASE_URL.startsWith('http')) {
      const rootUrl = API_BASE_URL.replace(/\/api\/v1\/?$/, '');
      const response = await axios.get(`${rootUrl}/health`);
      return response.data;
    }
    const response = await this.client.get('/health');
    return response.data;
  }
}

export const api = new ApiClient();