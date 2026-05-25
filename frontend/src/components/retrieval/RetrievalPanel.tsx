'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, ChevronUp, ExternalLink, Database } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
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
      <div className="text-center py-8">
        <Database className="w-12 h-12 mx-auto text-slate-300 dark:text-slate-600 mb-3" />
        <p className="text-slate-500 dark:text-slate-400 text-sm">
          No retrieval results yet. Ask a question to see retrieved chunks.
        </p>
      </div>
    );
  }

  const sortedChunks = [...chunks].sort((a, b) => {
    const aScore = a[sortBy] || 0;
    const bScore = b[sortBy] || 0;
    return bScore - aScore;
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-slate-900 dark:text-white">
          Retrieved Chunks ({chunks.length})
        </h3>
        <div className="flex gap-1">
          {(['fused_score', 'vector_score', 'bm25_score', 'rerank_score'] as const).map((scoreType) => (
            <button
              key={scoreType}
              onClick={() => setSortBy(scoreType)}
              className={cn(
                'px-2 py-1 text-xs rounded transition-colors',
                sortBy === scoreType
                  ? 'bg-primary text-white'
                  : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600'
              )}
            >
              {scoreType.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-3">
        {sortedChunks.map((chunk, index) => (
          <motion.div
            key={chunk.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
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