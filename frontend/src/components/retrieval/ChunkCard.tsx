'use client';

import { ChevronDown, ChevronUp, ExternalLink, Hash } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { cn, calculateSimilarityPercent, getScoreColor, getScoreLabel } from '@/lib/utils';
import type { RetrievedChunk } from '@/types';

interface ChunkCardProps {
  chunk: RetrievedChunk;
  index: number;
  isExpanded: boolean;
  onToggle: () => void;
}

export function ChunkCard({ chunk, index, isExpanded, onToggle }: ChunkCardProps) {
  const fusedPercent = calculateSimilarityPercent(chunk.fused_score);
  const vectorPercent = calculateSimilarityPercent(chunk.vector_score || 0);
  const bm25Percent = calculateSimilarityPercent(chunk.bm25_score || 0);
  const rerankPercent = calculateSimilarityPercent(chunk.rerank_score || 0);

  return (
    <Card className="overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full p-4 text-left hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors"
      >
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <Badge variant="outline" className="text-xs">
                <Hash className="w-3 h-3 mr-1" />
                {index + 1}
              </Badge>
              <Badge className={cn('text-xs', getScoreColor(chunk.fused_score))}>
                {getScoreLabel(chunk.fused_score)}
              </Badge>
            </div>
            <p className="text-sm text-slate-600 dark:text-slate-300 truncate">
              {chunk.content.slice(0, 100)}...
            </p>
            <p className="text-xs text-slate-400 dark:text-slate-500 mt-1 truncate">
              {chunk.source}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-primary">
              {fusedPercent}%
            </span>
            {isExpanded ? (
              <ChevronUp className="w-4 h-4 text-slate-400" />
            ) : (
              <ChevronDown className="w-4 h-4 text-slate-400" />
            )}
          </div>
        </div>
      </button>

      {isExpanded && (
        <div className="px-4 pb-4 space-y-4">
          <div className="border-t border-slate-100 dark:border-slate-700 pt-4">
            <h4 className="text-sm font-medium mb-2">Content</h4>
            <p className="text-sm text-slate-600 dark:text-slate-300 whitespace-pre-wrap">
              {chunk.content}
            </p>
          </div>

          <div className="space-y-3">
            <h4 className="text-sm font-medium">Score Breakdown</h4>
            
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-500">Fused Score</span>
                <span className="font-medium">{fusedPercent}%</span>
              </div>
              <Progress value={fusedPercent} className="h-2" />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-500">Vector Similarity</span>
                <span className="font-medium">{vectorPercent}%</span>
              </div>
              <Progress value={vectorPercent} className="h-2" />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-500">BM25 Score</span>
                <span className="font-medium">{bm25Percent}%</span>
              </div>
              <Progress value={bm25Percent} className="h-2" />
            </div>

            {chunk.rerank_score > 0 && (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-500">Rerank Score</span>
                  <span className="font-medium">{rerankPercent}%</span>
                </div>
                <Progress value={rerankPercent} className="h-2" />
              </div>
            )}
          </div>

          <div className="pt-2">
            <a
              href={chunk.source}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
            >
              <ExternalLink className="w-4 h-4" />
              View source
            </a>
          </div>
        </div>
      )}
    </Card>
  );
}