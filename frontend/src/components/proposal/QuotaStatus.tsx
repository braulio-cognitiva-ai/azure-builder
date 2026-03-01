'use client';

import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { Alert } from '@/components/ui/Alert';
import { Badge } from '@/components/ui/Badge';
import { Progress } from '@/components/ui/Progress';
import { Gauge, ChevronDown, ChevronUp } from 'lucide-react';

interface QuotaCheck {
  resource_type: string;
  quota_name: string;
  current_usage: number;
  quota_limit: number;
  requested: number;
  available: number;
  after_deployment: number;
  status: 'ok' | 'warning' | 'exceeded' | 'unknown';
  message: string;
}

interface QuotaReport {
  overall_status: 'ok' | 'warning' | 'exceeded' | 'unknown';
  can_deploy: boolean;
  warnings: string[];
  errors: string[];
  checks: QuotaCheck[];
}

interface QuotaStatusProps {
  report: QuotaReport;
  className?: string;
  compact?: boolean;
}

export function QuotaStatus({ report, className, compact = false }: QuotaStatusProps) {
  const [expanded, setExpanded] = useState(!compact);

  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'ok':
        return 'success';
      case 'warning':
        return 'warning';
      case 'exceeded':
        return 'danger';
      default:
        return 'default';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'ok':
        return '✓ Quota Available';
      case 'warning':
        return '⚠️ Quota Warning';
      case 'exceeded':
        return '❌ Quota Exceeded';
      default:
        return 'Unknown';
    }
  };

  const getProgressVariant = (check: QuotaCheck) => {
    const afterPercentage = (check.after_deployment / check.quota_limit) * 100;
    if (check.status === 'exceeded') return 'danger';
    if (afterPercentage >= 80) return 'warning';
    return 'success';
  };

  return (
    <div className={cn('space-y-4', className)}>
      {/* Status Header */}
      <div
        className={cn(
          'flex items-center justify-between p-4 rounded-lg border',
          compact && 'cursor-pointer hover:bg-gray-800/50',
          report.overall_status === 'exceeded' && 'bg-red-500/10 border-red-500/20',
          report.overall_status === 'warning' && 'bg-yellow-500/10 border-yellow-500/20',
          report.overall_status === 'ok' && 'bg-green-500/10 border-green-500/20',
          report.overall_status === 'unknown' && 'bg-gray-800/50 border-gray-700'
        )}
        onClick={compact ? () => setExpanded(!expanded) : undefined}
      >
        <div className="flex items-center gap-3">
          <Gauge className={cn(
            'h-6 w-6',
            report.overall_status === 'exceeded' && 'text-red-400',
            report.overall_status === 'warning' && 'text-yellow-400',
            report.overall_status === 'ok' && 'text-green-400',
            report.overall_status === 'unknown' && 'text-gray-400'
          )} />
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-gray-200">Quota Status</span>
              <Badge variant={getStatusVariant(report.overall_status)}>
                {getStatusLabel(report.overall_status)}
              </Badge>
            </div>
            {report.can_deploy ? (
              <div className="text-sm text-gray-400 mt-1">
                Sufficient quota available for deployment
              </div>
            ) : (
              <div className="text-sm text-red-400 mt-1">
                Insufficient quota - deployment will fail
              </div>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          {!report.can_deploy && (
            <Badge variant="danger">
              Cannot Deploy
            </Badge>
          )}
          {report.warnings.length > 0 && (
            <Badge variant="warning">
              {report.warnings.length} {report.warnings.length === 1 ? 'Warning' : 'Warnings'}
            </Badge>
          )}
          {compact && (
            expanded ? <ChevronUp className="h-5 w-5 text-gray-400" /> : <ChevronDown className="h-5 w-5 text-gray-400" />
          )}
        </div>
      </div>

      {/* Errors */}
      {expanded && report.errors.length > 0 && (
        <Alert variant="danger" title="Quota Exceeded">
          <ul className="list-disc list-inside space-y-1">
            {report.errors.map((error, index) => (
              <li key={index} className="text-sm">{error}</li>
            ))}
          </ul>
        </Alert>
      )}

      {/* Warnings */}
      {expanded && report.warnings.length > 0 && report.errors.length === 0 && (
        <Alert variant="warning" title="Quota Warnings">
          <ul className="list-disc list-inside space-y-1">
            {report.warnings.map((warning, index) => (
              <li key={index} className="text-sm">{warning}</li>
            ))}
          </ul>
        </Alert>
      )}

      {/* Success */}
      {expanded && report.can_deploy && report.warnings.length === 0 && report.errors.length === 0 && (
        <Alert variant="success" title="Quota Available">
          Your subscription has sufficient quota for this deployment.
        </Alert>
      )}

      {/* Quota Breakdown */}
      {expanded && report.checks.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-sm font-semibold text-gray-300">Quota Details</h4>
          {report.checks.map((check, index) => (
            <div
              key={index}
              className="p-4 rounded-lg border border-gray-700 bg-gray-800/30 space-y-3"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-200">{check.quota_name}</span>
                    <Badge variant={getStatusVariant(check.status)}>
                      {check.status.toUpperCase()}
                    </Badge>
                  </div>
                  <div className="text-sm text-gray-400 mt-1">
                    {check.resource_type}
                  </div>
                </div>
              </div>

              {/* Current Usage Progress */}
              <div>
                <div className="flex items-center justify-between text-xs text-gray-400 mb-1">
                  <span>Current Usage</span>
                  <span>{check.current_usage} / {check.quota_limit}</span>
                </div>
                <Progress
                  value={check.current_usage}
                  max={check.quota_limit}
                  variant={check.current_usage / check.quota_limit < 0.8 ? 'success' : 'warning'}
                />
              </div>

              {/* After Deployment Progress */}
              <div>
                <div className="flex items-center justify-between text-xs text-gray-400 mb-1">
                  <span>After Deployment</span>
                  <span>
                    {check.after_deployment} / {check.quota_limit}
                    <span className="ml-2 text-blue-400">
                      (+{check.requested})
                    </span>
                  </span>
                </div>
                <Progress
                  value={check.after_deployment}
                  max={check.quota_limit}
                  variant={getProgressVariant(check)}
                />
              </div>

              {/* Status Message */}
              <div className="text-xs text-gray-400 border-t border-gray-700 pt-2">
                {check.message}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Unknown Status */}
      {expanded && report.overall_status === 'unknown' && (
        <Alert variant="info" title="Quota Check Unavailable">
          Unable to verify quota. This might be due to missing Azure credentials or insufficient permissions.
          The deployment may still succeed if you have sufficient quota.
        </Alert>
      )}
    </div>
  );
}
