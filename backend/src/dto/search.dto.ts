import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { IsString, IsOptional, IsNumber, IsArray, IsBoolean, Min, Max } from 'class-validator';

export class VectorSearchDto {
  @ApiProperty({ description: 'Search query' })
  @IsString()
  query: string;

  @ApiPropertyOptional({ description: 'Number of results' })
  @IsOptional()
  @IsNumber()
  @Min(1)
  @Max(100)
  top_k?: number = 10;

  @ApiPropertyOptional({ description: 'Similarity threshold' })
  @IsOptional()
  @IsNumber()
  @Min(0)
  @Max(1)
  threshold?: number = 0.7;

  @ApiPropertyOptional({ description: 'Table to search' })
  @IsOptional()
  @IsString()
  table?: string = 'chunks';
}

export class BM25SearchDto {
  @ApiProperty({ description: 'Search query' })
  @IsString()
  query: string;

  @ApiPropertyOptional({ description: 'Number of results' })
  @IsOptional()
  @IsNumber()
  @Min(1)
  @Max(100)
  top_k?: number = 10;

  @ApiPropertyOptional({ description: 'Table to search' })
  @IsOptional()
  @IsString()
  table?: string = 'chunks';
}

export class HybridSearchDto {
  @ApiProperty({ description: 'Search query' })
  @IsString()
  query: string;

  @ApiPropertyOptional({ description: 'Number of results' })
  @IsOptional()
  @IsNumber()
  @Min(1)
  @Max(50)
  top_k?: number = 10;

  @ApiPropertyOptional({ description: 'Use reranking' })
  @IsOptional()
  @IsBoolean()
  use_reranking?: boolean = true;

  @ApiPropertyOptional({ description: 'Search weights' })
  @IsOptional()
  weights?: { vector?: number; bm25?: number };
}

export class RerankDto {
  @ApiProperty({ description: 'Query for reranking' })
  @IsString()
  query: string;

  @ApiProperty({ description: 'Documents to rerank' })
  @IsArray()
  documents: Array<{ content: string; metadata?: Record<string, any> }>;

  @ApiPropertyOptional({ description: 'Number of results' })
  @IsOptional()
  @IsNumber()
  @Min(1)
  @Max(50)
  top_k?: number = 5;
}