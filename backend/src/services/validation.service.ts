import { Injectable } from '@nestjs/common';

@Injectable()
export class ValidationService {
  private readonly MAX_QUERY_LENGTH = 1000;
  private readonly MAX_TEXT_LENGTH = 1_000_000;
  private readonly MIN_TEXT_LENGTH = 1;
  private readonly MAX_URL_LENGTH = 2000;

  private readonly BLOCKED_DOMAINS = [
    'facebook.com',
    'twitter.com',
    'x.com',
    'instagram.com',
    'linkedin.com',
  ];

  private readonly URL_PATTERN = /^https?:\/\/(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|localhost|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(?::\d+)?(?:\/?|[/?]\S+)$/i;

  validateQuery(query: string): string[] {
    const errors: string[] = [];

    if (!query || typeof query !== 'string') {
      errors.push('Query must be a non-empty string');
      return errors;
    }

    const trimmed = query.trim();

    if (trimmed.length < 1) {
      errors.push('Query is too short');
    }

    if (trimmed.length > this.MAX_QUERY_LENGTH) {
      errors.push(`Query too long (max: ${this.MAX_QUERY_LENGTH} characters)`);
    }

    if (/[\x00-\x08\x0b\x0c\x0e-\x1f]/.test(trimmed)) {
      errors.push('Query contains invalid characters');
    }

    if (/<\|[a-z]+\|>/i.test(trimmed)) {
      errors.push('Query contains potential injection patterns');
    }

    return errors;
  }

  validateText(text: string): string[] {
    const errors: string[] = [];

    if (!text || typeof text !== 'string') {
      errors.push('Text must be a non-empty string');
      return errors;
    }

    if (text.length < this.MIN_TEXT_LENGTH) {
      errors.push(`Text too short (min: ${this.MIN_TEXT_LENGTH} character)`);
    }

    if (text.length > this.MAX_TEXT_LENGTH) {
      errors.push(`Text too long (max: ${this.MAX_TEXT_LENGTH} characters)`);
    }

    const nullCount = (text.match(/\x00/g) || []).length;
    if (nullCount > 0) {
      errors.push(`Text contains ${nullCount} invalid null bytes`);
    }

    return errors;
  }

  validateURL(url: string): string[] {
    const errors: string[] = [];

    if (!url || typeof url !== 'string') {
      errors.push('URL must be a non-empty string');
      return errors;
    }

    if (url.length > this.MAX_URL_LENGTH) {
      errors.push(`URL too long (max: ${this.MAX_URL_LENGTH} characters)`);
    }

    if (!this.URL_PATTERN.test(url)) {
      errors.push('Invalid URL format');
    }

    const urlLower = url.toLowerCase();
    for (const domain of this.BLOCKED_DOMAINS) {
      if (urlLower.includes(domain)) {
        errors.push(`URL contains blocked domain: ${domain}`);
      }
    }

    return errors;
  }

  validateIngestion(dto: any): string[] {
    const errors: string[] = [];

    if (dto.chunk_size !== undefined) {
      if (dto.chunk_size < 100 || dto.chunk_size > 2000) {
        errors.push('Chunk size must be between 100 and 2000');
      }
    }

    if (dto.chunk_overlap !== undefined) {
      if (dto.chunk_overlap < 0 || dto.chunk_overlap > 500) {
        errors.push('Chunk overlap must be between 0 and 500');
      }

      if (dto.chunk_size && dto.chunk_overlap >= dto.chunk_size) {
        errors.push('Chunk overlap must be less than chunk size');
      }
    }

    return errors;
  }

  validateSearchParams(dto: any): string[] {
    const errors: string[] = [];

    if (dto.top_k !== undefined) {
      if (dto.top_k < 1 || dto.top_k > 100) {
        errors.push('top_k must be between 1 and 100');
      }
    }

    if (dto.threshold !== undefined) {
      if (dto.threshold < 0 || dto.threshold > 1) {
        errors.push('threshold must be between 0 and 1');
      }
    }

    return errors;
  }

  validateMemoryParams(dto: any): string[] {
    const errors: string[] = [];

    if (dto.role && !['user', 'assistant', 'system'].includes(dto.role)) {
      errors.push('Role must be user, assistant, or system');
    }

    if (dto.confidence !== undefined) {
      if (dto.confidence < 0 || dto.confidence > 1) {
        errors.push('Confidence must be between 0 and 1');
      }
    }

    return errors;
  }
}