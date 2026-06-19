'use client';

import { ChevronDown, ChevronUp, ExternalLink, Hash } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
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

  const scores = [
    { label: 'Fused', value: chunk.fused_score, color: 'bg-emerald-500' },
    { label: 'Vector', value: chunk.vector_score || 0, color: 'bg-blue-500' },
    { label: 'BM25', value: chunk.bm25_score || 0, color: 'bg-amber-500' },
    ...(chunk.rerank_score && chunk.rerank_score > 0 ? [{ label: 'Rerank', value: chunk.rerank_score, color: 'bg-violet-500' }] : []),
  ];

  return (
    <div className={cn(
      'rounded-xl border transition-all duration-200 overflow-hidden',
      isExpanded ? 'border-cyan-500/25 bg-white/[0.02] shadow-md shadow-black/10' : 'border-white/[0.04] bg-white/[0.01] hover:bg-white/[0.02] hover:border-white/[0.08]'
    )}>
      <button
        onClick={onToggle}
        className="w-full p-3.5 text-left cursor-pointer"
      >
        <div className="flex items-start justify-between gap-2.5">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5 mb-1.5 select-none">
              <span className="text-[9px] font-mono font-bold text-zinc-500 bg-white/[0.04] border border-white/[0.06] px-1.5 py-0.5 rounded">
                #{index + 1}
              </span>
              <Badge className={cn('text-[9px] font-semibold tracking-wide uppercase px-1.5 py-0.5 h-auto border-0 rounded-md', 
                fusedPercent >= 80 ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/10' :
                fusedPercent >= 60 ? 'bg-amber-500/10 text-amber-400 border border-amber-500/10' :
                'bg-rose-500/10 text-rose-400 border border-rose-500/10'
              )}>
                {getScoreLabel(chunk.fused_score)}
              </Badge>
            </div>
            <p className="text-xs text-zinc-400 line-clamp-2 leading-relaxed">
              {chunk.content.slice(0, 150)}
            </p>
            <p className="text-[9px] text-zinc-500 mt-2 truncate font-mono select-none">
              SOURCE: {chunk.source}
            </p>
          </div>
          <div className="flex items-center gap-2 shrink-0 select-none">
            <span className={cn('text-sm font-bold font-mono', getScoreColor(chunk.fused_score))}>
              {fusedPercent}%
            </span>
            {isExpanded ? (
              <ChevronUp className="w-3.5 h-3.5 text-zinc-500" />
            ) : (
              <ChevronDown className="w-3.5 h-3.5 text-zinc-500" />
            )}
          </div>
        </div>
      </button>

      {isExpanded && (
        <div className="px-3.5 pb-4 space-y-3.5 border-t border-white/[0.04] pt-4 bg-white/[0.005]">
          {/* Full content */}
          <div>
            <h4 className="text-[9px] font-bold text-zinc-500 uppercase tracking-wider mb-2 select-none">Content Chunk</h4>
            <p className="text-xs text-zinc-300 whitespace-pre-wrap leading-relaxed bg-black/15 p-3 rounded-lg border border-white/[0.04] select-text">
              {chunk.content}
            </p>
          </div>

          {/* Score breakdown */}
          <div>
            <h4 className="text-[9px] font-bold text-zinc-500 uppercase tracking-wider mb-2.5 select-none">Metric Breakdown</h4>
            <div className="space-y-2 select-none">
              {scores.map(({ label, value, color }) => (
                <div key={label} className="flex items-center gap-2.5">
                  <span className="text-[9px] font-bold tracking-wide uppercase text-zinc-500 w-16">{label}</span>
                  <div className="flex-1 h-1.5 rounded-full bg-white/[0.04] border border-white/[0.02] overflow-hidden">
                    <div
                      className={cn('h-full rounded-full animate-score-fill', color)}
                      style={{ width: `${Math.round(value * 100)}%` }}
                    />
                  </div>
                  <span className="text-[9px] font-mono text-zinc-400 w-8 text-right">
                    {Math.round(value * 100)}%
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Source link */}
          {chunk.source && (
            <a
              href={chunk.source}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-cyan-400 hover:text-cyan-300 transition-colors select-none cursor-pointer"
            >
              <ExternalLink className="w-3 h-3" />
              View raw source
            </a>
          )}
        </div>
      )}
    </div>
  );
}