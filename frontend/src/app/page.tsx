'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Brain, Cpu, Database, Search, Zap, ChevronRight, Activity } from 'lucide-react';
import { ChatPanel } from '@/components/chat/ChatPanel';
import { RetrievalPanel } from '@/components/retrieval/RetrievalPanel';
import { MemoryPanel } from '@/components/memory/MemoryPanel';
import { SourceAttribution } from '@/components/sources/SourceAttribution';
import { api } from '@/lib/api';

export default function HomePage() {
  const [selectedChunks, setSelectedChunks] = useState<any[]>([]);
  const [memoryData, setMemoryData] = useState<any>(null);
  const [sources, setSources] = useState<string[]>([]);
  const [sidebarTab, setSidebarTab] = useState<'retrieval' | 'memory' | 'sources'>('retrieval');
  const [isHealthy, setIsHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    api.healthCheck()
      .then(() => setIsHealthy(true))
      .catch(() => setIsHealthy(false));
  }, []);

  const sidebarTabs = [
    { id: 'retrieval' as const, label: 'Retrieval', icon: Search, count: selectedChunks.length },
    { id: 'memory' as const, label: 'Memory', icon: Brain, count: 0 },
    { id: 'sources' as const, label: 'Sources', icon: Database, count: sources.length },
  ];

  return (
    <main className="min-h-screen bg-background relative overflow-hidden font-sans">
      {/* Ambient Aurora Glows */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] aurora-blur-1 rounded-full blur-[140px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[60%] h-[60%] aurora-blur-2 rounded-full blur-[140px]" />
        <div className="absolute top-[30%] left-[50%] -translate-x-1/2 w-[70%] h-[50%] aurora-blur-3 rounded-full blur-[160px]" />
      </div>

      <div className="relative z-10 flex flex-col h-screen">
        {/* Header */}
        <header className="px-6 py-3.5 flex items-center justify-between border-b border-white/[0.04] bg-background/40 backdrop-blur-md sticky top-0 z-50">
          <div className="flex items-center gap-3 select-none">
            <div className="relative">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-400 via-violet-500 to-fuchsia-500 flex items-center justify-center shadow-lg shadow-cyan-500/10">
                <Brain className="w-4.5 h-4.5 text-white" />
              </div>
              <div className={`absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2 border-background ${isHealthy === true ? 'bg-emerald-500 shadow-sm shadow-emerald-500/30' : isHealthy === false ? 'bg-rose-500 shadow-sm shadow-rose-500/30' : 'bg-amber-500 animate-pulse'}`} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-sm font-bold tracking-tight bg-gradient-to-r from-white via-zinc-200 to-zinc-400 bg-clip-text text-transparent">MemoraAI</h1>
                <span className="text-[10px] font-mono font-medium px-1.5 py-0.5 rounded-md bg-white/[0.04] border border-white/[0.06] text-zinc-400">v1.0.0</span>
              </div>
              <p className="text-[10px] text-zinc-500 font-medium">Adaptive Hybrid Retrieval & Layered Memory Engine</p>
            </div>
          </div>

          {/* System Status Strip */}
          <div className="hidden md:flex items-center gap-2">
            {[
              { icon: Cpu, label: 'AI Service', status: isHealthy },
              { icon: Database, label: 'Vector DB', status: isHealthy },
              { icon: Zap, label: 'Reranker', status: isHealthy },
            ].map(({ icon: Icon, label, status }) => (
              <div key={label} className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-white/[0.02] border border-white/[0.04] hover:border-white/[0.08] transition-colors text-[10px] font-medium font-mono text-zinc-400 select-none">
                <Icon className="w-3 h-3 text-zinc-500" />
                <span>{label}</span>
                <span className={`w-1.5 h-1.5 rounded-full ${status === true ? 'bg-emerald-500 shadow-sm shadow-emerald-500/30' : status === false ? 'bg-rose-500 shadow-sm shadow-rose-500/30' : 'bg-amber-500 animate-pulse'}`} />
              </div>
            ))}
          </div>
        </header>

        {/* Main Content */}
        <div className="flex-1 flex overflow-hidden">
          {/* Chat Panel - Main Area */}
          <div className="flex-1 min-w-0">
            <ChatPanel
              onChunksRetrieved={(chunks) => {
                setSelectedChunks(chunks);
                if (chunks.length > 0) setSidebarTab('retrieval');
              }}
              onSourcesFound={(s) => {
                setSources(s);
              }}
              onMemoryUpdate={setMemoryData}
            />
          </div>

          {/* Sidebar - Panels */}
          <div className="hidden lg:flex w-[380px] xl:w-[420px] flex-col border-l border-white/[0.04] bg-zinc-950/20 backdrop-blur-md">
            {/* Sidebar Tabs */}
            <div className="flex border-b border-white/[0.04] p-1.5 gap-1 bg-white/[0.01]">
              {sidebarTabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setSidebarTab(tab.id)}
                  className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-semibold tracking-wide transition-all relative ${
                    sidebarTab === tab.id
                      ? 'text-foreground bg-white/[0.04] border border-white/[0.04] shadow-sm'
                      : 'text-zinc-500 hover:text-zinc-300 hover:bg-white/[0.01]'
                  }`}
                >
                  <tab.icon className="w-3.5 h-3.5" />
                  <span>{tab.label}</span>
                  {tab.count > 0 && (
                    <span className="px-1.5 py-0.5 rounded-full bg-primary/10 text-primary text-[9px] font-mono font-bold">
                      {tab.count}
                    </span>
                  )}
                </button>
              ))}
            </div>

            {/* Sidebar Content */}
            <div className="flex-1 overflow-y-auto p-4 scrollbar-thin">
              <AnimatePresence mode="wait">
                {sidebarTab === 'retrieval' && (
                  <motion.div
                    key="retrieval"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.15 }}
                  >
                    <RetrievalPanel chunks={selectedChunks} />
                  </motion.div>
                )}
                {sidebarTab === 'memory' && (
                  <motion.div
                    key="memory"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.15 }}
                  >
                    <MemoryPanel memory={memoryData} />
                  </motion.div>
                )}
                {sidebarTab === 'sources' && (
                  <motion.div
                    key="sources"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.15 }}
                  >
                    <SourceAttribution sources={sources} />
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}