import React, { forwardRef } from 'react';
import { cn } from '@/lib/utils';
import { DollarSign } from 'lucide-react';

interface CurrencyInputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label?: string;
  error?: string;
  helpText?: string;
}

export const CurrencyInput = forwardRef<HTMLInputElement, CurrencyInputProps>(
  ({ label, error, helpText, className, ...props }, ref) => {
    return (
      <div className="space-y-2">
        {label && (
          <label className="block text-sm font-medium text-gray-300">
            {label}
          </label>
        )}
        <div className="relative">
          <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
            <DollarSign className="h-5 w-5 text-gray-500" />
          </div>
          <input
            ref={ref}
            type="number"
            step="0.01"
            min="0"
            className={cn(
              'w-full pl-10 pr-20 py-2 bg-gray-900 border border-gray-700 rounded-lg',
              'text-gray-100 placeholder-gray-500',
              'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              error && 'border-red-500 focus:ring-red-500',
              className
            )}
            {...props}
          />
          <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
            <span className="text-sm text-gray-500">/month</span>
          </div>
        </div>
        {helpText && !error && (
          <p className="text-xs text-gray-500">{helpText}</p>
        )}
        {error && (
          <p className="text-xs text-red-400">{error}</p>
        )}
      </div>
    );
  }
);

CurrencyInput.displayName = 'CurrencyInput';
