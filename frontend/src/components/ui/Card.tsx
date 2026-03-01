import React from 'react';
import { cn } from '@/lib/utils';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  header?: React.ReactNode;
  noPadding?: boolean;
}

export function Card({ children, className, header, noPadding }: CardProps) {
  return (
    <div className={cn('glass-card', className)}>
      {header && (
        <div className="border-b border-gray-800 -mt-6 -mx-6 px-6 py-4 mb-6">
          {header}
        </div>
      )}
      <div className={noPadding ? '-m-6' : ''}>
        {children}
      </div>
    </div>
  );
}
