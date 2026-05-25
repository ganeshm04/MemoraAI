import { NestFactory } from '@nestjs/core';
import { ValidationPipe, Logger } from '@nestjs/common';
import { AppModule } from './app.module';
import { ConfigService } from './config/config.service';
import helmet from 'helmet';
import * as compression from 'compression';

async function bootstrap() {
  const logger = new Logger('Bootstrap');
  
  const app = await NestFactory.create(AppModule, {
    logger: ['error', 'warn', 'log', 'debug', 'verbose'],
  });

  const configService = app.get(ConfigService);
  const config = configService.get();

  app.use(helmet());
  app.use(compression());
  
  app.enableCors({
    origin: config.corsOrigins,
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization', 'X-Request-ID'],
  });

  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      forbidNonWhitelisted: true,
      transform: true,
      transformOptions: {
        enableImplicitConversion: true,
      },
    }),
  );

  app.setGlobalPrefix('api/v1', {
    exclude: ['health'],
  });

  const port = config.port || 3000;
  const host = config.host || '0.0.0.0';

  await app.listen(port, host);
  
  logger.log(`🚀 MemoraAI Backend running on http://${host}:${port}`);
  logger.log(`📚 API Documentation: http://${host}:${port}/api/docs`);
}

bootstrap();