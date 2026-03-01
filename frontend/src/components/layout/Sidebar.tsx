'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, FolderKanban, LayoutGrid, ScrollText, Settings, ChevronLeft, Cloud } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useState } from 'react';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Projects', href: '/projects', icon: FolderKanban },
  { name: 'Templates', href: '/templates', icon: LayoutGrid },
  { name: 'Audit Log', href: '/audit', icon: ScrollText },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div
      className={cn(
        'h-full bg-gray-900 border-r border-gray-800 flex flex-col transition-all duration-300',
        collapsed ? 'w-16' : 'w-64'
      )}
    >
      {/* Logo */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-gray-800">
        {!collapsed && (
          <div className="flex items-center gap-2">
            <Cloud className="w-8 h-8 text-[#0078D4]" />
            <span className="text-lg font-bold text-gray-100">Azure Builder</span>
          </div>
        )}
        {collapsed && <Cloud className="w-8 h-8 text-[#0078D4] mx-auto" />}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="text-gray-400 hover:text-gray-100 transition-smooth"
        >
          <ChevronLeft className={cn('w-5 h-5 transition-transform', collapsed && 'rotate-180')} />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {navigation.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
          const Icon = item.icon;
          
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-smooth',
                isActive
                  ? 'bg-[#0078D4] text-white'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-gray-100',
                collapsed && 'justify-center'
              )}
              title={collapsed ? item.name : undefined}
            >
              <Icon className="w-5 h-5 flex-shrink-0" />
              {!collapsed && <span>{item.name}</span>}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
