'use client';

import React, { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ProposalOptionCard } from '@/components/proposal/ProposalOptionCard';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Alert } from '@/components/ui/Alert';
import { ArrowLeft, Sparkles } from 'lucide-react';

// This would typically come from an API call
const mockProposal = {
  id: 'proposal-456',
  project_id: 'uuid-123',
  user_request: 'I need a Teams chatbot that can handle customer support queries',
  status: 'ready',
  budget_limit: 300,
  options: [
    {
      option_number: 1,
      name: 'Serverless Chatbot',
      description: 'Azure Functions-based bot with Cosmos DB serverless storage. Scales to zero when not in use. Ideal for small to medium traffic.',
      monthly_cost: 45.00,
      architecture_diagram: `graph TB
    Teams[Microsoft Teams]
    BotService[Azure Bot Service<br/>F0 Free]
    Functions[Azure Functions<br/>Consumption]
    CosmosDB[(Cosmos DB<br/>Serverless)]
    AppInsights[Application Insights]
    KeyVault[Key Vault]
    
    Teams -->|Messages| BotService
    BotService -->|Process| Functions
    Functions -->|Store| CosmosDB
    Functions -->|Secrets| KeyVault
    Functions -->|Logs| AppInsights`,
      resources_json: {
        resources: [
          { type: 'Azure Bot Service', name: 'bot-support-prod', sku: 'F0', region: 'eastus' },
          { type: 'Azure Functions', name: 'func-support-prod', sku: 'Consumption', region: 'eastus' },
          { type: 'Cosmos DB', name: 'cosmos-support-prod', sku: 'Serverless', region: 'eastus' },
          { type: 'Key Vault', name: 'kv-support-prod', sku: 'Standard', region: 'eastus' },
          { type: 'Application Insights', name: 'appi-support-prod', sku: 'Standard', region: 'eastus' }
        ]
      },
      cost_estimate_json: {
        estimates: [
          { service: 'Azure Bot Service', sku: 'F0', region: 'eastus', monthly_cost: 0, unit_price: 0, unit: 'messages' },
          { service: 'Azure Functions', sku: 'Consumption', region: 'eastus', monthly_cost: 15, unit_price: 0.00002, unit: 'execution' },
          { service: 'Cosmos DB', sku: 'Serverless', region: 'eastus', monthly_cost: 20, unit_price: 0.00036, unit: 'RU' },
          { service: 'Key Vault', sku: 'Standard', region: 'eastus', monthly_cost: 3, unit_price: 0.03, unit: 'operation' },
          { service: 'Application Insights', sku: 'Standard', region: 'eastus', monthly_cost: 7, unit_price: 2.30, unit: 'GB' }
        ]
      },
      pros_cons_json: {
        pros: [
          'Lowest cost at $45/month',
          'Auto-scales to zero (no idle costs)',
          'No infrastructure management',
          'Fast deployment'
        ],
        cons: [
          'Cold start latency (~2-3 seconds)',
          'Limited to 10GB storage in Cosmos serverless',
          'May struggle with high concurrent users'
        ],
        security_report: {
          score: 85,
          passed_checks: 6,
          total_checks: 7,
          has_critical: false,
          has_high: false,
          issues: [
            {
              severity: 'medium',
              category: 'Network Security',
              issue: 'Compute resources without Virtual Network isolation',
              recommendation: 'Deploy resources in a Virtual Network for network isolation and security',
              doc_link: 'https://learn.microsoft.com/azure/virtual-network/virtual-networks-overview'
            }
          ]
        },
        quota_report: {
          overall_status: 'ok',
          can_deploy: true,
          warnings: [],
          errors: [],
          checks: [
            {
              resource_type: 'Compute',
              quota_name: 'Total Regional vCPUs',
              current_usage: 10,
              quota_limit: 100,
              requested: 2,
              available: 90,
              after_deployment: 12,
              status: 'ok',
              message: 'Requesting 2 vCPUs'
            }
          ]
        },
        budget_exceeded: false
      }
    },
    {
      option_number: 2,
      name: 'Container-Based Chatbot',
      description: 'Azure Container Apps with SQL Database. Always-on service with persistent connections. Better performance and no cold starts.',
      monthly_cost: 180.00,
      architecture_diagram: `graph TB
    Teams[Microsoft Teams]
    BotService[Azure Bot Service<br/>S1]
    ContainerApp[Container App<br/>1 vCPU, 2GB]
    SQL[(SQL Database<br/>Basic)]
    AppInsights[Application Insights]
    KeyVault[Key Vault]
    
    Teams -->|Messages| BotService
    BotService -->|Process| ContainerApp
    ContainerApp -->|Query| SQL
    ContainerApp -->|Secrets| KeyVault
    ContainerApp -->|Logs| AppInsights`,
      resources_json: {
        resources: [
          { type: 'Azure Bot Service', name: 'bot-support-prod', sku: 'S1', region: 'eastus' },
          { type: 'Container App', name: 'ca-support-prod', sku: '1 vCPU', region: 'eastus' },
          { type: 'SQL Database', name: 'sql-support-prod', sku: 'Basic', region: 'eastus' },
          { type: 'Key Vault', name: 'kv-support-prod', sku: 'Standard', region: 'eastus' },
          { type: 'Application Insights', name: 'appi-support-prod', sku: 'Standard', region: 'eastus' }
        ]
      },
      cost_estimate_json: {
        estimates: [
          { service: 'Azure Bot Service', sku: 'S1', region: 'eastus', monthly_cost: 40, unit_price: 0.50, unit: 'channel' },
          { service: 'Container App', sku: '1 vCPU', region: 'eastus', monthly_cost: 75, unit_price: 0.000024, unit: 'vCPU-second' },
          { service: 'SQL Database', sku: 'Basic', region: 'eastus', monthly_cost: 55, unit_price: 0.075, unit: 'hour' },
          { service: 'Key Vault', sku: 'Standard', region: 'eastus', monthly_cost: 3, unit_price: 0.03, unit: 'operation' },
          { service: 'Application Insights', sku: 'Standard', region: 'eastus', monthly_cost: 7, unit_price: 2.30, unit: 'GB' }
        ]
      },
      pros_cons_json: {
        pros: [
          'No cold starts (always ready)',
          'Better performance under load',
          'Persistent database connections',
          'Auto-scaling support'
        ],
        cons: [
          'Higher cost at $180/month',
          'Requires container management',
          'Basic SQL tier may be slow for complex queries'
        ],
        security_report: {
          score: 71,
          passed_checks: 5,
          total_checks: 7,
          has_critical: false,
          has_high: true,
          issues: [
            {
              severity: 'high',
              category: 'Network Security',
              resource_type: 'Microsoft.Sql/servers',
              resource_name: 'sql-support-prod',
              issue: 'Database server allows public network access',
              recommendation: 'Disable public access and use Private Endpoints or VNet integration',
              doc_link: 'https://learn.microsoft.com/azure/azure-sql/database/private-endpoint-overview'
            },
            {
              severity: 'medium',
              category: 'Network Security',
              issue: 'Compute resources without Network Security Groups',
              recommendation: 'Add Network Security Groups to control inbound/outbound traffic',
              doc_link: 'https://learn.microsoft.com/azure/virtual-network/network-security-groups-overview'
            }
          ]
        },
        quota_report: {
          overall_status: 'ok',
          can_deploy: true,
          warnings: [],
          errors: [],
          checks: [
            {
              resource_type: 'Compute',
              quota_name: 'Total Regional vCPUs',
              current_usage: 10,
              quota_limit: 100,
              requested: 4,
              available: 90,
              after_deployment: 14,
              status: 'ok',
              message: 'Requesting 4 vCPUs'
            }
          ]
        },
        budget_exceeded: false
      }
    }
  ]
};

