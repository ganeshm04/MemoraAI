'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Loader2, Trash2, Upload, FileText, Link, Type, Sparkles, X, RotateCcw, Brain } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { MessageBubble } from './MessageBubble';
import { ChatInput } from './ChatInput';
import { useChatStore } from '@/hooks/useChat';
import { api } from '@/lib/api';
import toast from 'react-hot-toast';
import { cn } from '@/lib/utils';

interface ChatPanelProps {
  onChunksRetrieved?: (chunks: any[]) => void;
  onSourcesFound?: (sources: string[]) => void;
  onMemoryUpdate?: (memory: any) => void;
}

export function ChatPanel({ onChunksRetrieved, onSourcesFound, onMemoryUpdate }: ChatPanelProps = {}) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setMounted(true);
  }, []);

  const [input, setInput] = useState('');
  const [showUploadMenu, setShowUploadMenu] = useState(false);
  const [uploadUrl, setUploadUrl] = useState('');
  const [uploadText, setUploadText] = useState('');
  const [showUrlInput, setShowUrlInput] = useState(false);
  const [showTextInput, setShowTextInput] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [queryType, setQueryType] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const {
    messages,
    isLoading,
    sessionId,
    addMessage,
    setLoading,
    setError,
    setChunks,
    sources,
    setSources,
    clearChat,
    resetSession,
  } = useChatStore();

  const scrollToBottom = useCallback(() => {
    setTimeout(() => chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 100);
  }, []);

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();

    if (!input.trim() || isLoading) return;

    const query = input.trim();
    setInput('');

    addMessage({
      role: 'user',
      content: query,
    });
    scrollToBottom();

    setLoading(true);
    setError(null);
    setQueryType(null);

    try {
      const response = await api.query({
        query,
        session_id: sessionId,
        user_id: 'default-user',
        use_memory: true,
        use_reranking: true,
        temperature: 0.7,
        max_tokens: 2048,
      });

      addMessage({
        role: 'assistant',
        content: response.response,
        tokens_used: response.tokens_used,
        chunks: response.chunks,
      });

      setQueryType(response.query_type || null);
      if (response.chunks && response.chunks.length > 0) {
        setChunks(response.chunks);
        onChunksRetrieved?.(response.chunks);
      }
      const activeSources = response.sources || [];
      const newSources = Array.from(new Set([...sources, ...activeSources]));
      setSources(newSources);
      onSourcesFound?.(newSources);
      scrollToBottom();

    } catch (error: any) {
      const errorMessage = error?.response?.data?.message || error?.response?.data?.detail || 'Failed to get response. Please try again.';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const saveSessionEpisode = async () => {
    if (messages.length > 0) {
      try {
        toast.loading('Saving session memory...', { id: 'save-session' });
        await api.summarizeSession({
          user_id: 'default-user',
          session_id: sessionId,
        });
        toast.success('Session memory saved', { id: 'save-session' });
      } catch (error) {
        console.error('Failed to summarize session:', error);
        toast.dismiss('save-session');
      }
    }
  };

  const handleClearChat = async () => {
    await saveSessionEpisode();
    try {
      await api.clearShortTermMemory(sessionId);
    } catch (e) {
      console.error('Failed to clear short-term memory:', e);
    }
    clearChat();
    onChunksRetrieved?.([]);
    onSourcesFound?.([]);
    setQueryType(null);
    toast.success('Chat cleared');
  };

  const handleNewSession = async () => {
    await saveSessionEpisode();
    resetSession();
    onChunksRetrieved?.([]);
    onSourcesFound?.([]);
    setQueryType(null);
    toast.success('New session started');
  };

  const handleFileUpload = async (file: File) => {
    if (file.type !== 'application/pdf') {
      toast.error('Only PDF files are supported');
      return;
    }

    if (file.size > 50 * 1024 * 1024) {
      toast.error('File size exceeds 50MB limit');
      return;
    }

    setIsUploading(true);
    setShowUploadMenu(false);

    try {
      const response = await api.uploadFile(file);
      if (!response.success) {
        toast.error(response.errors?.[0] || 'Failed to ingest document');
      } else {
        toast.success(`Document ingested: ${response.chunks_created} chunks created`);
        const newSources = Array.from(new Set([...sources, response.source || file.name]));
        setSources(newSources);
        onSourcesFound?.(newSources);
      }
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || error?.response?.data?.message || 'Failed to upload file');
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFileUpload(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFileUpload(file);
  };

  const handleUrlUpload = async () => {
    if (!uploadUrl.trim()) return;

    setIsUploading(true);
    setShowUrlInput(false);

    try {
      const response = await api.ingestURL({ url: uploadUrl.trim() });
      if (!response.success) {
        toast.error(response.errors?.[0] || 'Failed to ingest URL');
      } else {
        toast.success(`URL ingested: ${response.chunks_created} chunks created`);
        const newSources = Array.from(new Set([...sources, response.source || uploadUrl.trim()]));
        setSources(newSources);
        onSourcesFound?.(newSources);
        setUploadUrl('');
      }
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || error?.response?.data?.message || 'Failed to ingest URL');
    } finally {
      setIsUploading(false);
    }
  };

  const handleTextUpload = async () => {
    if (!uploadText.trim()) return;

    setIsUploading(true);
    setShowTextInput(false);

    try {
      const response = await api.ingestText({
        text: uploadText,
        source: 'manual_input',
      });
      if (!response.success) {
        toast.error(response.errors?.[0] || 'Failed to ingest text');
      } else {
        toast.success(`Text ingested: ${response.chunks_created} chunks created`);
        const newSources = Array.from(new Set([...sources, response.source || 'manual_input']));
        setSources(newSources);
        onSourcesFound?.(newSources);
        setUploadText('');
      }
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || error?.response?.data?.message || 'Failed to ingest text');
    } finally {
      setIsUploading(false);
    }
  };

  const queryTypeColors: Record<string, string> = {
    factual: 'bg-blue-500/20 text-blue-400',
    conversational: 'bg-emerald-500/20 text-emerald-400',
    analytical: 'bg-amber-500/20 text-amber-400',
    memory_related: 'bg-purple-500/20 text-purple-400',
  };

  return (
    <div
      className="flex flex-col h-full relative z-10"
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,application/pdf"
        onChange={handleFileChange}
        className="hidden"
      />

      {/* Drag overlay */}
      <AnimatePresence>
        {isDragging && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-4 z-50 flex items-center justify-center bg-zinc-950/80 backdrop-blur-md border border-white/[0.08] rounded-2xl shadow-2xl"
          >
            <div className="text-center">
              <Upload className="w-10 h-10 text-cyan-400 mx-auto mb-3 animate-bounce" />
              <p className="text-sm font-bold text-zinc-100">Drop PDF document here</p>
              <p className="text-[10px] text-zinc-500 mt-1">Accepts file size up to 50MB</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Chat Header */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-white/[0.04] bg-white/[0.01] select-none">
        <div className="flex items-center gap-3">
          <div>
            <h2 className="text-xs font-bold tracking-wider uppercase text-zinc-400 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
              Session Sandbox
            </h2>
            <p className="text-[9px] text-zinc-500 font-mono mt-0.5">
              ID: {mounted ? sessionId.slice(0, 8).toUpperCase() : '---'}
            </p>
          </div>
          {queryType && (
            <span className={`px-2 py-0.5 rounded-full text-[9px] font-semibold font-mono tracking-wider uppercase ${queryTypeColors[queryType] || 'bg-white/[0.04] text-zinc-400'}`}>
              {queryType.replace('_', ' ')}
            </span>
          )}
        </div>
        <div className="flex gap-1.5">
          <div className="relative">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowUploadMenu(!showUploadMenu)}
              disabled={isUploading}
              className="h-8 text-[10px] font-semibold tracking-wide border-white/[0.06] bg-white/[0.01] hover:bg-white/[0.04] text-zinc-300 cursor-pointer"
            >
              <Upload className="w-3 h-3 mr-1 text-zinc-400" />
              {isUploading ? 'Ingesting...' : 'Ingest Data'}
            </Button>
            <AnimatePresence>
              {showUploadMenu && (
                <motion.div
                  initial={{ opacity: 0, y: -4, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -4, scale: 0.95 }}
                  transition={{ duration: 0.12 }}
                  className="absolute right-0 top-full mt-1.5 w-48 glass-strong rounded-xl shadow-xl z-50 border border-white/[0.08]"
                >
                  <div className="p-1 space-y-0.5">
                    <button
                      onClick={() => { fileInputRef.current?.click(); setShowUploadMenu(false); }}
                      className="w-full flex items-center gap-2 px-3 py-2 text-xs font-medium text-zinc-300 hover:text-white hover:bg-white/[0.04] rounded-lg transition-all cursor-pointer"
                    >
                      <FileText className="w-3.5 h-3.5 text-cyan-400" />
                      Upload PDF
                    </button>
                    <button
                      onClick={() => { setShowUrlInput(true); setShowUploadMenu(false); }}
                      className="w-full flex items-center gap-2 px-3 py-2 text-xs font-medium text-zinc-300 hover:text-white hover:bg-white/[0.04] rounded-lg transition-all cursor-pointer"
                    >
                      <Link className="w-3.5 h-3.5 text-cyan-400" />
                      Scrape URL
                    </button>
                    <button
                      onClick={() => { setShowTextInput(true); setShowUploadMenu(false); }}
                      className="w-full flex items-center gap-2 px-3 py-2 text-xs font-medium text-zinc-300 hover:text-white hover:bg-white/[0.04] rounded-lg transition-all cursor-pointer"
                    >
                      <Type className="w-3.5 h-3.5 text-violet-400" />
                      Add Text
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleNewSession}
            className="h-8 text-[10px] font-semibold tracking-wide border-white/[0.06] bg-white/[0.01] hover:bg-white/[0.04] text-zinc-300 cursor-pointer"
          >
            <RotateCcw className="w-3 h-3 mr-1 text-zinc-400" />
            Reset
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleClearChat}
            disabled={messages.length === 0}
            className="h-8 border-white/[0.06] bg-white/[0.01] hover:bg-white/[0.04] text-zinc-300 disabled:opacity-30 cursor-pointer"
          >
            <Trash2 className="w-3.5 h-3.5 text-zinc-400" />
          </Button>
        </div>
      </div>

      {/* URL Input Bar */}
      <AnimatePresence>
        {showUrlInput && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden border-b border-white/[0.04] bg-white/[0.01]"
          >
            <div className="px-6 py-4 flex gap-2">
              <Input
                value={uploadUrl}
                onChange={(e) => setUploadUrl(e.target.value)}
                placeholder="Paste the URL link to parse..."
                onKeyDown={(e) => e.key === 'Enter' && handleUrlUpload()}
                className="flex-1 h-9 text-xs glass-input text-zinc-100"
                autoFocus
              />
              <Button size="sm" onClick={handleUrlUpload} disabled={!uploadUrl.trim() || isUploading} className="h-9 text-xs font-semibold bg-primary hover:opacity-90 cursor-pointer">
                <Link className="w-3.5 h-3.5 mr-1" />
                Ingest
              </Button>
              <Button size="sm" variant="ghost" onClick={() => setShowUrlInput(false)} className="h-9 border border-white/[0.04] text-zinc-400 cursor-pointer">
                <X className="w-3.5 h-3.5" />
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Text Input Bar */}
      <AnimatePresence>
        {showTextInput && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden border-b border-white/[0.04] bg-white/[0.01]"
          >
            <div className="px-6 py-4 flex flex-col gap-2.5">
              <textarea
                value={uploadText}
                onChange={(e) => setUploadText(e.target.value)}
                placeholder="Paste your custom text body..."
                rows={4}
                className="w-full rounded-xl border border-white/[0.06] bg-black/15 px-3.5 py-2.5 text-xs text-zinc-100 placeholder:text-zinc-600 resize-none focus:outline-none focus:ring-1 focus:ring-primary/40 focus:border-primary/40 transition-all font-sans"
                autoFocus
              />
              <div className="flex gap-2 justify-end">
                <Button size="sm" onClick={handleTextUpload} disabled={!uploadText.trim() || isUploading} className="text-xs font-semibold bg-primary cursor-pointer">
                  <Type className="w-3.5 h-3.5 mr-1" />
                  Add Text
                </Button>
                <Button size="sm" variant="ghost" onClick={() => setShowTextInput(false)} className="text-zinc-400 border border-white/[0.04] cursor-pointer">
                  <X className="w-3.5 h-3.5" />
                </Button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-5 scrollbar-thin">
        <AnimatePresence>
          {messages.map((message, idx) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ delay: idx === messages.length - 1 ? 0.05 : 0, duration: 0.2 }}
            >
              <MessageBubble
                message={message}
                onSelectChunks={(chunks) => {
                  setChunks(chunks);
                  onChunksRetrieved?.(chunks);
                }}
              />
            </motion.div>
          ))}
        </AnimatePresence>

        {isLoading && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-3 py-2"
          >
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-400 to-violet-600 flex items-center justify-center shrink-0 shadow-lg shadow-cyan-500/10">
              <Sparkles className="w-4 h-4 text-white animate-spin" />
            </div>
            <div className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-white/[0.015] border border-white/[0.04]">
              <div className="w-1.5 h-1.5 rounded-full bg-primary/80 typing-dot" />
              <div className="w-1.5 h-1.5 rounded-full bg-primary/80 typing-dot" />
              <div className="w-1.5 h-1.5 rounded-full bg-primary/80 typing-dot" />
            </div>
          </motion.div>
        )}

        {messages.length === 0 && !isLoading && (
          <div className="flex flex-col items-center justify-center h-full max-w-2xl mx-auto px-4 py-12 select-none">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.3, ease: 'easeOut' }}
              className="text-center mb-10"
            >
              <div className="w-14 h-14 mx-auto rounded-2xl bg-gradient-to-tr from-cyan-400 via-violet-500 to-fuchsia-500 flex items-center justify-center mb-5 shadow-xl shadow-cyan-500/10">
                <Brain className="w-7 h-7 text-white" />
              </div>
              <h2 className="text-xl font-bold tracking-tight text-white mb-2.5">
                MemoraAI Sandbox
              </h2>
              <p className="text-xs text-zinc-400 max-w-md mx-auto leading-relaxed">
                Connect external files, raw web pages, or manual notes to feed the hybrid RAG retrieval pipeline (Vector + BM25 + RRF + Cross-Encoder).
              </p>
            </motion.div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 w-full">
              {[
                { 
                  icon: FileText, 
                  label: 'Upload Document', 
                  desc: 'Ingest local PDF books or papers up to 50MB.', 
                  color: 'text-cyan-400 bg-cyan-500/[0.02] border-cyan-500/10 hover:border-cyan-500/30', 
                  action: () => fileInputRef.current?.click() 
                },
                { 
                  icon: Link, 
                  label: 'Scrape URL', 
                  desc: 'Parse and index any HTML web page or link.', 
                  color: 'text-cyan-400 bg-cyan-500/[0.02] border-cyan-500/10 hover:border-cyan-500/30', 
                  action: () => setShowUrlInput(true) 
                },
                { 
                  icon: Type, 
                  label: 'Add Raw Text', 
                  desc: 'Paste text segments directly into vector space.', 
                  color: 'text-violet-400 bg-violet-500/[0.02] border-violet-500/10 hover:border-violet-500/30', 
                  action: () => setShowTextInput(true) 
                },
              ].map(({ icon: Icon, label, desc, color, action }, idx) => (
                <motion.button
                  key={label}
                  onClick={action}
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 + idx * 0.05, duration: 0.25 }}
                  className={cn(
                    "flex flex-col items-start text-left p-5 rounded-2xl border transition-all cursor-pointer",
                    "glass-card hover:-translate-y-0.5",
                    color
                  )}
                >
                  <div className="p-2 rounded-xl bg-white/[0.02] border border-white/[0.04] mb-4">
                    <Icon className="w-5 h-5" />
                  </div>
                  <span className="text-xs font-bold text-zinc-100 mb-1">{label}</span>
                  <span className="text-[10px] text-zinc-500 leading-normal font-medium">{desc}</span>
                </motion.button>
              ))}
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-white/[0.04] bg-white/[0.01]">
        <form onSubmit={handleSubmit} className="flex gap-2.5 max-w-4xl mx-auto">
          <ChatInput
            value={input}
            onChange={setInput}
            onSubmit={() => handleSubmit()}
            disabled={isLoading}
            placeholder="Ask me anything about your documents..."
          />
          <Button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="h-11 w-11 shrink-0 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-600 hover:opacity-90 transition-all shadow-md shadow-cyan-500/20 active:scale-95 cursor-pointer"
          >
            <Send className="w-4 h-4" />
          </Button>
        </form>
      </div>
    </div>
  );
}
