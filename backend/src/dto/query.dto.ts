import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { IsString, IsOptional, IsNumber, IsBoolean, Min, Max } from 'class-validator';

export class QueryDto {
  @ApiProperty({ description: 'User query' })
  @IsString()
  query: string;

  @ApiProperty({ description: 'Session identifier' })
  @IsString()
  session_id: string;

  @ApiPropertyOptional({ description: 'User identifier' })
  @IsOptional()
  @IsString()
  user_id?: string;

  @ApiPropertyOptional({ description: 'Include memory context' })
  @IsOptional()
  @IsBoolean()
  use_memory?: boolean = true;

  @ApiPropertyOptional({ description: 'Use reranking' })
  @IsOptional()
  @IsBoolean()
  use_reranking?: boolean = true;

  @ApiPropertyOptional({ description: 'Generation temperature' })
  @IsOptional()
  @IsNumber()
  @Min(0)
  @Max(2)
  temperature?: number = 0.7;

  @ApiPropertyOptional({ description: 'Max tokens' })
  @IsOptional()
  @IsNumber()
  @Min(1)
  @Max(8192)
  max_tokens?: number = 2048;
}

export class ConversationalQueryDto {
  @ApiProperty({ description: 'User query' })
  @IsString()
  query: string;

  @ApiProperty({ description: 'Session identifier' })
  @IsString()
  session_id: string;

  @ApiPropertyOptional({ description: 'User identifier' })
  @IsOptional()
  @IsString()
  user_id?: string;

  @ApiPropertyOptional({ description: 'Temperature' })
  @IsOptional()
  @IsNumber()
  temperature?: number = 0.7;

  @ApiPropertyOptional({ description: 'Max tokens' })
  @IsOptional()
  @IsNumber()
  max_tokens?: number = 2048;
}