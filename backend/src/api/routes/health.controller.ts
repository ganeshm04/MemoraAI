import { Controller, Get, Logger, Headers, HttpException, HttpStatus } from '@nestjs/common';
import { ApiTags, ApiOperation } from '@nestjs/swagger';
import { HttpService } from '@nestjs/axios';
import { ConfigService } from '../../config/config.service';
import { firstValueFrom } from 'rxjs';

@ApiTags('health')
@Controller('health')
export class HealthController {
  private readonly logger = new Logger(HealthController.name);

  constructor(
    private readonly httpService: HttpService,
    private readonly configService: ConfigService,
  ) {}

  @Get()
  @ApiOperation({ summary: 'Health check endpoint' })
  async check() {
    const config = this.configService.get();
    let aiServiceStatus = 'unknown';
    let aiServiceLatency = -1;

    const start = Date.now();
    try {
      await firstValueFrom(
        this.httpService.get(`${config.aiServiceUrl}/api/v1/health/live`, {
          timeout: 5000,
        }),
      );
      aiServiceStatus = 'connected';
      aiServiceLatency = Date.now() - start;
    } catch (error) {
      aiServiceStatus = 'disconnected';
      aiServiceLatency = Date.now() - start;
      this.logger.warn('AI service health check failed');
    }

    return {
      status: aiServiceStatus === 'connected' ? 'healthy' : 'degraded',
      timestamp: new Date().toISOString(),
      service: 'memora-backend',
      version: '1.0.0',
      dependencies: {
        ai_service: {
          status: aiServiceStatus,
          latency_ms: aiServiceLatency,
        },
      },
    };
  }

  @Get('ready')
  @ApiOperation({ summary: 'Readiness check' })
  async ready() {
    const config = this.configService.get();
    try {
      await firstValueFrom(
        this.httpService.get(`${config.aiServiceUrl}/api/v1/health/ready`, {
          timeout: 5000,
        }),
      );
      return { ready: true, checks: { api: 'ok', ai_service: 'ok' } };
    } catch {
      return { ready: false, checks: { api: 'ok', ai_service: 'unreachable' } };
    }
  }

  @Get('live')
  @ApiOperation({ summary: 'Liveness check' })
  live() {
    return { alive: true, timestamp: new Date().toISOString() };
  }

  @Get('metrics/dashboard')
  @ApiOperation({ summary: 'Get aggregated JSON metrics for UI dashboard' })
  async getDashboardMetrics(@Headers('x-metrics-token') token?: string) {
    const config = this.configService.get();
    
    if (config.metricsToken && token !== config.metricsToken) {
      throw new HttpException('Unauthorized access to dashboard metrics', HttpStatus.UNAUTHORIZED);
    }

    try {
      const response = await firstValueFrom(
        this.httpService.get(`${config.aiServiceUrl}/api/v1/health/metrics/dashboard`, {
          timeout: 5000,
        }),
      );
      return response.data;
    } catch (error) {
      this.logger.error('Failed to fetch dashboard metrics from AI service', error.stack);
      return {
        retrieval: {
          search_counts: { vector: 0, bm25: 0, hybrid: 0, total: 0 },
          avg_durations: { vector: 0, bm25: 0, hybrid: 0, fusion: 0, rerank: 0 },
          total_fusions: 0,
          total_reranks: 0
        },
        generation: {
          total_generations: 0,
          avg_duration_ms: 0,
          total_tokens: 0,
          avg_tokens_per_req: 0
        },
        embedding: {
          total_embeddings: 0,
          avg_duration_ms: 0
        },
        memory: {
          reads: { short_term: 0, long_term: 0, episodic: 0, total: 0 },
          writes: { short_term: 0, long_term: 0, episodic: 0, total: 0 }
        }
      };
    }
  }
}