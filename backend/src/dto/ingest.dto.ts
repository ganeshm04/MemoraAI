import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { IsString, IsOptional, IsNumber, IsObject, Min, Max } from 'class-validator';

export class IngestPDFDto {
  @ApiProperty({ description: 'Path to PDF file' })
  @IsString()
  file_path: string;

  @ApiPropertyOptional({ description: 'Additional metadata' })
  @IsOptional()
  @IsObject()
  metadata?: Record<string, any>;

  @ApiPropertyOptional({ description: 'Chunk size in tokens' })
  @IsOptional()
  @IsNumber()
  @Min(100)
  @Max(2000)
  chunk_size?: number = 700;

  @ApiPropertyOptional({ description: 'Chunk overlap in tokens' })
  @IsOptional()
  @IsNumber()
  @Min(0)
  @Max(500)
  chunk_overlap?: number = 100;
}

export class IngestURLDto {
  @ApiProperty({ description: 'URL to scrape' })
  @IsString()
  url: string;

  @ApiPropertyOptional({ description: 'Additional metadata' })
  @IsOptional()
  @IsObject()
  metadata?: Record<string, any>;

  @ApiPropertyOptional({ description: 'Chunk size' })
  @IsOptional()
  @IsNumber()
  chunk_size?: number = 700;

  @ApiPropertyOptional({ description: 'Chunk overlap' })
  @IsOptional()
  @IsNumber()
  chunk_overlap?: number = 100;
}

export class IngestTextDto {
  @ApiProperty({ description: 'Text content to ingest' })
  @IsString()
  text: string;

  @ApiProperty({ description: 'Source identifier' })
  @IsString()
  source: string;

  @ApiPropertyOptional({ description: 'Additional metadata' })
  @IsOptional()
  @IsObject()
  metadata?: Record<string, any>;

  @ApiPropertyOptional({ description: 'Chunk size' })
  @IsOptional()
  @IsNumber()
  chunk_size?: number = 700;

  @ApiPropertyOptional({ description: 'Chunk overlap' })
  @IsOptional()
  @IsNumber()
  chunk_overlap?: number = 100;
}