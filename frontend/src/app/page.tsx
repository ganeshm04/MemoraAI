'use client';

import { useState } from 'react';
import { ChatPanel } from '@/components/chat/ChatPanel';
import { RetrievalPanel } from '@/components/retrieval/RetrievalPanel';
import { MemoryPanel } from '@/components/memory/MemoryPanel';
import { SourceAttribution } from '@/components/sources/SourceAttribution';

export default function HomePage() {
  const [activeTab, setActiveTab] = useState<'chat' | 'retrieval' | 'memory'>('chat');
  const [selectedChunks, setSelectedChunks] = useState<any[]>([]);
  const [memoryData, setMemoryData] = useState<any>(null);
  const [sources, setSources] = useState<string[]>([]);

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <div className="container mx-auto px-4 py-8">
        <header className="mb-8 text-center">
          <h1 className="text-4xl font-bold text-slate-900 dark:text-white mb-2">
            MemoraAI
          </h1>
          <p className="text-slate-600 dark:text-slate-300">
            Adaptive RAG System with Hybrid Retrieval & Memory
          </p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <ChatPanel
              onChunksRetrieved={setSelectedChunks}
              onSourcesFound={setSources}
              onMemoryUpdate={setMemoryData}
            />
          </div>

          <div className="space-y-6">
            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-lg overflow-hidden">
              <div className="flex border-b border-slate-200 dark:border-slate-700">
                <button
                  onClick={() => setActiveTab('chat')}
                  className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
                    activeTab === 'chat'
                      ? 'bg-primary text-white'
                      : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700'
                  }`}
                >
                  Chat
                </button>
                <button
                  onClick={() => setActiveTab('retrieval')}
                  className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
                    activeTab === 'retrieval'
                      ? 'bg-primary text-white'
                      : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700'
                  }`}
                >
                  Retrieval
                </button>
                <button
                  onClick={() => setActiveTab('memory')}
                  className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
                    activeTab === 'memory'
                      ? 'bg-primary text-white'
                      : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700'
                  }`}
                >
                  Memory
                </button>
              </div>

              <div className="p-4">
                {activeTab === 'retrieval' && (
                  <RetrievalPanel chunks={selectedChunks} />
                )}
                {activeTab === 'memory' && (
                  <MemoryPanel memory={memoryData} />
                )}
                {activeTab === 'chat' && (
                  <div className="text-center text-slate-500 dark:text-slate-400 py-8">
                    <p>Select a tab to view details</p>
                  </div>
                )}
              </div>
            </div>

            <SourceAttribution sources={sources} />
          </div>
        </div>
      </div>
    </main>
  );
}