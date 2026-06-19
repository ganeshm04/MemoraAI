'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Brain, BookOpen, Clock, MessageSquare, ChevronDown, ChevronRight, Gauge, Star, RefreshCw } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { api } from '@/lib/api';
import { useChatStore } from '@/hooks/useChat';
import { cn } from '@/lib/utils';

interface MemoryPanelProps {
  memory?: any;
}

type MemoryTab = 'short' | 'long' | 'episodic';

export function MemoryPanel({ memory }: MemoryPanelProps) {
  const [activeTab, setActiveTab] = useState<MemoryTab>('short');
  const [shortTermData, setShortTermData] = useState<any[]>([]);
  const [longTermData, setLongTermData] = useState<any[]>([]);
  const [episodicData, setEpisodicData] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const { sessionId } = useChatStore();

  const fetchMemory = async (tab: MemoryTab) => {
    setIsLoading(true);
    try {
      if (tab === 'short') {
        const data = await api.getShortTermMemory(sessionId);
        setShortTermData(data.messages || []);
      } else if (tab === 'long') {
        const data = await api.getLongTermMemory('default-user');
        setLongTermData(data.facts || []);
      } else {
        const data = await api.getEpisodicMemory('default-user');
        setEpisodicData(data.episodes || []);
      }
    } catch (error: any) {
      console.error('Failed to fetch memory:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchMemory(activeTab);
  }, [activeTab, sessionId]);

  const tabs = [
    { id: 'short' as const, label: 'Short-Term', icon: MessageSquare, count: shortTermData.length },
    { id: 'long' as const, label: 'Long-Term', icon: BookOpen, count: longTermData.length },
    { id: 'episodic' as const, label: 'Episodic', icon: Clock, count: episodicData.length },
  ];

  return (
    <div className="space-y-5">
      {/* Memory Tabs */}
      <div className="flex gap-1 p-1 rounded-xl bg-white/[0.02] border border-white/[0.04] select-none">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              'flex-1 flex items-center justify-center gap-1.5 px-2.5 py-2 text-[9px] font-bold uppercase tracking-wider rounded-lg transition-all cursor-pointer',
              activeTab === tab.id
                ? 'bg-white/[0.04] text-zinc-100 border border-white/[0.04] shadow-sm'
                : 'text-zinc-500 hover:text-zinc-300 hover:bg-white/[0.01]'
            )}
          >
            <tab.icon className="w-3 h-3" />
            <span>{tab.label.replace('-Term', '')}</span>
            {tab.count > 0 && (
              <span className="px-1.5 py-0.5 rounded-md bg-cyan-500/10 text-cyan-300 text-[8px] font-mono font-bold border border-cyan-500/10">
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Refresh button */}
      <div className="flex justify-end select-none animate-fade-in">
        <Button variant="ghost" size="sm" onClick={() => fetchMemory(activeTab)} disabled={isLoading} className="h-7 text-[9px] font-bold uppercase tracking-wider text-zinc-500 hover:text-zinc-300 hover:bg-white/[0.02] cursor-pointer">
          <RefreshCw className={cn('w-3 h-3 mr-1', isLoading && 'animate-spin')} />
          Sync
        </Button>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-20 rounded-2xl animate-shimmer" />
          ))}
        </div>
      )}

      {/* Short-Term Memory */}
      {!isLoading && activeTab === 'short' && (
        <div className="space-y-2.5">
          {shortTermData.length === 0 ? (
            <EmptyState label="No local buffer" desc="Active messages from this session will render here." />
          ) : (
            shortTermData.map((msg: any, idx: number) => (
              <motion.div
                key={msg.id || idx}
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.02 }}
                className="p-3.5 rounded-xl bg-white/[0.01] border border-white/[0.04] hover:bg-white/[0.015] hover:border-white/[0.06] transition-all"
              >
                <div className="flex items-center gap-2 mb-2 select-none">
                  <Badge className={cn(
                    'text-[8px] font-mono font-bold uppercase px-1.5 py-0.5 h-auto border-0 rounded-md',
                    msg.role === 'user' ? 'bg-blue-500/10 text-blue-400 border border-blue-500/10' : 'bg-violet-500/10 text-violet-400 border border-violet-500/10'
                  )}>
                    {msg.role}
                  </Badge>
                  <span className="text-[9px] text-zinc-500 font-mono font-medium">
                    {msg.token_count} tokens
                  </span>
                </div>
                <p className="text-xs text-zinc-400 line-clamp-3 select-text leading-relaxed">{msg.content}</p>
                <p className="text-[9px] text-zinc-600 mt-2 select-none font-mono">
                  {msg.created_at ? new Date(msg.created_at).toLocaleTimeString() : ''}
                </p>
              </motion.div>
            ))
          )}
        </div>
      )}

      {/* Long-Term Memory */}
      {!isLoading && activeTab === 'long' && (
        <div className="space-y-2.5">
          {longTermData.length === 0 ? (
            <EmptyState label="No persistent facts" desc="User profile facts and structured context will be stored here." />
          ) : (
            longTermData.map((fact: any, idx: number) => (
              <motion.div
                key={fact.id || idx}
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.02 }}
                className="p-3.5 rounded-xl bg-white/[0.01] border border-white/[0.04] hover:bg-white/[0.015] hover:border-white/[0.06] transition-all"
              >
                <div className="flex items-center justify-between mb-2 select-none">
                  <span className="text-xs font-bold text-zinc-200">{fact.key}</span>
                  <ConfidenceMeter value={fact.confidence || 1} />
                </div>
                <p className="text-xs text-zinc-400 select-text leading-relaxed">{fact.value}</p>
                <div className="flex items-center gap-2 mt-3 select-none">
                  <Badge variant="secondary" className="text-[8px] font-mono tracking-wide px-1.5 py-0.5 h-auto bg-white/[0.02] border-white/[0.04] text-zinc-400 rounded-md">
                    {fact.category}
                  </Badge>
                  <span className="text-[9px] text-zinc-600 font-mono">{fact.source}</span>
                </div>
              </motion.div>
            ))
          )}
        </div>
      )}

      {/* Episodic Memory */}
      {!isLoading && activeTab === 'episodic' && (
        <div className="space-y-2.5">
          {episodicData.length === 0 ? (
            <EmptyState label="No episodic memory" desc="Historical sessions and user sentiment markers will compile here." />
          ) : (
            episodicData.map((episode: any, idx: number) => (
              <motion.div
                key={episode.id || idx}
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.02 }}
                className="p-3.5 rounded-xl bg-white/[0.01] border border-white/[0.04] hover:bg-white/[0.015] hover:border-white/[0.06] transition-all"
              >
                <div className="flex items-center justify-between gap-2 mb-2 select-none">
                  <div className="flex items-center gap-2">
                    <div className={cn('w-1.5 h-1.5 rounded-full shadow-sm',
                      episode.sentiment === 'positive' ? 'bg-emerald-500 shadow-emerald-500/25' :
                      episode.sentiment === 'negative' ? 'bg-rose-500 shadow-rose-500/25' :
                      'bg-amber-500 shadow-amber-500/25'
                    )} />
                    <span className="text-[9px] text-zinc-500 font-mono font-medium">
                      {episode.created_at ? new Date(episode.created_at).toLocaleDateString() : 'Session'}
                    </span>
                  </div>
                  {episode.message_count > 0 && (
                    <Badge variant="secondary" className="text-[8px] font-mono px-1.5 py-0.5 h-auto bg-white/[0.02] border-white/[0.04] text-zinc-400 rounded-md">
                      {episode.message_count} messages
                    </Badge>
                  )}
                </div>
                <p className="text-xs text-zinc-400 select-text leading-relaxed mb-3">{episode.summary}</p>
                {episode.key_topics && episode.key_topics.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 select-none">
                    {episode.key_topics.map((topic: string, i: number) => (
                      <Badge key={i} variant="outline" className="text-[8px] font-mono tracking-wide px-1.5 py-0.5 h-auto border-cyan-500/10 text-cyan-400 bg-cyan-500/[0.02] rounded-md">
                        #{topic}
                      </Badge>
                    ))}
                  </div>
                )}
              </motion.div>
            ))
          )}
        </div>
      )}
    </div>
  );
}

function ConfidenceMeter({ value }: { value: number }) {
  return (
    <div className="flex items-center gap-1.5 select-none">
      <div className="w-12 h-1 rounded-full bg-white/[0.04] border border-white/[0.02] overflow-hidden">
        <div
          className={cn('h-full rounded-full',
            value >= 0.8 ? 'bg-emerald-500' : value >= 0.5 ? 'bg-amber-500' : 'bg-rose-500'
          )}
          style={{ width: `${Math.round(value * 100)}%` }}
        />
      </div>
      <span className="text-[8px] text-zinc-500 font-mono font-bold">{Math.round(value * 100)}%</span>
    </div>
  );
}

function EmptyState({ label, desc }: { label: string; desc: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center select-none">
      <div className="w-10 h-10 rounded-xl bg-white/[0.02] border border-white/[0.04] flex items-center justify-center mb-3">
        <Brain className="w-5 h-5 text-zinc-600" />
      </div>
      <p className="text-xs font-bold text-zinc-400 mb-0.5">{label}</p>
      <p className="text-[10px] text-zinc-500 max-w-[200px] leading-normal">{desc}</p>
    </div>
  );
}