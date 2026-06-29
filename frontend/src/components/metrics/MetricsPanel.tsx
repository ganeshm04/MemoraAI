'use client';

import { useState, useEffect } from 'react';
import { Activity, Clock, Cpu, RefreshCw, Layers, ShieldCheck, Flame, Lock, Unlock } from 'lucide-react';
import { api } from '@/lib/api';
import { Badge } from '@/components/ui/badge';
import toast from 'react-hot-toast';

interface MetricsData {
  retrieval: {
    search_counts: { vector: number; bm25: number; hybrid: number; total: number };
    avg_durations: { vector: number; bm25: number; hybrid: number; fusion: number; rerank: number };
    total_fusions: number;
    total_reranks: number;
  };
  generation: {
    total_generations: number;
    avg_duration_ms: number;
    total_tokens: number;
    avg_tokens_per_req: number;
  };
  embedding: {
    total_embeddings: number;
    avg_duration_ms: number;
  };
  memory: {
    reads: { short_term: number; long_term: number; episodic: number; total: number };
    writes: { short_term: number; long_term: number; episodic: number; total: number };
  };
}

export function MetricsPanel() {
  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  
  // Authentication states
  const [token, setToken] = useState<string>('');
  const [unauthorized, setUnauthorized] = useState(false);
  const [passcode, setPasscode] = useState('');

  // Fetch token from localStorage on mount
  useEffect(() => {
    const savedToken = localStorage.getItem('metrics_token') || '';
    setToken(savedToken);
    fetchMetrics(savedToken);
  }, []);

  const fetchMetrics = async (activeToken: string) => {
    try {
      setError(false);
      const data = await api.getDashboardMetrics(activeToken);
      setMetrics(data);
      setLastUpdated(new Date());
      setUnauthorized(false);
    } catch (err: any) {
      console.error('Error fetching metrics:', err);
      if (err.response?.status === 401) {
        setUnauthorized(true);
        localStorage.removeItem('metrics_token');
      } else {
        setError(true);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleUnlock = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!passcode.trim()) return;

    setLoading(true);
    try {
      const data = await api.getDashboardMetrics(passcode);
      setMetrics(data);
      setLastUpdated(new Date());
      setToken(passcode);
      localStorage.setItem('metrics_token', passcode);
      setUnauthorized(false);
      toast.success('Metrics dashboard unlocked');
    } catch (err: any) {
      console.error('Unlock failed:', err);
      toast.error('Invalid metrics token');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!autoRefresh || unauthorized) return;

    const interval = setInterval(() => {
      fetchMetrics(token);
    }, 4000);

    return () => clearInterval(interval);
  }, [autoRefresh, token, unauthorized]);

  const formatMs = (ms: number | undefined) => {
    if (ms === undefined || isNaN(ms)) return '0.0 ms';
    return `${ms.toFixed(1)} ms`;
  };

  if (loading && !metrics) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-3 text-zinc-500">
        <RefreshCw className="w-6 h-6 animate-spin text-cyan-400" />
        <span className="text-xs font-mono">Connecting to telemetry stream...</span>
      </div>
    );
  }

  // Render password prompt if unauthorized
  if (unauthorized) {
    return (
      <div className="flex flex-col items-center justify-center py-12 px-4 text-center select-none text-zinc-300">
        <div className="w-12 h-12 rounded-full bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center mb-4 text-cyan-400 shadow-lg shadow-cyan-500/5">
          <Lock className="w-5 h-5 animate-pulse" />
        </div>
        <h3 className="text-sm font-bold text-white mb-1 tracking-tight">Telemetry Stream Locked</h3>
        <p className="text-xs text-zinc-500 max-w-[260px] leading-relaxed mb-6">
          Access to system logs and latency pipelines requires an authorization key.
        </p>

        <form onSubmit={handleUnlock} className="w-full max-w-[280px] flex flex-col gap-3">
          <input
            type="password"
            placeholder="Enter Metrics Token..."
            value={passcode}
            onChange={(e) => setPasscode(e.target.value)}
            className="w-full px-3.5 py-2.5 rounded-xl text-xs font-mono bg-white/[0.02] border border-white/[0.06] text-white focus:outline-none focus:border-cyan-500/50 focus:bg-white/[0.04] transition-all placeholder-zinc-600 text-center"
            autoFocus
          />
          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-xl text-xs font-bold bg-gradient-to-r from-cyan-400 to-violet-600 text-white cursor-pointer hover:opacity-90 transition-all flex items-center justify-center gap-1.5 shadow-md shadow-cyan-500/10"
          >
            {loading ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <>
                <Unlock className="w-3.5 h-3.5" />
                Unlock Telemetry
              </>
            )}
          </button>
        </form>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-5 select-none text-zinc-300">
      {/* Header Info */}
      <div className="flex items-center justify-between border-b border-white/[0.04] pb-3">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-cyan-400 animate-pulse" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-400">Live Telemetry</h3>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[9px] font-mono text-zinc-500">
            Updated {lastUpdated.toLocaleTimeString()}
          </span>
          <button
            onClick={() => fetchMetrics(token)}
            className="p-1 rounded-md hover:bg-white/[0.04] border border-transparent hover:border-white/[0.06] transition-all cursor-pointer text-zinc-400 hover:text-white"
            title="Refresh metrics"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => {
              localStorage.removeItem('metrics_token');
              setToken('');
              setUnauthorized(true);
            }}
            className="p-1 rounded-md hover:bg-white/[0.04] border border-transparent hover:border-white/[0.06] transition-all cursor-pointer text-zinc-400 hover:text-white"
            title="Lock dashboard"
          >
            <Lock className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded-full border transition-all ${
              autoRefresh
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                : 'bg-zinc-800/40 text-zinc-500 border-zinc-700/30'
            }`}
          >
            {autoRefresh ? 'AUTO' : 'PAUSED'}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs font-mono leading-relaxed">
          Warning: Failed to fetch latest live metrics. Displaying last cached data.
        </div>
      )}

      {metrics && (
        <>
          {/* Section 1: RAG Pipeline Latency */}
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-cyan-400" />
              <h4 className="text-xs font-semibold text-zinc-300">RAG Latency Pipeline</h4>
            </div>

            <div className="rounded-xl border border-white/[0.04] bg-white/[0.01] p-3.5 flex flex-col gap-3 relative overflow-hidden">
              <div className="absolute top-0 right-0 w-24 h-24 bg-cyan-500/5 rounded-full blur-2xl pointer-events-none" />

              {/* Progress Flow */}
              {[
                { label: 'Vector Search', value: metrics.retrieval.avg_durations.vector, color: 'from-cyan-400 to-cyan-500' },
                { label: 'BM25 Search', value: metrics.retrieval.avg_durations.bm25, color: 'from-cyan-400 to-cyan-500' },
                { label: 'RRF Rank Fusion', value: metrics.retrieval.avg_durations.fusion, color: 'from-violet-400 to-violet-500' },
                { label: 'Cross-Encoder Rerank', value: metrics.retrieval.avg_durations.rerank, color: 'from-violet-500 to-fuchsia-500' },
              ].map((stage) => (
                <div key={stage.label} className="flex flex-col gap-1.5">
                  <div className="flex justify-between items-center text-[10px] font-mono">
                    <span className="text-zinc-400 font-semibold">{stage.label}</span>
                    <span className="text-white font-bold">{formatMs(stage.value)}</span>
                  </div>
                  <div className="h-1.5 w-full bg-white/[0.03] rounded-full overflow-hidden border border-white/[0.02]">
                    <div
                      className={`h-full bg-gradient-to-r ${stage.color} rounded-full`}
                      style={{ width: `${Math.min(100, (stage.value || 0) / 3)}%`, transition: 'width 0.8s ease-in-out' }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Section 2: Generation Engine */}
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5 text-violet-400" />
              <h4 className="text-xs font-semibold text-zinc-300">LLM Generation Engine</h4>
            </div>

            <div className="rounded-xl border border-white/[0.04] bg-white/[0.01] p-3.5 grid grid-cols-2 gap-3 relative overflow-hidden">
              <div className="absolute bottom-0 right-0 w-24 h-24 bg-violet-500/5 rounded-full blur-2xl pointer-events-none" />

              <div className="flex flex-col gap-1 p-2 bg-white/[0.01] rounded-lg border border-white/[0.03]">
                <span className="text-[9px] font-mono font-semibold uppercase tracking-wider text-zinc-500">Avg Generation</span>
                <span className="text-sm font-bold text-white font-mono">
                  {formatMs(metrics.generation.avg_duration_ms)}
                </span>
              </div>

              <div className="flex flex-col gap-1 p-2 bg-white/[0.01] rounded-lg border border-white/[0.03]">
                <span className="text-[9px] font-mono font-semibold uppercase tracking-wider text-zinc-500">Generations</span>
                <span className="text-sm font-bold text-white font-mono">
                  {metrics.generation.total_generations} requests
                </span>
              </div>

              <div className="flex flex-col gap-1 p-2 bg-white/[0.01] rounded-lg border border-white/[0.03]">
                <span className="text-[9px] font-mono font-semibold uppercase tracking-wider text-zinc-500">Total Tokens</span>
                <span className="text-xs font-bold text-white font-mono flex items-center gap-1">
                  <Flame className="w-3 h-3 text-amber-500 fill-amber-500/25" />
                  {metrics.generation.total_tokens?.toLocaleString() || 0}
                </span>
              </div>

              <div className="flex flex-col gap-1 p-2 bg-white/[0.01] rounded-lg border border-white/[0.03]">
                <span className="text-[9px] font-mono font-semibold uppercase tracking-wider text-zinc-500">Avg Tokens/Req</span>
                <span className="text-sm font-bold text-white font-mono">
                  {Math.round(metrics.generation.avg_tokens_per_req || 0)}
                </span>
              </div>
            </div>
          </div>

          {/* Section 3: Layered Memory Engine */}
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-fuchsia-400" />
              <h4 className="text-xs font-semibold text-zinc-300">Memory Engine Reads/Writes</h4>
            </div>

            <div className="rounded-xl border border-white/[0.04] bg-white/[0.01] p-3.5 flex flex-col gap-3.5 relative overflow-hidden">
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-28 h-28 bg-fuchsia-500/5 rounded-full blur-2xl pointer-events-none" />

              {[
                {
                  label: 'Short-Term Memory',
                  read: metrics.memory.reads.short_term,
                  write: metrics.memory.writes.short_term,
                  color: 'from-cyan-400 to-cyan-500',
                  desc: 'Context Windows',
                },
                {
                  label: 'Long-Term Memory',
                  read: metrics.memory.reads.long_term,
                  write: metrics.memory.writes.long_term,
                  color: 'from-violet-500 to-violet-600',
                  desc: 'Fact Extractions',
                },
                {
                  label: 'Episodic Memory',
                  read: metrics.memory.reads.episodic,
                  write: metrics.memory.writes.episodic,
                  color: 'from-fuchsia-500 to-fuchsia-600',
                  desc: 'Session Summaries',
                },
              ].map((mem) => {
                const total = mem.read + mem.write;
                const max = Math.max(1, total);
                const readPercent = (mem.read / max) * 100;
                const writePercent = (mem.write / max) * 100;

                return (
                  <div key={mem.label} className="flex flex-col gap-2">
                    <div className="flex justify-between items-center text-[10px] font-mono">
                      <div className="flex flex-col">
                        <span className="text-white font-semibold">{mem.label}</span>
                        <span className="text-[8px] text-zinc-500">{mem.desc}</span>
                      </div>
                      <div className="flex items-center gap-2 font-bold">
                        <span className="text-cyan-400">R: {mem.read}</span>
                        <span className="text-zinc-600">/</span>
                        <span className="text-fuchsia-400">W: {mem.write}</span>
                      </div>
                    </div>

                    <div className="h-2 w-full bg-white/[0.03] rounded-full overflow-hidden border border-white/[0.02] flex">
                      {total > 0 ? (
                        <>
                          <div
                            className="h-full bg-gradient-to-r from-cyan-400 to-cyan-500"
                            style={{ width: `${readPercent}%` }}
                          />
                          <div
                            className="h-full bg-gradient-to-r from-fuchsia-500 to-fuchsia-600 border-l border-black/40"
                            style={{ width: `${writePercent}%` }}
                          />
                        </>
                      ) : (
                        <div className="h-full w-full bg-white/[0.01]" />
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
