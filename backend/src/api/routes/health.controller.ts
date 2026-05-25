import { Controller, Get } from '@nestjs/common';
import { ApiTags, ApiOperation } from '@nestjs/swagger';

@ApiTags('health')
@Controller('health')
export class HealthController {
  @Get()
  @ApiOperation({ summary: 'Health check endpoint' })
  check() {
    return {
      status: 'ok',
      timestamp: new Date().toISOString(),
      service: 'memora-backend',
      version: '1.0.0',
    };
  }

  @Get('ready')
  @ApiOperation({ summary: 'Readiness check' })
  ready() {
    return {
      ready: true,
      checks: {
        api: 'ok',
        service: 'ready',
      },
    };
  }

  @Get('live')
  @ApiOperation({ summary: 'Liveness check' })
  live() {
    return {
      alive: true,
    };
  }
}