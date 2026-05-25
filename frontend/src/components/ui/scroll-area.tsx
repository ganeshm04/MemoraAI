import * as React from 'react';
import { cn } from '@/lib/utils';

export interface ScrollAreaProps extends React.HTMLAttributes<HTMLDivElement> {
  orientation?: 'vertical' | 'horizontal' | 'both';
}

const ScrollArea = React.forwardRef<HTMLDivElement, ScrollAreaProps>(
  ({ className, orientation = 'vertical', ...props }, ref) => (
    <div
      ref={ref}
      className={cn('relative overflow-hidden', className)}
      {...props}
    >
      <div
        className={cn(
          'h-full w-full rounded-[inherit]',
          orientation === 'vertical' || orientation === 'both' ? 'overflow-y-auto' : '',
          orientation === 'horizontal' || orientation === 'both' ? 'overflow-x-auto' : ''
        )}
      >
        {props.children}
      </div>
    </div>
  )
);
ScrollArea.displayName = 'ScrollArea';

export { ScrollArea };