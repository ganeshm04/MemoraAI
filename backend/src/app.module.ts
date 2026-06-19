import { Module, MiddlewareConsumer, NestModule } from '@nestjs/common';
import { HttpModule } from '@nestjs/axios';
import { ThrottlerModule, ThrottlerGuard } from '@nestjs/throttler';
import { APP_GUARD } from '@nestjs/core';
import { ConfigModule } from './config/config.module';
import { ConfigService } from './config/config.service';
import { ApiModule } from './api/api.module';
import { HealthController } from './api/routes/health.controller';
import { LoggingMiddleware } from './middleware/logging.middleware';
import { SecurityMiddleware } from './middleware/security.middleware';

@Module({
  imports: [
    ThrottlerModule.forRoot([{
      ttl: 60000,
      limit: 30, // 30 requests per minute
    }]),
    ConfigModule,
    ApiModule,
    HttpModule,
  ],
  controllers: [HealthController],
  providers: [
    ConfigService,
    {
      provide: APP_GUARD,
      useClass: ThrottlerGuard,
    },
  ],
})
export class AppModule implements NestModule {
  configure(consumer: MiddlewareConsumer) {
    consumer
      .apply(LoggingMiddleware)
      .forRoutes('*');
    
    consumer
      .apply(SecurityMiddleware)
      .forRoutes('*');
  }
}