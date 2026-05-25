'use client';

import { motion } from 'framer-motion';
import { User, Bot, FileText } from 'lucide-react';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { cn, formatTimestamp } from '@/lib/utils';
import type { Message } from '@/types';

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

  return (
    <div className={cn('flex gap-3', isUser && 'flex-row-reverse')}>
      <Avatar className="w-8 h-8 shrink-0">
        {isUser ? (
          <>
            <AvatarImage />
            <AvatarFallback className="bg-blue-500 text-white">
              <User className="w-4 h-4" />
            </AvatarFallback>
          </>
        ) : (
          <>
            <AvatarImage />
            <AvatarFallback className="bg-purple-500 text-white">
              <Bot className="w-4 h-4" />
            </AvatarFallback>
          </>
        )}
      </Avatar>

      <div className={cn('flex flex-col gap-1 max-w-[80%]', isUser && 'items-end')}>
        <div
          className={cn(
            'rounded-lg px-4 py-2 text-sm',
            isUser && 'bg-blue-500 text-white',
            !isUser && !isSystem && 'bg-slate-100 dark:bg-slate-700 text-slate-900 dark:text-white',
            isSystem && 'bg-yellow-100 dark:bg-yellow-900 text-yellow-900 dark:text-yellow-100'
          )}
        >
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>

        <div className="flex items-center gap-2 text-xs text-slate-400 dark:text-slate-500">
          <span>{formatTimestamp(message.timestamp)}</span>
          {message.tokens_used && (
            <Badge variant="secondary" className="text-xs">
              {message.tokens_used} tokens
            </Badge>
          )}
          {message.chunks && message.chunks.length > 0 && (
            <Badge variant="outline" className="text-xs">
              <FileText className="w-3 h-3 mr-1" />
              {message.chunks.length} sources
            </Badge>
          )}
        </div>
      </div>
    </div>
  );
}