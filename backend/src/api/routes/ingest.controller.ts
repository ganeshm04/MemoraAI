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
import { IngestPDFDto, IngestURLDto, IngestTextDto } from '../../dto/ingest.dto';

@ApiTags('ingestion')
@Controller('ingest')
export class IngestController {
  constructor(
    private readonly aiService: AIService,
    private readonly validationService: ValidationService,
  ) {}

  @Post('pdf')
  @HttpCode(HttpStatus.OK)
  @ApiOperation({ summary: 'Ingest PDF document' })
  @ApiResponse({ status: 200, description: 'PDF ingested successfully' })
  @ApiResponse({ status: 400, description: 'Invalid request' })
  async ingestPDF(@Body() dto: IngestPDFDto) {
    const errors = this.validationService.validateIngestion(dto);
    if (errors.length > 0) {
      throw new BadRequestException(errors);
    }

    return this.aiService.ingestPDF(dto);
  }

  @Post('url')
  @HttpCode(HttpStatus.OK)
  @ApiOperation({ summary: 'Ingest content from URL' })
  @ApiResponse({ status: 200, description: 'URL content ingested' })
  @ApiResponse({ status: 400, description: 'Invalid URL' })
  async ingestURL(@Body() dto: IngestURLDto) {
    const errors = this.validationService.validateURL(dto.url);
    if (errors.length > 0) {
      throw new BadRequestException(errors);
    }

    return this.aiService.ingestURL(dto);
  }

  @Post('text')
  @HttpCode(HttpStatus.OK)
  @ApiOperation({ summary: 'Ingest plain text' })
  @ApiResponse({ status: 200, description: 'Text ingested' })
  @ApiResponse({ status: 400, description: 'Invalid text' })
  async ingestText(@Body() dto: IngestTextDto) {
    const errors = this.validationService.validateText(dto.text);
    if (errors.length > 0) {
      throw new BadRequestException(errors);
    }

    return this.aiService.ingestText(dto);
  }

  @Post('batch')
  @HttpCode(HttpStatus.OK)
  @ApiOperation({ summary: 'Batch ingestion' })
  @ApiResponse({ status: 200, description: 'Batch processed' })
  async ingestBatch(@Body() sources: Array<{type: string; content: string}>) {
    return this.aiService.ingestBatch(sources);
  }
}