'use client';

import { useState } from 'react';
import { User, Sparkles, Copy, Check, FileText } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { cn, formatTimestamp } from '@/lib/utils';
import type { Message } from '@/types';
import toast from 'react-hot-toast';

interface MessageBubbleProps {
  message: Message;
  onSelectChunks?: (chunks: any[]) => void;
}

export function MessageBubble({ message, onSelectChunks }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const [copied, setCopied] = useState(false);
  const chunks = message.chunks;

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    toast.success('Response copied to clipboard');
    setTimeout(() => setCopied(false), 2000);
  };

  // Simple markdown-like rendering
  const renderContent = (text: string) => {
    // Split by code blocks first
    const parts = text.split(/(```[\s\S]*?```)/);
    return parts.map((part, i) => {
      if (part.startsWith('```') && part.endsWith('```')) {
        const code = part.slice(3, -3);
        const firstLine = code.indexOf('\n');
        const lang = firstLine > 0 ? code.slice(0, firstLine).trim() : 'code';
        const codeContent = firstLine > 0 ? code.slice(firstLine + 1) : code;
        return (
          <div key={i} className="my-3 border border-white/[0.06] rounded-xl overflow-hidden bg-black/35 shadow-lg select-text">
            {/* Terminal Header */}
            <div className="flex items-center justify-between px-4 py-2 bg-white/[0.02] border-b border-white/[0.04] select-none">
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-rose-500/80" />
                <span className="w-2 h-2 rounded-full bg-amber-500/80" />
                <span className="w-2 h-2 rounded-full bg-emerald-500/80" />
                <span className="text-[10px] font-mono font-semibold text-zinc-500 ml-2 uppercase tracking-wider">{lang}</span>
              </div>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(codeContent);
                  toast.success('Code snippet copied');
                }}
                className="flex items-center gap-1 text-[10px] font-semibold text-zinc-500 hover:text-zinc-300 transition-colors cursor-pointer"
              >
                <Copy className="w-3 h-3" />
                Copy
              </button>
            </div>
            <pre className="p-4 overflow-x-auto text-[11px] font-mono text-zinc-300 leading-relaxed scrollbar-thin">
              <code>{codeContent}</code>
            </pre>
          </div>
        );
      }
      // Handle inline formatting
      return (
        <span key={i} className="whitespace-pre-wrap select-text">
          {part.split('\n').map((line, j) => (
            <span key={j}>
              {j > 0 && <br />}
              {renderInline(line)}
            </span>
          ))}
        </span>
      );
    });
  };

  const renderInline = (text: string) => {
    // Bold
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold text-white">$1</strong>');
    // Inline code
    text = text.replace(/`(.*?)`/g, '<code class="bg-white/[0.06] px-1.5 py-0.5 rounded text-[11px] font-mono text-cyan-300 border border-white/[0.04]">$1</code>');
    return <span dangerouslySetInnerHTML={{ __html: text }} />;
  };

  return (
    <div className={cn('flex gap-3 group', isUser && 'flex-row-reverse')}>
      {/* Avatar */}
      <div className={cn(
        'w-8 h-8 rounded-lg flex items-center justify-center shrink-0 border select-none',
        isUser
          ? 'bg-white/[0.02] border-white/[0.06] text-zinc-400'
          : 'bg-gradient-to-tr from-cyan-400 to-violet-600 border-cyan-400/20 text-white shadow-md shadow-cyan-500/10'
      )}>
        {isUser ? (
          <User className="w-3.5 h-3.5" />
        ) : (
          <Sparkles className="w-3.5 h-3.5" />
        )}
      </div>

      {/* Content */}
      <div className={cn('flex flex-col gap-1.5 max-w-[82%]', isUser && 'items-end')}>
        <div
          className={cn(
            'rounded-2xl px-4 py-3 text-sm relative leading-relaxed',
            isUser && 'bg-cyan-500/10 border border-cyan-500/20 text-zinc-100 shadow-sm shadow-cyan-500/5',
            !isUser && 'bg-white/[0.015] border border-white/[0.04] text-zinc-200 prose-chat shadow-sm',
          )}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap select-text">{message.content}</p>
          ) : (
            <div>{renderContent(message.content)}</div>
          )}

          {/* Copy button */}
          {!isUser && (
            <button
              onClick={handleCopy}
              className="absolute top-2.5 right-2.5 p-1 rounded-md opacity-0 group-hover:opacity-100 hover:bg-white/[0.04] border border-transparent hover:border-white/[0.06] transition-all cursor-pointer"
              title="Copy response"
            >
              {copied ? (
                <Check className="w-3.5 h-3.5 text-emerald-400" />
              ) : (
                <Copy className="w-3.5 h-3.5 text-zinc-500" />
              )}
            </button>
          )}
        </div>

        {/* Meta info */}
        <div className="flex items-center gap-2.5 text-[10px] text-zinc-500 px-1 select-none font-medium">
          <span>{formatTimestamp(message.timestamp)}</span>
          {message.tokens_used && message.tokens_used > 0 && (
            <Badge variant="secondary" className="text-[9px] px-1.5 py-0 h-4 bg-white/[0.02] border-white/[0.04] text-zinc-400 font-mono">
              {message.tokens_used} tokens
            </Badge>
          )}
          {chunks && chunks.length > 0 && (
            <Badge
              variant="secondary"
              className="text-[9px] px-1.5 py-0 h-4 bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 cursor-pointer hover:bg-cyan-500/20 transition-all font-mono"
              onClick={() => onSelectChunks?.(chunks)}
            >
              <FileText className="w-2.5 h-2.5 mr-0.5" />
              {chunks.length} sources
            </Badge>
          )}
        </div>
      </div>
    </div>
  );
}