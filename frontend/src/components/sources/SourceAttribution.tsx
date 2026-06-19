'use client';

import { motion } from 'framer-motion';
import { FileText, Globe, Type, ExternalLink, BookOpen } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface SourceAttributionProps {
  sources: string[];
}

function getSourceType(source: string): { type: string; icon: any; color: string } {
  if (source.startsWith('http://') || source.startsWith('https://')) {
    return { type: 'URL', icon: Globe, color: 'bg-emerald-500/20 text-emerald-400' };
  }
  if (source.endsWith('.pdf') || source.includes('.pdf')) {
    return { type: 'PDF', icon: FileText, color: 'bg-blue-500/20 text-blue-400' };
  }
  return { type: 'Text', icon: Type, color: 'bg-amber-500/20 text-amber-400' };
}

function getSourceLabel(source: string): string {
  if (source.startsWith('http://') || source.startsWith('https://')) {
    try {
      const url = new URL(source);
      return url.hostname + (url.pathname !== '/' ? url.pathname.slice(0, 30) : '');
    } catch {
      return source.slice(0, 40);
    }
  }
  // Extract filename from path
  const parts = source.split(/[/\\]/);
  return parts[parts.length - 1] || source;
}

export function SourceAttribution({ sources }: SourceAttributionProps) {
  if (!sources || sources.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center select-none">
        <div className="w-12 h-12 rounded-xl bg-white/[0.02] border border-white/[0.04] flex items-center justify-center mb-3">
          <BookOpen className="w-5 h-5 text-zinc-600" />
        </div>
        <p className="text-xs font-bold text-zinc-400 mb-0.5">No active sources</p>
        <p className="text-[10px] text-zinc-500 max-w-[200px] leading-normal">
          Documents referenced in queries will list here.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3.5">
      <h3 className="text-xs font-bold text-zinc-300 uppercase tracking-wider flex items-center gap-1.5 select-none">
        <BookOpen className="w-3.5 h-3.5 text-cyan-400" />
        Active Database
        <span className="px-1.5 py-0.5 rounded-full bg-white/[0.02] border border-white/[0.06] text-[9px] font-mono font-bold">{sources.length}</span>
      </h3>

      <div className="space-y-2">
        {sources.map((source, index) => {
          const { type, icon: Icon, color } = getSourceType(source);
          const label = getSourceLabel(source);
          const isLink = source.startsWith('http://') || source.startsWith('https://');

          return (
            <motion.div
              key={source}
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.03 }}
              className="flex items-center gap-3 p-3 rounded-xl bg-white/[0.01] border border-white/[0.04] hover:bg-white/[0.02] hover:border-white/[0.08] transition-colors group"
            >
              <div className={cn('w-8 h-8 rounded-lg flex items-center justify-center shrink-0 border select-none', color)}>
                <Icon className="w-3.5 h-3.5" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-bold text-zinc-200 truncate select-text">{label}</p>
                <p className="text-[9px] text-zinc-500 font-mono truncate select-text mt-0.5">{source}</p>
              </div>
              <Badge className={cn('text-[8px] font-mono tracking-wide uppercase px-1.5 py-0.5 h-auto border-0 shrink-0 rounded-md', color)}>
                {type}
              </Badge>
              {isLink && (
                <a
                  href={source}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="opacity-0 group-hover:opacity-100 transition-opacity shrink-0 cursor-pointer"
                >
                  <ExternalLink className="w-3.5 h-3.5 text-cyan-400 hover:text-cyan-300" />
                </a>
              )}
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}