export default function ProposalPage() {
  const params = useParams();
  const router = useRouter();
  const [selectedOption, setSelectedOption] = useState<number | null>(null);

  const handleSelectOption = (optionNumber: number) => {
    setSelectedOption(optionNumber);
  };

  const handleDownloadBicep = (optionNumber: number) => {
    // TODO: Implement Bicep download
    console.log('Download Bicep for option', optionNumber);
  };

  const handleProceedToDeployment = () => {
    if (selectedOption) {
      router.push(`/projects/${params.id}/proposals/${params.proposalId}/deploy/${selectedOption}`);
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            onClick={() => router.back()}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
          <div>
            <h1 className="text-3xl font-bold text-gray-100">Architecture Proposals</h1>
            <p className="text-gray-400 mt-1">{mockProposal.user_request}</p>
          </div>
        </div>
        <Badge variant="success">
          <Sparkles className="h-3 w-3 mr-1" />
          AI Generated
        </Badge>
      </div>

      {/* Budget Info */}
      {mockProposal.budget_limit && (
        <Alert variant="info">
          <strong>Budget Limit:</strong> ${mockProposal.budget_limit}/month
          {' • '}Options within your budget are highlighted
        </Alert>
      )}

      {/* Options */}
      <div className="space-y-6">
        {mockProposal.options.map((option) => (
          <ProposalOptionCard
            key={option.option_number}
            option={option}
            budgetLimit={mockProposal.budget_limit}
            selected={selectedOption === option.option_number}
            onSelect={handleSelectOption}
            onDownloadBicep={handleDownloadBicep}
          />
        ))}
      </div>

      {/* Action Bar */}
      {selectedOption && (
        <div className="fixed bottom-0 left-0 right-0 bg-gray-900/95 border-t border-gray-800 backdrop-blur-sm">
          <div className="max-w-7xl mx-auto p-4 flex items-center justify-between">
            <div>
              <div className="font-semibold text-gray-200">
                Option {selectedOption} selected
              </div>
              <div className="text-sm text-gray-400">
                Ready to proceed with deployment
              </div>
            </div>
            <Button
              variant="primary"
              onClick={handleProceedToDeployment}
            >
              Proceed to Deployment
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
