'use client';

import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { FolderKanban, Rocket, DollarSign, Plus, LayoutGrid, Activity, ArrowRight } from 'lucide-react';

const stats = [
  { label: 'Total Projects', value: '12', icon: FolderKanban, color: 'text-blue-400' },
  { label: 'Active Deployments', value: '3', icon: Rocket, color: 'text-green-400' },
  { label: 'Monthly Cost', value: '$1,247', icon: DollarSign, color: 'text-yellow-400' },
];

const recentActivity = [
  { id: '1', action: 'Deployed', entity: 'Production Web App', time: '2 hours ago', status: 'success' },
  { id: '2', action: 'Created proposal for', entity: 'ML Pipeline', time: '5 hours ago', status: 'info' },
  { id: '3', action: 'Updated', entity: 'Staging Environment', time: '1 day ago', status: 'info' },
  { id: '4', action: 'Rolled back', entity: 'API Gateway v2', time: '2 days ago', status: 'warning' },
];

export default function DashboardPage() {
  const { user } = useAuth();
  const router = useRouter();

  return (
    <div className="space-y-8">
      {/* Welcome */}
      <div>
        <h1 className="text-3xl font-bold text-gray-100">
          Welcome back, {user?.name || 'there'} 👋
        </h1>
        <p className="text-gray-400 mt-1">Here&apos;s what&apos;s happening with your Azure infrastructure.</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.label}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">{stat.label}</p>
                  <p className="text-3xl font-bold text-gray-100 mt-1">{stat.value}</p>
                </div>
                <div className="w-12 h-12 bg-gray-800 rounded-lg flex items-center justify-center">
                  <Icon className={`w-6 h-6 ${stat.color}`} />
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Quick Actions + Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Quick Actions */}
        <Card>
          <h2 className="text-lg font-semibold text-gray-100 mb-4">Quick Actions</h2>
          <div className="space-y-3">
            <Button className="w-full justify-start gap-2" onClick={() => router.push('/projects')}>
              <Plus className="w-4 h-4" /> New Project
            </Button>
            <Button variant="secondary" className="w-full justify-start gap-2" onClick={() => router.push('/templates')}>
              <LayoutGrid className="w-4 h-4" /> Browse Templates
            </Button>
          </div>
        </Card>

        {/* Recent Activity */}
        <div className="lg:col-span-2">
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-100">Recent Activity</h2>
              <Activity className="w-5 h-5 text-gray-400" />
            </div>
            <div className="space-y-4">
              {recentActivity.map((item) => (
                <div key={item.id} className="flex items-center justify-between py-2 border-b border-gray-800 last:border-0">
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${
                      item.status === 'success' ? 'bg-green-400' :
                      item.status === 'warning' ? 'bg-yellow-400' : 'bg-blue-400'
                    }`} />
                    <span className="text-gray-300">
                      {item.action} <span className="text-gray-100 font-medium">{item.entity}</span>
                    </span>
                  </div>
                  <span className="text-sm text-gray-500">{item.time}</span>
                </div>
              ))}
            </div>
            <button
              onClick={() => router.push('/audit')}
              className="flex items-center gap-1 text-sm text-[#0078D4] hover:text-[#106EBE] mt-4 transition-smooth"
            >
              View all activity <ArrowRight className="w-4 h-4" />
            </button>
          </Card>
        </div>
      </div>
    </div>
  );
}
