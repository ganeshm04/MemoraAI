'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, ArrowRight, Layers, Zap, BarChart3 } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { ChunkCard } from './ChunkCard';
import { cn } from '@/lib/utils';
import type { RetrievedChunk } from '@/types';

interface RetrievalPanelProps {
  chunks: RetrievedChunk[];
}

export function RetrievalPanel({ chunks }: RetrievalPanelProps) {
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [sortBy, setSortBy] = useState<'fused_score' | 'vector_score' | 'bm25_score' | 'rerank_score'>('fused_score');

  if (chunks.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="w-14 h-14 rounded-2xl bg-muted/50 flex items-center justify-center mb-4">
          <Search className="w-7 h-7 text-muted-foreground/50" />
        </div>
        <p className="text-sm font-medium text-muted-foreground mb-1">No retrieval results</p>
        <p className="text-xs text-muted-foreground/70">
          Ask a question to see the hybrid retrieval pipeline in action
        </p>
      </div>
    );
  }

  const sortedChunks = [...chunks].sort((a, b) => {
    const aScore = a[sortBy] || 0;
    const bScore = b[sortBy] || 0;
    return bScore - aScore;
  });

  // Pipeline visualization
  const avgScores = {
    vector: chunks.reduce((s, c) => s + (c.vector_score || 0), 0) / chunks.length,
    bm25: chunks.reduce((s, c) => s + (c.bm25_score || 0), 0) / chunks.length,
    fused: chunks.reduce((s, c) => s + (c.fused_score || 0), 0) / chunks.length,
    rerank: chunks.reduce((s, c) => s + (c.rerank_score || 0), 0) / chunks.length,
  };

  return (
    <div className="space-y-5">
      {/* Pipeline Visualization */}
      <div className="p-4 rounded-2xl bg-white/[0.015] border border-white/[0.04] backdrop-blur-md">
        <div className="flex items-center justify-between mb-4 select-none">
          <div className="flex items-center gap-2">
            <Layers className="w-3.5 h-3.5 text-cyan-400" />
            <h4 className="text-xs font-bold text-zinc-300 uppercase tracking-wider">Retrieval Pipeline</h4>
          </div>
          <span className="text-[9px] font-mono text-zinc-500 font-semibold px-2 py-0.5 rounded-full bg-white/[0.02] border border-white/[0.04]">ACTIVE PATH</span>
        </div>

        {/* Node timeline map */}
        <div className="relative flex items-center justify-between py-2 select-none">
          {/* Connector line behind */}
          <div className="absolute top-1/2 left-4 right-4 h-[1px] bg-white/[0.06] -translate-y-1/2 z-0" />

          {[
            { label: 'Vector', score: avgScores.vector, color: 'border-blue-500/30 text-blue-400 bg-blue-500/10' },
            { label: 'BM25', score: avgScores.bm25, color: 'border-amber-500/30 text-amber-400 bg-amber-500/10' },
            { label: 'RRF', score: avgScores.fused, color: 'border-emerald-500/30 text-emerald-400 bg-emerald-500/10' },
            { label: 'Rerank', score: avgScores.rerank, color: 'border-violet-500/30 text-violet-400 bg-violet-500/10' },
          ].map((stage, idx) => {
            const hasScore = !isNaN(stage.score) && stage.score > 0;
            const percent = hasScore ? Math.round(stage.score * 100) : 0;
            return (
              <div key={stage.label} className="relative z-10 flex flex-col items-center gap-1.5">
                <div 
                  className={cn(
                    "w-9 h-9 rounded-full border flex flex-col items-center justify-center text-[10px] font-mono font-bold tracking-tighter transition-all",
                    hasScore ? stage.color : "border-white/[0.06] bg-zinc-900 text-zinc-600"
                  )}
                  title={`${stage.label}: ${percent}%`}
                >
                  {percent}%
                </div>
                <span className={cn(
                  "text-[9px] font-semibold tracking-wide uppercase",
                  hasScore ? "text-zinc-300" : "text-zinc-600"
                )}>
                  {stage.label}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Sort Controls */}
      <div className="flex items-center justify-between select-none">
        <h3 className="text-xs font-bold text-zinc-300 uppercase tracking-wider flex items-center gap-1.5">
          <BarChart3 className="w-3.5 h-3.5 text-cyan-400" />
          Retrieved Chunks
          <span className="px-1.5 py-0.5 rounded-full bg-white/[0.02] border border-white/[0.06] text-[9px] font-mono font-bold">{chunks.length}</span>
        </h3>
        <div className="flex gap-0.5 p-0.5 rounded-lg bg-white/[0.02] border border-white/[0.04]">
          {(['fused_score', 'vector_score', 'bm25_score', 'rerank_score'] as const).map((scoreType) => {
            const label = scoreType.replace('_score', '').replace('fused', 'rrf');
            return (
              <button
                key={scoreType}
                onClick={() => setSortBy(scoreType)}
                className={cn(
                  'px-2 py-1 text-[9px] rounded-md transition-all font-semibold uppercase tracking-wider cursor-pointer',
                  sortBy === scoreType
                    ? 'bg-cyan-600/20 text-cyan-300 border border-cyan-500/10'
                    : 'text-zinc-500 hover:text-zinc-300 hover:bg-white/[0.02]'
                )}
              >
                {label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Chunk Cards */}
      <div className="space-y-2.5">
        {sortedChunks.map((chunk, index) => (
          <motion.div
            key={chunk.id}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.03 }}
          >
            <ChunkCard
              chunk={chunk}
              index={index}
              isExpanded={expandedId === chunk.id}
              onToggle={() => setExpandedId(expandedId === chunk.id ? null : chunk.id)}
            />
          </motion.div>
        ))}
      </div>
    </div>
  );
}