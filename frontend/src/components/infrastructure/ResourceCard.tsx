'use client';

import React from 'react';
import { cn, formatCurrency } from '@/lib/utils';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Progress } from '@/components/ui/Progress';
import { 
  Server, 
  Database, 
  HardDrive, 
  Network, 
  Key, 
  Activity,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Minus
} from 'lucide-react';

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

interface ResourceCardProps {
  resource: DeployedResource;
  className?: string;
  onViewDetails?: (resourceId: string) => void;
}

const getResourceIcon = (type: string) => {
  const lowerType = type.toLowerCase();
  
  if (lowerType.includes('compute') || lowerType.includes('virtualmachine')) {
    return Server;
  } else if (lowerType.includes('sql') || lowerType.includes('database') || lowerType.includes('cosmos')) {
    return Database;
  } else if (lowerType.includes('storage')) {
    return HardDrive;
  } else if (lowerType.includes('network') || lowerType.includes('vnet')) {
    return Network;
  } else if (lowerType.includes('keyvault') || lowerType.includes('vault')) {
    return Key;
  } else if (lowerType.includes('insights') || lowerType.includes('monitor')) {
    return Activity;
  }
  
  return Server;
};

const getStatusVariant = (status: string) => {
  switch (status) {
    case 'active':
      return 'success';
    case 'deleted':
      return 'default';
    case 'failed':
      return 'danger';
    default:
      return 'warning';
  }
};

const getCostTrend = (estimated: number, actual: number) => {
  if (!actual) return { icon: Minus, variant: 'default' as const, text: 'No data' };
  
  const projectedMonthly = (actual / new Date().getDate()) * 30;
  const variance = ((projectedMonthly - estimated) / estimated) * 100;
  
  if (Math.abs(variance) < 5) {
    return { icon: Minus, variant: 'success' as const, text: 'On track' };
  } else if (variance > 0) {
    return { 
      icon: TrendingUp, 
      variant: 'warning' as const, 
      text: `${variance.toFixed(0)}% over` 
    };
  } else {
    return { 
      icon: TrendingDown, 
      variant: 'success' as const, 
      text: `${Math.abs(variance).toFixed(0)}% under` 
    };
  }
};

export function ResourceCard({ resource, className, onViewDetails }: ResourceCardProps) {
  const Icon = getResourceIcon(resource.resource_type);
  const costTrend = getCostTrend(resource.monthly_cost_estimate, resource.actual_cost_mtd);
  const TrendIcon = costTrend.icon;
  
  // Calculate projected monthly cost
  const daysInMonth = 30;
  const currentDay = new Date().getDate();
  const projectedMonthlyCost = resource.actual_cost_mtd 
    ? (resource.actual_cost_mtd / currentDay) * daysInMonth 
    : 0;

  return (
    <Card
      className={cn(
        'hover:ring-2 hover:ring-blue-500/50 transition-all cursor-pointer',
        resource.has_drift && 'ring-2 ring-yellow-500/50',
        className
      )}
      onClick={() => onViewDetails?.(resource.id)}
    >
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-lg bg-blue-500/10">
              <Icon className="h-6 w-6 text-blue-400" />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 flex-wrap">
                <h3 className="font-semibold text-gray-200">{resource.name}</h3>
                <Badge variant={getStatusVariant(resource.status)}>
                  {resource.status}
                </Badge>
                {resource.has_drift && (
                  <Badge variant="warning">
                    <AlertTriangle className="h-3 w-3 mr-1" />
                    Drift Detected
                  </Badge>
                )}
              </div>
              <div className="text-sm text-gray-400 mt-1">
                {resource.resource_type}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {resource.resource_group} • {resource.region} • {resource.sku}
              </div>
            </div>
          </div>
        </div>

        {/* Cost Information */}
        <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-800">
          <div>
            <div className="text-xs text-gray-500 mb-1">Estimated Monthly</div>
            <div className="text-lg font-semibold text-gray-200">
              {formatCurrency(resource.monthly_cost_estimate)}
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-500 mb-1">
              MTD (Projected: {formatCurrency(projectedMonthlyCost)})
            </div>
            <div className="flex items-center gap-2">
              <div className="text-lg font-semibold text-gray-200">
                {formatCurrency(resource.actual_cost_mtd)}
              </div>
              <Badge variant={costTrend.variant} className="text-xs">
                <TrendIcon className="h-3 w-3 mr-1" />
                {costTrend.text}
              </Badge>
            </div>
          </div>
        </div>

        {/* Cost Progress */}
        {resource.actual_cost_mtd > 0 && (
          <div>
            <div className="flex items-center justify-between text-xs text-gray-400 mb-1">
              <span>Cost Progress</span>
              <span>
                {((resource.actual_cost_mtd / resource.monthly_cost_estimate) * 100).toFixed(0)}%
              </span>
            </div>
            <Progress
              value={resource.actual_cost_mtd}
              max={resource.monthly_cost_estimate}
              variant={
                projectedMonthlyCost > resource.monthly_cost_estimate * 1.1 
                  ? 'warning' 
                  : 'success'
              }
            />
          </div>
        )}

        {/* Metadata */}
        <div className="text-xs text-gray-500 pt-2 border-t border-gray-800">
          Deployed: {new Date(resource.deployed_at).toLocaleDateString()} • 
          Last synced: {new Date(resource.last_synced_at).toLocaleDateString()}
        </div>
      </div>
    </Card>
  );
}
