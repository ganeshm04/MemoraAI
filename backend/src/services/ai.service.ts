import { Injectable, Logger, HttpException } from '@nestjs/common';
import { HttpService } from '@nestjs/axios';
import { firstValueFrom } from 'rxjs';
import { ConfigService } from '../config/config.service';
import { IngestPDFDto, IngestURLDto, IngestTextDto } from '../dto/ingest.dto';
import { QueryDto, ConversationalQueryDto } from '../dto/query.dto';
import {
  VectorSearchDto,
  BM25SearchDto,
  HybridSearchDto,
  RerankDto,
} from '../dto/search.dto';
import {
  AddMemoryDto,
  StoreFactDto,
  CreateEpisodeDto,
} from '../dto/memory.dto';

@Injectable()
export class AIService {
  private readonly logger = new Logger(AIService.name);
  private readonly baseURL: string;
  private readonly timeout: number;

  constructor(
    private readonly httpService: HttpService,
    private readonly configService: ConfigService,
  ) {
    const config = this.configService.get();
    this.baseURL = config.aiServiceUrl;
    this.timeout = config.aiServiceTimeout;
  }

  private async request<T>(method: string, path: string, data?: any): Promise<T> {
    try {
      const url = `${this.baseURL}/api/v1${path}`;
      const response = await firstValueFrom(
        this.httpService.request({
          method,
          url,
          data,
          timeout: this.timeout,
          headers: {
            'Content-Type': 'application/json',
          },
        }),
      );
      return response.data;
    } catch (error) {
      this.logger.error(`AI Service request failed: ${path}`, error?.message);
      throw new HttpException(
        error?.response?.data?.detail || 'AI service unavailable',
        error?.response?.status || 503,
      );
    }
  }

  async ingestPDF(dto: IngestPDFDto) {
    this.logger.log('Ingesting PDF', dto.file_path);
    return this.request('POST', '/ingest/pdf', dto);
  }

  async ingestURL(dto: IngestURLDto) {
    this.logger.log('Ingesting URL', dto.url);
    return this.request('POST', '/ingest/url', dto);
  }

  async ingestText(dto: IngestTextDto) {
    this.logger.log('Ingesting text', dto.source);
    return this.request('POST', '/ingest/text', dto);
  }

  async ingestBatch(sources: Array<{type: string; content: string}>) {
    this.logger.log('Batch ingestion', sources.length, 'sources');
    return this.request('POST', '/ingest/batch', sources);
  }

  async query(dto: QueryDto) {
    this.logger.log('Processing query', dto.query.substring(0, 50));
    return this.request('POST', '/query', dto);
  }

  async conversationalQuery(dto: ConversationalQueryDto) {
    this.logger.log('Processing conversational query', dto.query.substring(0, 50));
    return this.request('POST', '/query/conversational', dto);
  }

  async vectorSearch(dto: VectorSearchDto) {
    this.logger.log('Vector search', dto.query.substring(0, 50));
    return this.request('POST', '/search/vector', dto);
  }

  async bm25Search(dto: BM25SearchDto) {
    this.logger.log('BM25 search', dto.query.substring(0, 50));
    return this.request('POST', '/search/bm25', dto);
  }

  async hybridSearch(dto: HybridSearchDto) {
    this.logger.log('Hybrid search', dto.query.substring(0, 50));
    return this.request('POST', '/search/hybrid', dto);
  }

  async rerank(dto: RerankDto) {
    this.logger.log('Reranking documents', dto.documents.length);
    return this.request('POST', '/search/rerank', {
      query: dto.query,
      documents: dto.documents,
      top_k: dto.top_k,
    });
  }

  async getShortTermMemory(sessionId: string, limit?: number) {
    return this.request('GET', `/memory/short/${sessionId}${limit ? `?limit=${limit}` : ''}`);
  }

  async addShortTermMemory(dto: AddMemoryDto) {
    return this.request('POST', '/memory/short/add', dto);
  }

  async clearShortTermMemory(sessionId: string) {
    return this.request('DELETE', `/memory/short/${sessionId}`);
  }

  async getLongTermMemory(userId: string, category?: string) {
    const path = `/memory/long/${userId}${category ? `?category=${category}` : ''}`;
    return this.request('GET', path);
  }

  async storeLongTermFact(dto: StoreFactDto) {
    return this.request('POST', '/memory/long/fact', dto);
  }

  async deleteLongTermFact(userId: string, key: string) {
    return this.request('DELETE', `/memory/long/${userId}/${key}`);
  }

  async getEpisodicMemory(userId: string, limit?: number, days?: number) {
    let path = `/memory/episodic/${userId}`;
    const params = [];
    if (limit) params.push(`limit=${limit}`);
    if (days) params.push(`days=${days}`);
    if (params.length) path += `?${params.join('&')}`;
    return this.request('GET', path);
  }

  async createEpisode(dto: CreateEpisodeDto) {
    return this.request('POST', '/memory/episodic', dto);
  }

  async getMemoryStats(userId: string) {
    return this.request('GET', `/memory/stats/${userId}`);
  }
}