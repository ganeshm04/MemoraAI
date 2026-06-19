import { Injectable, NestMiddleware } from '@nestjs/common';
import { Request, Response, NextFunction } from 'express';
import { v4 as uuidv4 } from 'uuid';
import { Logger } from '@nestjs/common';
import { requestContext } from './request-context';

@Injectable()
export class LoggingMiddleware implements NestMiddleware {
  private readonly logger = new Logger('HTTP');

  use(req: Request, res: Response, next: NextFunction) {
    const requestId = (req.headers['x-request-id'] as string) || uuidv4();
    const startTime = Date.now();

    req.headers['x-request-id'] = requestId;

    const { method, originalUrl, ip } = req;
    const userAgent = req.headers['user-agent'] || 'unknown';

    this.logger.log(`[${requestId}] --> ${method} ${originalUrl} - ${ip} - ${userAgent}`);

    res.on('finish', () => {
      const duration = Date.now() - startTime;
      const { statusCode } = res;

      this.logger.log(
        `[${requestId}] <-- ${method} ${originalUrl} - ${statusCode} - ${duration}ms`,
      );

      if (statusCode >= 400) {
        this.logger.warn(`[${requestId}] Request completed with error status ${statusCode}`);
      }
    });

    requestContext.run({ requestId }, () => {
      next();
    });
  }
}