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
import { QueryDto, ConversationalQueryDto } from '../../dto/query.dto';

@ApiTags('query')
@Controller('query')
export class QueryController {
  constructor(
    private readonly aiService: AIService,
    private readonly validationService: ValidationService,
  ) {}

  @Post()
  @HttpCode(HttpStatus.OK)
  @ApiOperation({ summary: 'Main query endpoint' })
  @ApiResponse({ status: 200, description: 'Query processed' })
  @ApiResponse({ status: 400, description: 'Invalid query' })
  async query(@Body() dto: QueryDto) {
    const errors = this.validationService.validateQuery(dto.query);
    if (errors.length > 0) {
      throw new BadRequestException(errors);
    }

    return this.aiService.query(dto);
  }

  @Post('conversational')
  @HttpCode(HttpStatus.OK)
  @ApiOperation({ summary: 'Conversational query' })
  @ApiResponse({ status: 200, description: 'Query processed' })
  async conversationalQuery(@Body() dto: ConversationalQueryDto) {
    return this.aiService.conversationalQuery(dto);
  }
}