'use client';

import { MetricsPanel } from '@/components/metrics/MetricsPanel';
import { Brain, ArrowLeft } from 'lucide-react';
import Link from 'next/link';

export default function MetricsPage() {
  return (
    <main className="min-h-screen bg-background relative overflow-hidden font-sans flex flex-col justify-center items-center p-4 md:p-8">
      {/* Ambient Aurora Glows */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] aurora-blur-1 rounded-full blur-[140px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[60%] h-[60%] aurora-blur-2 rounded-full blur-[140px]" />
        <div className="absolute top-[30%] left-[50%] -translate-x-1/2 w-[70%] h-[50%] aurora-blur-3 rounded-full blur-[160px]" />
      </div>

      <div className="relative z-10 w-full max-w-[550px] flex flex-col gap-6">
        {/* Navigation & Brand */}
        <div className="flex items-center justify-between px-2">
          <Link
            href="/"
            className="flex items-center gap-1.5 text-xs font-semibold text-zinc-400 hover:text-white transition-colors group cursor-pointer"
          >
            <ArrowLeft className="w-3.5 h-3.5 group-hover:-translate-x-0.5 transition-transform" />
            Back to Chat
          </Link>
          
          <div className="flex items-center gap-2 select-none">
            <div className="w-6 h-6 rounded-lg bg-gradient-to-tr from-cyan-400 via-violet-500 to-fuchsia-500 flex items-center justify-center">
              <Brain className="w-3 h-3 text-white" />
            </div>
            <span className="text-xs font-bold text-white tracking-tight">MemoraAI</span>
          </div>
        </div>

        {/* Dashboard Box */}
        <div className="rounded-2xl border border-white/[0.04] bg-zinc-950/40 backdrop-blur-xl p-6 shadow-2xl shadow-black/45 relative overflow-hidden">
          <MetricsPanel />
        </div>
      </div>
    </main>
  );
}
