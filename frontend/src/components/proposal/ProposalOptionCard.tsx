'use client';

import React, { useState } from 'react';
import { cn, formatCurrency } from '@/lib/utils';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { MermaidDiagram } from '@/components/diagram/MermaidDiagram';
import { SecurityScore } from './SecurityScore';
import { QuotaStatus } from './QuotaStatus';
import { IntegrationSuggestions } from './IntegrationSuggestions';
import { BudgetBadge } from './BudgetBadge';
import { CheckCircle, ChevronDown, ChevronUp, Download, FileCode } from 'lucide-react';

interface ProposalOption {
  option_number: number;
  name: string;
  description: string;
  architecture_diagram: string;
  monthly_cost: number;
  resources_json: {
    resources: any[];
  };
  cost_estimate_json: {
    estimates: any[];
  };
  pros_cons_json: {
    pros: string[];
    cons: string[];
    security_report?: any;
    quota_report?: any;
    budget_exceeded?: boolean;
  };
}

interface ProposalOptionCardProps {
  option: ProposalOption;
  budgetLimit?: number;
  selected?: boolean;
  onSelect?: (optionNumber: number) => void;
  onDownloadBicep?: (optionNumber: number) => void;
  className?: string;
}

export function ProposalOptionCard({
  option,
  budgetLimit,
  selected = false,
  onSelect,
  onDownloadBicep,
  className
}: ProposalOptionCardProps) {
  const [showDetails, setShowDetails] = useState(false);
  const [activeTab, setActiveTab] = useState<'diagram' | 'resources' | 'costs'>('diagram');

  const { pros_cons_json } = option;
  const hasSecurityReport = pros_cons_json.security_report;
  const hasQuotaReport = pros_cons_json.quota_report;
  const budgetExceeded = pros_cons_json.budget_exceeded;

  // Determine overall status
  const canDeploy = hasQuotaReport ? pros_cons_json.quota_report.can_deploy : true;
  const hasCriticalSecurity = hasSecurityReport && pros_cons_json.security_report.has_critical;
  const hasHighSecurity = hasSecurityReport && pros_cons_json.security_report.has_high;

  return (
    <Card
      className={cn(
        'transition-all duration-200',
        selected && 'ring-2 ring-blue-500',
        !canDeploy && 'opacity-75',
        className
      )}
    >
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <h3 className="text-xl font-bold text-gray-100">
                Option {option.option_number}: {option.name}
              </h3>
              {selected && (
                <Badge variant="success">
                  <CheckCircle className="h-3 w-3 mr-1" />
                  Selected
                </Badge>
              )}
            </div>
            <p className="text-gray-400 text-sm leading-relaxed">
              {option.description}
            </p>
          </div>

          <div className="flex flex-col items-end gap-2">
            <div className="text-right">
              <div className="text-2xl font-bold text-gray-100">
                {formatCurrency(option.monthly_cost)}
              </div>
              <div className="text-xs text-gray-500">per month</div>
            </div>
            <BudgetBadge cost={option.monthly_cost} budgetLimit={budgetLimit} />
          </div>
        </div>

        {/* Status Badges */}
        <div className="flex flex-wrap gap-2">
          {!canDeploy && (
            <Badge variant="danger">Cannot Deploy - Quota Exceeded</Badge>
          )}
          {hasCriticalSecurity && (
            <Badge variant="danger">Critical Security Issues</Badge>
          )}
          {hasHighSecurity && !hasCriticalSecurity && (
            <Badge variant="warning">Security Warnings</Badge>
          )}
          {hasSecurityReport && !hasCriticalSecurity && !hasHighSecurity && (
            <Badge variant="success">Security: {pros_cons_json.security_report.score}/100</Badge>
          )}
          {budgetExceeded && (
            <Badge variant="warning">Over Budget</Badge>
          )}
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-800">
          <div className="flex gap-4">
            <button
              onClick={() => setActiveTab('diagram')}
              className={cn(
                'px-4 py-2 text-sm font-medium border-b-2 transition-colors',
                activeTab === 'diagram'
                  ? 'border-blue-500 text-blue-400'
                  : 'border-transparent text-gray-400 hover:text-gray-300'
              )}
            >
              Architecture
            </button>
            <button
              onClick={() => setActiveTab('resources')}
              className={cn(
                'px-4 py-2 text-sm font-medium border-b-2 transition-colors',
                activeTab === 'resources'
                  ? 'border-blue-500 text-blue-400'
                  : 'border-transparent text-gray-400 hover:text-gray-300'
              )}
            >
              Resources ({option.resources_json.resources.length})
            </button>
            <button
              onClick={() => setActiveTab('costs')}
              className={cn(
                'px-4 py-2 text-sm font-medium border-b-2 transition-colors',
                activeTab === 'costs'
                  ? 'border-blue-500 text-blue-400'
                  : 'border-transparent text-gray-400 hover:text-gray-300'
              )}
            >
              Cost Breakdown
            </button>
          </div>
        </div>

        {/* Tab Content */}
        <div className="min-h-[300px]">
          {activeTab === 'diagram' && (
            <MermaidDiagram
              chart={option.architecture_diagram}
              title="Architecture Diagram"
            />
          )}

          {activeTab === 'resources' && (
            <div className="space-y-2">
              {option.resources_json.resources.map((resource, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 rounded-lg bg-gray-800/30 border border-gray-700"
                >
                  <div>
                    <div className="font-medium text-gray-200">{resource.name}</div>
                    <div className="text-sm text-gray-400">{resource.type}</div>
                  </div>
                  <Badge variant="info">{resource.sku}</Badge>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'costs' && (
            <div className="space-y-2">
              {option.cost_estimate_json.estimates.map((estimate, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 rounded-lg bg-gray-800/30 border border-gray-700"
                >
                  <div>
                    <div className="font-medium text-gray-200">{estimate.service}</div>
                    <div className="text-sm text-gray-400">
                      {estimate.sku} • {estimate.region}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-medium text-gray-200">
                      {formatCurrency(estimate.monthly_cost)}/mo
                    </div>
                    <div className="text-xs text-gray-500">
                      {formatCurrency(estimate.unit_price)}/{estimate.unit}
                    </div>
                  </div>
                </div>
              ))}
              <div className="flex items-center justify-between p-4 rounded-lg bg-blue-500/10 border border-blue-500/20 font-semibold">
                <span className="text-gray-200">Total Monthly Cost</span>
                <span className="text-xl text-blue-400">
                  {formatCurrency(option.monthly_cost)}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Pros & Cons */}
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <h4 className="text-sm font-semibold text-green-400 mb-2">✓ Pros</h4>
            <ul className="space-y-1">
              {pros_cons_json.pros.map((pro, index) => (
                <li key={index} className="text-sm text-gray-300 flex items-start gap-2">
                  <span className="text-green-400 mt-1">•</span>
                  <span>{pro}</span>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-red-400 mb-2">✗ Cons</h4>
            <ul className="space-y-1">
              {pros_cons_json.cons.map((con, index) => (
                <li key={index} className="text-sm text-gray-300 flex items-start gap-2">
                  <span className="text-red-400 mt-1">•</span>
                  <span>{con}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Security & Quota */}
        {(hasSecurityReport || hasQuotaReport) && (
          <div className="space-y-4">
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="flex items-center gap-2 text-sm font-medium text-gray-300 hover:text-gray-100 transition-colors"
            >
              {showDetails ? (
                <>
                  <ChevronUp className="h-4 w-4" />
                  Hide Details
                </>
              ) : (
                <>
                  <ChevronDown className="h-4 w-4" />
                  Show Security & Quota Details
                </>
              )}
            </button>

            {showDetails && (
              <div className="space-y-4 pt-4 border-t border-gray-800">
                {hasSecurityReport && (
                  <SecurityScore report={pros_cons_json.security_report} />
                )}
                {hasQuotaReport && (
                  <QuotaStatus report={pros_cons_json.quota_report} />
                )}
              </div>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3 pt-4 border-t border-gray-800">
          <Button
            variant={selected ? 'secondary' : 'primary'}
            onClick={() => onSelect?.(option.option_number)}
            disabled={!canDeploy}
            className="flex-1"
          >
            {selected ? 'Selected' : canDeploy ? 'Select This Option' : 'Cannot Deploy'}
          </Button>
          {onDownloadBicep && (
            <Button
              variant="ghost"
              onClick={() => onDownloadBicep(option.option_number)}
            >
              <FileCode className="h-4 w-4 mr-2" />
              Download Bicep
            </Button>
          )}
        </div>
      </div>
    </Card>
  );
}
