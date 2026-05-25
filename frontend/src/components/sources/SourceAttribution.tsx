'use client';

import { motion } from 'framer-motion';
import { FileText, ExternalLink, Quote } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface SourceAttributionProps {
  sources: string[];
}

export function SourceAttribution({ sources }: SourceAttributionProps) {
  if (sources.length === 0) {
    return null;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-4"
    >
      <div className="flex items-center gap-2 mb-3">
        <Quote className="w-4 h-4 text-primary" />
        <h3 className="text-sm font-medium text-slate-900 dark:text-white">
          Source Attribution
        </h3>
      </div>

      <div className="space-y-2">
        {sources.map((source, index) => (
          <motion.div
            key={source || index}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
            className={cn(
              'flex items-center justify-between p-2 rounded-lg',
              'bg-slate-50 dark:bg-slate-700/50',
              'hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors'
            )}
          >
            <div className="flex items-center gap-2 min-w-0">
              <FileText className="w-4 h-4 text-slate-400 shrink-0" />
              <span className="text-sm text-slate-700 dark:text-slate-300 truncate">
                {source || 'Unknown source'}
              </span>
            </div>
            {source && (
              <a
                href={source}
                target="_blank"
                rel="noopener noreferrer"
                className="p-1 hover:bg-slate-200 dark:hover:bg-slate-600 rounded transition-colors"
              >
                <ExternalLink className="w-4 h-4 text-slate-400" />
              </a>
            )}
          </motion.div>
        ))}
      </div>

      <p className="text-xs text-slate-400 mt-3">
        Response generated using {sources.length} source{sources.length > 1 ? 's' : ''}
      </p>
    </motion.div>
  );
}