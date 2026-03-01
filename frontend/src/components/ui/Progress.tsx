import React from 'react';
import { cn } from '@/lib/utils';

interface ProgressProps {
  value: number;
  max?: number;
  variant?: 'default' | 'success' | 'warning' | 'danger';
  showLabel?: boolean;
  className?: string;
}

export function Progress({
  value,
  max = 100,
  variant = 'default',
  showLabel = false,
  className
}: ProgressProps) {
  const percentage = Math.min((value / max) * 100, 100);
  
  const variants = {
    default: 'bg-blue-500',
    success: 'bg-green-500',
    warning: 'bg-yellow-500',
    danger: 'bg-red-500',
  };

  return (
    <div className={cn('relative', className)}>
      <div className="w-full bg-gray-800 rounded-full h-2 overflow-hidden">
        <div
          className={cn(
            'h-full transition-all duration-300 ease-in-out',
            variants[variant]
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
      {showLabel && (
        <span className="text-xs text-gray-400 mt-1">
          {value} / {max}
        </span>
      )}
    </div>
  );
}
