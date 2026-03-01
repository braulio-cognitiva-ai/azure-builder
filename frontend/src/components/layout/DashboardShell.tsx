import React from 'react';

interface DashboardShellProps {
  children: React.ReactNode;
}

export function DashboardShell({ children }: DashboardShellProps) {
  return (
    <div className="flex-1 overflow-auto">
      <div className="p-8">
        {children}
      </div>
    </div>
  );
}
