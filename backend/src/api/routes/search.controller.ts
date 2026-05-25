import {
  Controller,
  Post,
  Body,
  HttpCode,
  HttpStatus,
  BadRequestException,
} from '@nestjs/common';
import {
  ApiTags,
  ApiOperation,
  ApiResponse,
} from '@nestjs/swagger';
import { AIService } from '../../services/ai.service';
import { ValidationService } from '../../services/validation.service';
import {
  VectorSearchDto,
  BM25SearchDto,
  HybridSearchDto,
  RerankDto,
} from '../../dto/search.dto';

@ApiTags('search')
@Controller('search')
export class SearchController {
  constructor(
    private readonly aiService: AIService,
    private readonly validationService: ValidationService,
  ) {}

  @Post('vector')
  @HttpCode(HttpStatus.OK)
  @ApiOperation({ summary: 'Vector similarity search' })
  @ApiResponse({ status: 200, description: 'Search completed' })
  async vectorSearch(@Body() dto: VectorSearchDto) {
    return this.aiService.vectorSearch(dto);
  }

  @Post('bm25')
  @HttpCode(HttpStatus.OK)
  @ApiOperation({ summary: 'BM25 keyword search' })
  @ApiResponse({ status: 200, description: 'Search completed' })
  async bm25Search(@Body() dto: BM25SearchDto) {
    return this.aiService.bm25Search(dto);
  }

  @Post('hybrid')
  @HttpCode(HttpStatus.OK)
  @ApiOperation({ summary: 'Hybrid search with RRF' })
  @ApiResponse({ status: 200, description: 'Search completed' })
  async hybridSearch(@Body() dto: HybridSearchDto) {
    return this.aiService.hybridSearch(dto);
  }

  @Post('rerank')
  @HttpCode(HttpStatus.OK)
  @ApiOperation({ summary: 'Standalone reranking' })
  @ApiResponse({ status: 200, description: 'Reranking completed' })
  async rerank(@Body() dto: RerankDto) {
    return this.aiService.rerank(dto);
  }
}