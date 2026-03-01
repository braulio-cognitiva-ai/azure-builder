'use client';

import { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { formatDateTime } from '@/lib/utils';
import { Shield, ChevronLeft, ChevronRight } from 'lucide-react';

const mockAudit = [
  { id: '1', timestamp: '2026-02-27T20:30:00Z', user_name: 'Zephiroth', action: 'project.create', entity_type: 'Project', entity_name: 'Production API', details: 'Created new project' },
  { id: '2', timestamp: '2026-02-27T19:15:00Z', user_name: 'Zephiroth', action: 'deployment.approve', entity_type: 'Deployment', entity_name: 'dep-abc123', details: 'Approved deployment for Production API' },
  { id: '3', timestamp: '2026-02-27T18:00:00Z', user_name: 'Zephiroth', action: 'deployment.execute', entity_type: 'Deployment', entity_name: 'dep-abc123', details: '3 resources deployed successfully' },
  { id: '4', timestamp: '2026-02-27T14:22:00Z', user_name: 'admin@contoso.com', action: 'user.login', entity_type: 'User', entity_name: 'admin@contoso.com', details: 'Login from 192.168.1.50' },
  { id: '5', timestamp: '2026-02-26T16:45:00Z', user_name: 'Zephiroth', action: 'proposal.create', entity_type: 'Proposal', entity_name: 'prop-def456', details: 'Requested: "Deploy a web app with Redis cache"' },
  { id: '6', timestamp: '2026-02-26T15:30:00Z', user_name: 'Zephiroth', action: 'proposal.select', entity_type: 'Proposal', entity_name: 'prop-def456', details: 'Selected option 2: Standard tier' },
  { id: '7', timestamp: '2026-02-26T11:00:00Z', user_name: 'admin@contoso.com', action: 'azure.connect', entity_type: 'Azure', entity_name: 'sub-prod-001', details: 'Connected Azure subscription' },
  { id: '8', timestamp: '2026-02-25T22:10:00Z', user_name: 'Zephiroth', action: 'project.update', entity_type: 'Project', entity_name: 'Staging Env', details: 'Updated description' },
  { id: '9', timestamp: '2026-02-25T17:30:00Z', user_name: 'Zephiroth', action: 'deployment.rollback', entity_type: 'Deployment', entity_name: 'dep-ghi789', details: 'Rolled back due to health check failure' },
  { id: '10', timestamp: '2026-02-25T10:00:00Z', user_name: 'admin@contoso.com', action: 'user.login', entity_type: 'User', entity_name: 'admin@contoso.com', details: 'Login from 10.0.0.1' },
  { id: '11', timestamp: '2026-02-24T14:00:00Z', user_name: 'Zephiroth', action: 'project.delete', entity_type: 'Project', entity_name: 'Test Project', details: 'Deleted project and all resources' },
  { id: '12', timestamp: '2026-02-24T09:00:00Z', user_name: 'Zephiroth', action: 'project.create', entity_type: 'Project', entity_name: 'ML Pipeline', details: 'Created new project' },
];

const actionColors: Record<string, 'success' | 'warning' | 'danger' | 'info' | 'default'> = {
  'project.create': 'success',
  'project.update': 'info',
  'project.delete': 'danger',
  'deployment.approve': 'success',
  'deployment.execute': 'info',
  'deployment.rollback': 'warning',
  'proposal.create': 'info',
  'proposal.select': 'default',
  'user.login': 'default',
  'azure.connect': 'success',
};

const PAGE_SIZE = 8;

export default function AuditPage() {
  const [actionFilter, setActionFilter] = useState('all');
  const [page, setPage] = useState(0);

  const actionTypes = ['all', ...Array.from(new Set(mockAudit.map(a => a.action)))];

  const filtered = actionFilter === 'all' ? mockAudit : mockAudit.filter(a => a.action === actionFilter);
  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);
  const paged = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-100">Audit Log</h1>
          <p className="text-gray-400 mt-1">Track all actions across your organization.</p>
        </div>
        <Shield className="w-8 h-8 text-gray-600" />
      </div>

      {/* Filters */}
      <Card>
        <div className="flex flex-wrap items-center gap-4">
          <div>
            <label className="text-sm text-gray-400 block mb-1">Action Type</label>
            <select
              value={actionFilter}
              onChange={e => { setActionFilter(e.target.value); setPage(0); }}
              className="bg-gray-800 border border-gray-700 text-gray-200 rounded-lg px-3 py-2 text-sm focus:border-[#0078D4] focus:outline-none"
            >
              {actionTypes.map(a => (
                <option key={a} value={a}>{a === 'all' ? 'All Actions' : a}</option>
              ))}
            </select>
          </div>
        </div>
      </Card>

      {/* Table */}
      <Card noPadding>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-gray-400">
                <th className="text-left px-6 py-4 font-medium">Time</th>
                <th className="text-left px-6 py-4 font-medium">User</th>
                <th className="text-left px-6 py-4 font-medium">Action</th>
                <th className="text-left px-6 py-4 font-medium">Entity</th>
                <th className="text-left px-6 py-4 font-medium">Details</th>
              </tr>
            </thead>
            <tbody>
              {paged.map(entry => (
                <tr key={entry.id} className="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors">
                  <td className="px-6 py-4 text-gray-400 whitespace-nowrap">{formatDateTime(entry.timestamp)}</td>
                  <td className="px-6 py-4 text-gray-300">{entry.user_name}</td>
                  <td className="px-6 py-4">
                    <Badge variant={actionColors[entry.action] || 'default'}>{entry.action}</Badge>
                  </td>
                  <td className="px-6 py-4 text-gray-300">
                    <span className="text-gray-500 text-xs">{entry.entity_type} / </span>
                    {entry.entity_name}
                  </td>
                  <td className="px-6 py-4 text-gray-400 max-w-xs truncate">{entry.details}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {/* Pagination */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-gray-800">
          <span className="text-sm text-gray-500">
            Showing {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, filtered.length)} of {filtered.length}
          </span>
          <div className="flex gap-2">
            <Button variant="secondary" size="sm" disabled={page === 0} onClick={() => setPage(p => p - 1)}>
              <ChevronLeft className="w-4 h-4" /> Prev
            </Button>
            <Button variant="secondary" size="sm" disabled={page >= totalPages - 1} onClick={() => setPage(p => p + 1)}>
              Next <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
