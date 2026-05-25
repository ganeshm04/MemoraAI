import { Module, MiddlewareConsumer, NestModule } from '@nestjs/common';
import { ConfigModule } from './config/config.module';
import { ConfigService } from './config/config.service';
import { ApiModule } from './api/api.module';
import { HealthController } from './api/routes/health.controller';
import { LoggingMiddleware } from './middleware/logging.middleware';
import { SecurityMiddleware } from './middleware/security.middleware';

@Module({
  imports: [
    ConfigModule,
    ApiModule,
  ],
  controllers: [HealthController],
  providers: [ConfigService],
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