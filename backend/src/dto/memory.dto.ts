import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import {
  IsString,
  IsOptional,
  IsNumber,
  IsArray,
  IsEnum,
  Min,
  Max,
} from 'class-validator';

export class AddMemoryDto {
  @ApiProperty({ description: 'Session identifier' })
  @IsString()
  session_id: string;

  @ApiProperty({ description: 'Message role' })
  @IsString()
  role: string;

  @ApiProperty({ description: 'Message content' })
  @IsString()
  content: string;

  @ApiPropertyOptional({ description: 'Additional metadata' })
  @IsOptional()
  metadata?: Record<string, any>;
}

export class StoreFactDto {
  @ApiProperty({ description: 'User identifier' })
  @IsString()
  user_id: string;

  @ApiProperty({ description: 'Fact key' })
  @IsString()
  key: string;

  @ApiProperty({ description: 'Fact value' })
  @IsString()
  value: string;

  @ApiPropertyOptional({ description: 'Category' })
  @IsOptional()
  @IsString()
  category?: string = 'general';

  @ApiPropertyOptional({ description: 'Confidence' })
  @IsOptional()
  @IsNumber()
  @Min(0)
  @Max(1)
  confidence?: number = 1.0;

  @ApiPropertyOptional({ description: 'Source' })
  @IsOptional()
  @IsString()
  source?: string = 'conversation';
}

export class CreateEpisodeDto {
  @ApiProperty({ description: 'User identifier' })
  @IsString()
  user_id: string;

  @ApiProperty({ description: 'Session identifier' })
  @IsString()
  session_id: string;

  @ApiProperty({ description: 'Session summary' })
  @IsString()
  summary: string;

  @ApiPropertyOptional({ description: 'Key topics' })
  @IsOptional()
  @IsArray()
  key_topics?: string[] = [];

  @ApiPropertyOptional({ description: 'Important facts' })
  @IsOptional()
  @IsArray()
  important_facts?: string[] = [];

  @ApiPropertyOptional({ description: 'Sentiment' })
  @IsOptional()
  @IsString()
  sentiment?: string = 'neutral';

  @ApiPropertyOptional({ description: 'Duration in minutes' })
  @IsOptional()
  @IsNumber()
  duration_minutes?: number = 0;

  @ApiPropertyOptional({ description: 'Message count' })
  @IsOptional()
  @IsNumber()
  message_count?: number = 0;
}