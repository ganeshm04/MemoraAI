'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Loader2, Trash2, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { MessageBubble } from './MessageBubble';
import { ChatInput } from './ChatInput';
import { useChatStore } from '@/hooks/useChat';
import { api } from '@/lib/api';
import toast from 'react-hot-toast';

export function ChatPanel() {
  const [input, setInput] = useState('');
  const {
    messages,
    isLoading,
    sessionId,
    addMessage,
    setLoading,
    setError,
    setChunks,
    setSources,
    clearChat,
  } = useChatStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!input.trim() || isLoading) return;

    const query = input.trim();
    setInput('');

    addMessage({
      role: 'user',
      content: query,
    });

    setLoading(true);
    setError(null);

    try {
      const response = await api.query({
        query,
        session_id: sessionId,
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

      setChunks(response.chunks || []);
      setSources(response.sources || []);

    } catch (error: any) {
      const errorMessage = error?.response?.data?.message || 'Failed to get response. Please try again.';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleClearChat = () => {
    clearChat();
    toast.success('Chat cleared');
  };

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl shadow-lg overflow-hidden">
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-700">
        <div>
          <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
            Chat
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Session: {sessionId.slice(0, 8)}...
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClearChat}
            disabled={messages.length === 0}
          >
            <Trash2 className="w-4 h-4 mr-1" />
            Clear
          </Button>
        </div>
      </div>

      <div className="h-[500px] overflow-y-auto p-6 space-y-4">
        <AnimatePresence>
          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              <MessageBubble message={message} />
            </motion.div>
          ))}
        </AnimatePresence>

        {isLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex items-center gap-2 text-slate-500 dark:text-slate-400"
          >
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Thinking...</span>
          </motion.div>
        )}
      </div>

      <div className="p-4 border-t border-slate-200 dark:border-slate-700">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <ChatInput
            value={input}
            onChange={setInput}
            disabled={isLoading}
            placeholder="Ask me anything about your documents..."
          />
          <Button type="submit" disabled={isLoading || !input.trim()}>
            <Send className="w-4 h-4" />
          </Button>
        </form>
      </div>
    </div>
  );
}