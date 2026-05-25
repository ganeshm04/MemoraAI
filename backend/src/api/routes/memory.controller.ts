import {
  Controller,
  Get,
  Post,
  Delete,
  Body,
  Param,
  HttpCode,
  HttpStatus,
} from '@nestjs/common';
import {
  ApiTags,
  ApiOperation,
  ApiResponse,
  ApiParam,
} from '@nestjs/swagger';
import { AIService } from '../../services/ai.service';
import {
  AddMemoryDto,
  StoreFactDto,
  CreateEpisodeDto,
} from '../../dto/memory.dto';

@ApiTags('memory')
@Controller('memory')
export class MemoryController {
  constructor(private readonly aiService: AIService) {}

  @Get('short/:sessionId')
  @ApiOperation({ summary: 'Get short-term memory' })
  @ApiParam({ name: 'sessionId', description: 'Session identifier' })
  async getShortTermMemory(
    @Param('sessionId') sessionId: string,
    @Body('limit') limit?: number,
  ) {
    return this.aiService.getShortTermMemory(sessionId, limit);
  }

  @Post('short')
  @HttpCode(HttpStatus.CREATED)
  @ApiOperation({ summary: 'Add to short-term memory' })
  async addShortTermMemory(@Body() dto: AddMemoryDto) {
    return this.aiService.addShortTermMemory(dto);
  }

  @Delete('short/:sessionId')
  @ApiOperation({ summary: 'Clear short-term memory' })
  async clearShortTermMemory(@Param('sessionId') sessionId: string) {
    return this.aiService.clearShortTermMemory(sessionId);
  }

  @Get('long/:userId')
  @ApiOperation({ summary: 'Get long-term memory' })
  @ApiParam({ name: 'userId', description: 'User identifier' })
  async getLongTermMemory(
    @Param('userId') userId: string,
    @Body('category') category?: string,
  ) {
    return this.aiService.getLongTermMemory(userId, category);
  }

  @Post('long')
  @HttpCode(HttpStatus.CREATED)
  @ApiOperation({ summary: 'Store fact in long-term memory' })
  async storeLongTermFact(@Body() dto: StoreFactDto) {
    return this.aiService.storeLongTermFact(dto);
  }

  @Delete('long/:userId/:key')
  @ApiOperation({ summary: 'Delete fact from long-term memory' })
  async deleteLongTermFact(
    @Param('userId') userId: string,
    @Param('key') key: string,
  ) {
    return this.aiService.deleteLongTermFact(userId, key);
  }

  @Get('episodic/:userId')
  @ApiOperation({ summary: 'Get episodic memory' })
  @ApiParam({ name: 'userId', description: 'User identifier' })
  async getEpisodicMemory(
    @Param('userId') userId: string,
    @Body('limit') limit?: number,
    @Body('days') days?: number,
  ) {
    return this.aiService.getEpisodicMemory(userId, limit, days);
  }

  @Post('episodic')
  @HttpCode(HttpStatus.CREATED)
  @ApiOperation({ summary: 'Create episodic memory' })
  async createEpisode(@Body() dto: CreateEpisodeDto) {
    return this.aiService.createEpisode(dto);
  }

  @Get('stats/:userId')
  @ApiOperation({ summary: 'Get memory statistics' })
  async getMemoryStats(@Param('userId') userId: string) {
    return this.aiService.getMemoryStats(userId);
  }
}