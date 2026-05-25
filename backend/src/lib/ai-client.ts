import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { ConfigService } from '../config/config.service';

export class AIClient {
  private client: AxiosInstance;
  private baseURL: string;

  constructor(private readonly configService: ConfigService) {
    const config = this.configService.get();
    this.baseURL = config.aiServiceUrl;

    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: config.aiServiceTimeout,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    this.client.interceptors.request.use(
      (config) => {
        config.headers['X-Request-ID'] = this.generateRequestId();
        return config;
      },
      (error) => Promise.reject(error),
    );

    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 503 && !originalRequest._retry) {
          originalRequest._retry = true;

          await this.delay(1000);
          return this.client(originalRequest);
        }

        return Promise.reject(error);
      },
    );
  }

  private generateRequestId(): string {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  async get<T = any>(path: string, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.client.get(path, config);
    return response.data;
  }

  async post<T = any>(path: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.client.post(path, data, config);
    return response.data;
  }

  async put<T = any>(path: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.client.put(path, data, config);
    return response.data;
  }

  async delete<T = any>(path: string, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.client.delete(path, config);
    return response.data;
  }

  async patch<T = any>(path: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.client.patch(path, data, config);
    return response.data;
  }

  async healthCheck(): Promise<boolean> {
    try {
      await this.client.get('/api/v1/health');
      return true;
    } catch {
      return false;
    }
  }

  getBaseURL(): string {
    return this.baseURL;
  }
}