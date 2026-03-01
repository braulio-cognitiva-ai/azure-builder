'use client';

import React, { useState } from 'react';
import { cn, formatCurrency } from '@/lib/utils';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Alert } from '@/components/ui/Alert';
import { ResourceCard } from './ResourceCard';
import { 
  Server, 
  DollarSign, 
  AlertTriangle, 
  RefreshCw,
  Filter,
  TrendingUp,
  TrendingDown
} from 'lucide-react';

interface ProjectSummary {
  total_resources: number;
  active: number;
  deleted: number;
  has_drift: number;
  estimated_monthly_cost: number;
  actual_cost_mtd: number;
  by_type: Record<string, {
    count: number;
    estimated_cost: number;
    actual_cost: number;
  }>;
}

interface DeployedResource {
  id: string;
  name: string;
  resource_type: string;
  resource_group: string;
  region: string;
  sku: string;
  status: 'active' | 'deleted' | 'failed' | 'unknown';
  monthly_cost_estimate: number;
  actual_cost_mtd: number;
  has_drift: boolean;
  deployed_at: string;
  last_synced_at: string;
}

interface InfrastructureDashboardProps {
  projectId: string;
  summary: ProjectSummary;
  resources: DeployedResource[];
  onRefresh?: () => void;
  onViewResource?: (resourceId: string) => void;
  loading?: boolean;
}

export function InfrastructureDashboard({
  projectId,
  summary,
  resources,
  onRefresh,
  onViewResource,
  loading = false
}: InfrastructureDashboardProps) {
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterType, setFilterType] = useState<string>('all');

  // Calculate projected monthly cost
  const daysInMonth = 30;
  const currentDay = new Date().getDate();
  const projectedMonthlyCost = (summary.actual_cost_mtd / currentDay) * daysInMonth;
  const costVariance = projectedMonthlyCost - summary.estimated_monthly_cost;
  const costVariancePercent = (costVariance / summary.estimated_monthly_cost) * 100;

  // Filter resources
  const filteredResources = resources.filter(r => {
    if (filterStatus !== 'all' && r.status !== filterStatus) return false;
    if (filterType !== 'all' && r.resource_type !== filterType) return false;
    return true;
  });

  // Get unique types
  const resourceTypes = Array.from(new Set(resources.map(r => r.resource_type)));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-100">Your Infrastructure</h2>
          <p className="text-gray-400 mt-1">
            Deployed resources and cost tracking
          </p>
        </div>
        <Button
          onClick={onRefresh}
          disabled={loading}
          variant="secondary"
        >
          <RefreshCw className={cn('h-4 w-4 mr-2', loading && 'animate-spin')} />
          {loading ? 'Syncing...' : 'Sync with Azure'}
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Total Resources */}
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-400">Total Resources</div>
              <div className="text-2xl font-bold text-gray-100 mt-1">
                {summary.active}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {summary.deleted} deleted
              </div>
            </div>
            <Server className="h-8 w-8 text-blue-400" />
          </div>
        </Card>

        {/* Estimated Cost */}
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-400">Estimated Monthly</div>
              <div className="text-2xl font-bold text-gray-100 mt-1">
                {formatCurrency(summary.estimated_monthly_cost)}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Budget target
              </div>
            </div>
            <DollarSign className="h-8 w-8 text-green-400" />
          </div>
        </Card>

        {/* Actual Cost MTD */}
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-400">Actual MTD</div>
              <div className="text-2xl font-bold text-gray-100 mt-1">
                {formatCurrency(summary.actual_cost_mtd)}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Projected: {formatCurrency(projectedMonthlyCost)}
              </div>
            </div>
            {costVariance > 0 ? (
              <TrendingUp className="h-8 w-8 text-yellow-400" />
            ) : (
              <TrendingDown className="h-8 w-8 text-green-400" />
            )}
          </div>
        </Card>

        {/* Drift Detection */}
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-400">Configuration Drift</div>
              <div className="text-2xl font-bold text-gray-100 mt-1">
                {summary.has_drift}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {summary.has_drift > 0 ? 'Resources changed' : 'No drift detected'}
              </div>
            </div>
            <AlertTriangle className={cn(
              'h-8 w-8',
              summary.has_drift > 0 ? 'text-yellow-400' : 'text-gray-600'
            )} />
          </div>
        </Card>
      </div>

      {/* Cost Variance Alert */}
      {Math.abs(costVariancePercent) > 10 && (
        <Alert variant={costVariance > 0 ? 'warning' : 'success'}>
          <strong>Cost Projection:</strong> Based on current usage, you're projected to 
          {costVariance > 0 ? ' exceed' : ' come under'} your estimate by{' '}
          <strong>{formatCurrency(Math.abs(costVariance))}</strong>
          {' '}({Math.abs(costVariancePercent).toFixed(0)}%)
        </Alert>
      )}

      {/* Drift Alert */}
      {summary.has_drift > 0 && (
        <Alert variant="warning" title="Configuration Drift Detected">
          {summary.has_drift} {summary.has_drift === 1 ? 'resource has' : 'resources have'} configuration 
          drift. This means the actual configuration differs from what was deployed. 
          Review the affected resources below.
        </Alert>
      )}

      {/* Resources by Type */}
      {Object.keys(summary.by_type).length > 0 && (
        <Card>
          <h3 className="text-lg font-semibold text-gray-200 mb-4">Resources by Type</h3>
          <div className="space-y-2">
            {Object.entries(summary.by_type).map(([type, data]) => (
              <div
                key={type}
                className="flex items-center justify-between p-3 rounded-lg bg-gray-800/30 border border-gray-700"
              >
                <div className="flex-1">
                  <div className="font-medium text-gray-200">{type}</div>
                  <div className="text-sm text-gray-400">
                    {data.count} {data.count === 1 ? 'resource' : 'resources'}
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-medium text-gray-200">
                    {formatCurrency(data.estimated_cost)}/mo
                  </div>
                  <div className="text-sm text-gray-400">
                    MTD: {formatCurrency(data.actual_cost)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Filters */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-gray-400" />
          <span className="text-sm text-gray-400">Filter:</span>
        </div>
        
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-gray-200 text-sm"
        >
          <option value="all">All Status</option>
          <option value="active">Active</option>
          <option value="deleted">Deleted</option>
          <option value="failed">Failed</option>
        </select>

        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          className="px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-gray-200 text-sm"
        >
          <option value="all">All Types</option>
          {resourceTypes.map(type => (
            <option key={type} value={type}>{type}</option>
          ))}
        </select>

        {(filterStatus !== 'all' || filterType !== 'all') && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setFilterStatus('all');
              setFilterType('all');
            }}
          >
            Clear Filters
          </Button>
        )}
      </div>

      {/* Resource List */}
      {filteredResources.length === 0 ? (
        <Card>
          <div className="text-center py-12">
            <Server className="h-12 w-12 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400">
              {resources.length === 0 
                ? 'No resources deployed yet'
                : 'No resources match the current filters'}
            </p>
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredResources.map(resource => (
            <ResourceCard
              key={resource.id}
              resource={resource}
              onViewDetails={onViewResource}
            />
          ))}
        </div>
      )}
    </div>
  );
}
