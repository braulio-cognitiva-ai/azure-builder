'use client';

import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { Alert } from '@/components/ui/Alert';
import { Badge } from '@/components/ui/Badge';
import { Progress } from '@/components/ui/Progress';
import { Shield, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react';

interface SecurityIssue {
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  category: string;
  resource_type?: string;
  resource_name?: string;
  issue: string;
  recommendation: string;
  doc_link?: string;
}

interface SecurityReport {
  score: number;
  passed_checks: number;
  total_checks: number;
  has_critical: boolean;
  has_high: boolean;
  issues: SecurityIssue[];
}

interface SecurityScoreProps {
  report: SecurityReport;
  className?: string;
  compact?: boolean;
}

export function SecurityScore({ report, className, compact = false }: SecurityScoreProps) {
  const [expanded, setExpanded] = useState(!compact);

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'success';
    if (score >= 70) return 'warning';
    return 'danger';
  };

  const getSeverityVariant = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'danger';
      case 'high':
        return 'danger';
      case 'medium':
        return 'warning';
      case 'low':
        return 'info';
      default:
        return 'default';
    }
  };

  const getSeverityLabel = (severity: string) => {
    return severity.toUpperCase();
  };

  const scoreColor = getScoreColor(report.score);
  const criticalCount = report.issues.filter(i => i.severity === 'critical').length;
  const highCount = report.issues.filter(i => i.severity === 'high').length;
  const mediumCount = report.issues.filter(i => i.severity === 'medium').length;

  return (
    <div className={cn('space-y-4', className)}>
      {/* Score Header */}
      <div
        className={cn(
          'flex items-center justify-between p-4 rounded-lg border',
          compact && 'cursor-pointer hover:bg-gray-800/50',
          report.has_critical && 'bg-red-500/10 border-red-500/20',
          report.has_high && !report.has_critical && 'bg-yellow-500/10 border-yellow-500/20',
          !report.has_critical && !report.has_high && 'bg-green-500/10 border-green-500/20'
        )}
        onClick={compact ? () => setExpanded(!expanded) : undefined}
      >
        <div className="flex items-center gap-3">
          <Shield className={cn(
            'h-6 w-6',
            report.has_critical && 'text-red-400',
            report.has_high && !report.has_critical && 'text-yellow-400',
            !report.has_critical && !report.has_high && 'text-green-400'
          )} />
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-gray-200">Security Score</span>
              <Badge variant={scoreColor}>
                {report.score}/100
              </Badge>
            </div>
            <div className="text-sm text-gray-400 mt-1">
              {report.passed_checks} of {report.total_checks} checks passed
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {report.has_critical && (
            <Badge variant="danger">
              {criticalCount} Critical
            </Badge>
          )}
          {report.has_high && (
            <Badge variant="danger">
              {highCount} High
            </Badge>
          )}
          {mediumCount > 0 && (
            <Badge variant="warning">
              {mediumCount} Medium
            </Badge>
          )}
          {compact && (
            expanded ? <ChevronUp className="h-5 w-5 text-gray-400" /> : <ChevronDown className="h-5 w-5 text-gray-400" />
          )}
        </div>
      </div>

      {/* Progress Bar */}
      {expanded && (
        <Progress
          value={report.score}
          max={100}
          variant={scoreColor}
          className="w-full"
        />
      )}

      {/* Summary Alert */}
      {expanded && report.has_critical && (
        <Alert variant="danger" title="Critical Security Issues">
          This architecture has {criticalCount} critical security {criticalCount === 1 ? 'issue' : 'issues'} that must be addressed before deployment.
        </Alert>
      )}

      {expanded && report.has_high && !report.has_critical && (
        <Alert variant="warning" title="Security Recommendations">
          This architecture has {highCount} high-severity security {highCount === 1 ? 'recommendation' : 'recommendations'}.
        </Alert>
      )}

      {expanded && !report.has_critical && !report.has_high && report.issues.length === 0 && (
        <Alert variant="success" title="No Security Issues">
          This architecture passed all security checks. Great job!
        </Alert>
      )}

      {/* Issues List */}
      {expanded && report.issues.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-sm font-semibold text-gray-300">Security Issues & Recommendations</h4>
          {report.issues.map((issue, index) => (
            <div
              key={index}
              className={cn(
                'p-4 rounded-lg border',
                issue.severity === 'critical' && 'bg-red-500/5 border-red-500/20',
                issue.severity === 'high' && 'bg-yellow-500/5 border-yellow-500/20',
                issue.severity === 'medium' && 'bg-yellow-500/5 border-yellow-500/20',
                (issue.severity === 'low' || issue.severity === 'info') && 'bg-gray-800/50 border-gray-700'
              )}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 space-y-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    <Badge variant={getSeverityVariant(issue.severity)}>
                      {getSeverityLabel(issue.severity)}
                    </Badge>
                    <span className="text-xs text-gray-500">{issue.category}</span>
                    {issue.resource_name && (
                      <span className="text-xs text-gray-500">• {issue.resource_name}</span>
                    )}
                  </div>
                  
                  <div className="text-sm text-gray-300">
                    <strong className="text-gray-200">Issue:</strong> {issue.issue}
                  </div>
                  
                  <div className="text-sm text-gray-400">
                    <strong className="text-gray-300">Recommendation:</strong> {issue.recommendation}
                  </div>
                </div>
                
                {issue.doc_link && (
                  <a
                    href={issue.doc_link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-shrink-0 p-2 rounded-lg hover:bg-gray-800 text-gray-400 hover:text-gray-200 transition-colors"
                    title="View documentation"
                  >
                    <ExternalLink className="h-4 w-4" />
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
