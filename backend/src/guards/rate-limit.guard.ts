import { Injectable, CanActivate, ExecutionContext } from '@nestjs/common';
import { ThrottlerGuard, ThrottlerException } from '@nestjs/throttler';

@Injectable()
export class RateLimitGuard extends ThrottlerGuard {
  protected async throwThrottlingException(): Promise<void> {
    throw new ThrottlerException('Rate limit exceeded. Please try again later.');
  }

  protected async getTracker(req: ExecutionContext): Promise<string> {
    const request = req.switchToHttp().getRequest();
    return request.ip || request.headers['x-forwarded-for'] || 'unknown';
  }
}