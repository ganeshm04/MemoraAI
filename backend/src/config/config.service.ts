import { Injectable } from '@nestjs/common';

export interface AppConfig {
  port: number;
  host: string;
  environment: string;
  aiServiceUrl: string;
  aiServiceTimeout: number;
  corsOrigins: string[];
  metricsToken: string;
  rateLimit: {
    ttl: number;
    limit: number;
  };
  logging: {
    level: string;
    format: string;
  };
  security: {
    maxRequestSize: string;
    corsMaxAge: number;
  };
}

@Injectable()
export class ConfigService {
  private readonly config: AppConfig;

  constructor() {
    this.config = {
      port: parseInt(process.env.PORT || '3000', 10),
      host: process.env.HOST || '0.0.0.0',
      environment: process.env.NODE_ENV || 'development',
      aiServiceUrl: process.env.AI_SERVICE_URL || 'http://localhost:8000',
      aiServiceTimeout: parseInt(process.env.AI_SERVICE_TIMEOUT || '120000', 10),
      corsOrigins: this.parseCorsOrigins(),
      metricsToken: process.env.METRICS_TOKEN || '',
      rateLimit: {
        ttl: parseInt(process.env.RATE_LIMIT_TTL || '60000', 10),
        limit: parseInt(process.env.RATE_LIMIT_LIMIT || '100', 10),
      },
      logging: {
        level: process.env.LOG_LEVEL || 'info',
        format: process.env.LOG_FORMAT || 'json',
      },
      security: {
        maxRequestSize: process.env.MAX_REQUEST_SIZE || '10mb',
        corsMaxAge: parseInt(process.env.CORS_MAX_AGE || '86400', 10),
      },
    };
  }

  get(): AppConfig;
  get<T>(key: string): T;
  get<T>(key?: string): AppConfig | T {
    if (key) {
      return this.config[key as keyof AppConfig] as T;
    }
    return this.config;
  }

  isProduction(): boolean {
    return this.config.environment === 'production';
  }

  isDevelopment(): boolean {
    return this.config.environment === 'development';
  }

  private parseCorsOrigins(): string[] {
    const origins = process.env.CORS_ORIGINS || 'http://localhost:3000,http://localhost:3001,http://localhost:4000';
    return origins.split(',').map((o) => o.trim());
  }
}