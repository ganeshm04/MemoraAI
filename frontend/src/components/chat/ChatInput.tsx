'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Paperclip, X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export function ChatInput({
  value,
  onChange,
  disabled = false,
  placeholder = 'Type your message...',
}: ChatInputProps) {
  const [isFocused, setIsFocused] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [value]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
    }
  };

  return (
    <div
      className={cn(
        'flex items-center gap-2 flex-1 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 transition-colors',
        isFocused && 'border-blue-500 ring-2 ring-blue-500/20'
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
        className="flex-1 resize-none bg-transparent border-none outline-none text-sm placeholder:text-slate-400 dark:text-slate-300 disabled:opacity-50"
        style={{ maxHeight: '150px' }}
      />
    </div>
  );
}