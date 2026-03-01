import React from 'react';
import { cn } from '@/lib/utils';
import { AlertCircle, CheckCircle, Info, AlertTriangle } from 'lucide-react';

interface AlertProps {
  children: React.ReactNode;
  variant?: 'info' | 'success' | 'warning' | 'danger';
  title?: string;
  className?: string;
}

export function Alert({
  children,
  variant = 'info',
  title,
  className
}: AlertProps) {
  const variants = {
    info: {
      container: 'bg-blue-500/10 border-blue-500/20 text-blue-400',
      icon: Info,
    },
    success: {
      container: 'bg-green-500/10 border-green-500/20 text-green-400',
      icon: CheckCircle,
    },
    warning: {
      container: 'bg-yellow-500/10 border-yellow-500/20 text-yellow-400',
      icon: AlertTriangle,
    },
    danger: {
      container: 'bg-red-500/10 border-red-500/20 text-red-400',
      icon: AlertCircle,
    },
  };

  const { container, icon: Icon } = variants[variant];

  return (
    <div className={cn('rounded-lg border p-4', container, className)}>
      <div className="flex gap-3">
        <Icon className="h-5 w-5 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          {title && (
            <div className="font-semibold mb-1">{title}</div>
          )}
          <div className="text-sm opacity-90">{children}</div>
        </div>
      </div>
    </div>
  );
}
