'use client';

import { useState } from 'react';
import { Brain, Clock, Star, MessageSquare } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useMemoryStore } from '@/hooks/useMemory';
import { cn, formatDate } from '@/lib/utils';

interface MemoryPanelProps {
  memory: any;
}

export function MemoryPanel({ memory }: MemoryPanelProps) {
  const [activeTab, setActiveTab] = useState<'short' | 'long' | 'episodic'>('short');
  const { shortTerm, longTerm, episodic, stats } = useMemoryStore();

  if (!memory && shortTerm.length === 0 && longTerm.length === 0 && episodic.length === 0) {
    return (
      <div className="text-center py-8">
        <Brain className="w-12 h-12 mx-auto text-slate-300 dark:text-slate-600 mb-3" />
        <p className="text-slate-500 dark:text-slate-400 text-sm">
          No memory data yet. Start chatting to build memory.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <button
          onClick={() => setActiveTab('short')}
          className={cn(
            'flex-1 px-3 py-2 text-xs font-medium rounded-lg transition-colors',
            activeTab === 'short'
              ? 'bg-primary text-white'
              : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300'
          )}
        >
          <Clock className="w-4 h-4 inline mr-1" />
          Short
        </button>
        <button
          onClick={() => setActiveTab('long')}
          className={cn(
            'flex-1 px-3 py-2 text-xs font-medium rounded-lg transition-colors',
            activeTab === 'long'
              ? 'bg-primary text-white'
              : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300'
          )}
        >
          <Star className="w-4 h-4 inline mr-1" />
          Long
        </button>
        <button
          onClick={() => setActiveTab('episodic')}
          className={cn(
            'flex-1 px-3 py-2 text-xs font-medium rounded-lg transition-colors',
            activeTab === 'episodic'
              ? 'bg-primary text-white'
              : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300'
          )}
        >
          <MessageSquare className="w-4 h-4 inline mr-1" />
          Episodic
        </button>
      </div>

      {activeTab === 'short' && (
        <div className="space-y-2">
          {shortTerm.length === 0 ? (
            <p className="text-sm text-slate-500 text-center py-4">No short-term memory</p>
          ) : (
            shortTerm.slice(-5).reverse().map((entry, idx) => (
              <div
                key={entry.id || idx}
                className="p-3 rounded-lg bg-slate-50 dark:bg-slate-700/50 text-sm"
              >
                <Badge variant="outline" className="mb-2">
                  {entry.role}
                </Badge>
                <p className="text-slate-700 dark:text-slate-300 truncate">
                  {entry.content.slice(0, 100)}
                </p>
                {entry.created_at && (
                  <p className="text-xs text-slate-400 mt-1">
                    {formatDate(entry.created_at)}
                  </p>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {activeTab === 'long' && (
        <div className="space-y-2">
          {longTerm.length === 0 ? (
            <p className="text-sm text-slate-500 text-center py-4">No long-term memory</p>
          ) : (
            longTerm.map((fact, idx) => (
              <div
                key={fact.id || idx}
                className="p-3 rounded-lg bg-slate-50 dark:bg-slate-700/50"
              >
                <div className="flex items-center justify-between mb-1">
                  <Badge>{fact.category}</Badge>
                  <span className="text-xs text-slate-400">
                    {Math.round(fact.confidence * 100)}% confidence
                  </span>
                </div>
                <p className="text-sm font-medium text-slate-900 dark:text-white">
                  {fact.key}
                </p>
                <p className="text-sm text-slate-600 dark:text-slate-300">
                  {fact.value}
                </p>
              </div>
            ))
          )}
        </div>
      )}

      {activeTab === 'episodic' && (
        <div className="space-y-2">
          {episodic.length === 0 ? (
            <p className="text-sm text-slate-500 text-center py-4">No episodic memory</p>
          ) : (
            episodic.map((episode, idx) => (
              <div
                key={episode.id || idx}
                className="p-3 rounded-lg bg-slate-50 dark:bg-slate-700/50"
              >
                <p className="text-sm text-slate-700 dark:text-slate-300 mb-2">
                  {episode.summary.slice(0, 100)}...
                </p>
                <div className="flex flex-wrap gap-1 mb-2">
                  {episode.key_topics.slice(0, 3).map((topic, i) => (
                    <Badge key={i} variant="secondary" className="text-xs">
                      {topic}
                    </Badge>
                  ))}
                </div>
                <div className="flex items-center gap-3 text-xs text-slate-400">
                  <span>{episode.message_count} messages</span>
                  <span>{episode.duration_minutes} min</span>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {stats && (
        <div className="border-t border-slate-200 dark:border-slate-700 pt-4 mt-4">
          <h4 className="text-xs font-medium text-slate-500 mb-2">Statistics</h4>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="p-2 rounded bg-slate-50 dark:bg-slate-700/50">
              <span className="text-slate-500">Episodes:</span>
              <span className="ml-1 font-medium">{stats.episodic?.total_episodes || 0}</span>
            </div>
            <div className="p-2 rounded bg-slate-50 dark:bg-slate-700/50">
              <span className="text-slate-500">Facts:</span>
              <span className="ml-1 font-medium">{stats.long_term_facts_count || 0}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}