import { Module } from '@nestjs/common';
import { HttpModule } from '@nestjs/axios';
import { IngestController } from './routes/ingest.controller';
import { QueryController } from './routes/query.controller';
import { SearchController } from './routes/search.controller';
import { MemoryController } from './routes/memory.controller';
import { AIService } from '../services/ai.service';
import { ValidationService } from '../services/validation.service';

@Module({
  imports: [HttpModule],
  controllers: [
    IngestController,
    QueryController,
    SearchController,
    MemoryController,
  ],
  providers: [AIService, ValidationService],
  exports: [AIService, ValidationService],
})
export class ApiModule {}