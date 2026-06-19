import { Controller, Get, Logger } from '@nestjs/common';
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
}