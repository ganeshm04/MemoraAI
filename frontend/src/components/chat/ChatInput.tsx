'use client';

import { useState, useRef, useEffect } from 'react';
import { Paperclip } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  disabled?: boolean;
  placeholder?: string;
}

export function ChatInput({
  value,
  onChange,
  onSubmit,
  disabled = false,
  placeholder = 'Type your message...',
}: ChatInputProps) {
  const [isFocused, setIsFocused] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 150)}px`;
    }
  }, [value]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSubmit();
    }
  };

  return (
    <div
      className={cn(
        'flex items-end gap-2.5 flex-1 rounded-xl border glass-input px-3.5 py-2.5 transition-all shadow-inner',
        isFocused ? 'border-cyan-500/45 ring-2 ring-cyan-500/10 bg-white/[0.03]' : 'border-white/[0.05]',
      )}
    >
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onFocus={() => setIsFocused(true)}
        onBlur={() => setIsFocused(false)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        placeholder={placeholder}
        rows={1}
        className="flex-1 resize-none bg-transparent border-none outline-none text-xs leading-relaxed placeholder:text-zinc-600 text-zinc-100 disabled:opacity-50 py-0.5"
        style={{ maxHeight: '150px' }}
      />
      <div className="flex items-center gap-1.5 shrink-0 select-none pb-0.5">
        {value.length > 0 && (
          <span className="text-[9px] font-mono text-zinc-500">
            {value.length} ch
          </span>
        )}
        <kbd className="hidden sm:inline-flex h-4 items-center gap-0.5 rounded border border-white/[0.06] bg-white/[0.02] px-1.5 font-mono text-[8px] font-bold text-zinc-500">
          <span>⌘</span><span>⏎</span>
        </kbd>
      </div>
    </div>
  );
}