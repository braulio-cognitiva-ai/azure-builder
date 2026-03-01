'use client';

import React, { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { InfrastructureDashboard } from '@/components/infrastructure/InfrastructureDashboard';
import { Button } from '@/components/ui/Button';
import { ArrowLeft } from 'lucide-react';

// Mock data - would come from API
const mockSummary = {
  total_resources: 8,
  active: 7,
  deleted: 1,
  has_drift: 2,
  estimated_monthly_cost: 180.00,
  actual_cost_mtd: 65.00,  // $65 spent so far this month
  by_type: {
    'Microsoft.Web/sites': {
      count: 2,
      estimated_cost: 75.00,
      actual_cost: 28.00
    },
    'Microsoft.Sql/servers/databases': {
      count: 1,
      estimated_cost: 55.00,
      actual_cost: 20.00
    },
    'Microsoft.KeyVault/vaults': {
      count: 1,
      estimated_cost: 3.00,
      actual_cost: 1.20
    },
    'Microsoft.Insights/components': {
      count: 2,
      estimated_cost: 14.00,
      actual_cost: 5.50
    },
    'Microsoft.Storage/storageAccounts': {
      count: 1,
      estimated_cost: 20.00,
      actual_cost: 7.80
    },
    'Microsoft.ContainerRegistry/registries': {
      count: 1,
      estimated_cost: 13.00,
      actual_cost: 4.50
    }
  }
};

const mockResources = [
  {
    id: '1',
    name: 'app-chatbot-prod',
    resource_type: 'Microsoft.Web/sites',
    resource_group: 'rg-chatbot-prod',
    region: 'eastus',
    sku: 'P1V2',
    status: 'active' as const,
    monthly_cost_estimate: 73.00,
    actual_cost_mtd: 27.00,
    has_drift: false,
    deployed_at: '2026-02-15T10:30:00Z',
    last_synced_at: '2026-03-01T17:00:00Z'
  },
  {
    id: '2',
    name: 'sql-chatbot-prod',
    resource_type: 'Microsoft.Sql/servers/databases',
    resource_group: 'rg-chatbot-prod',
    region: 'eastus',
    sku: 'Basic',
    status: 'active' as const,
    monthly_cost_estimate: 55.00,
    actual_cost_mtd: 20.00,
    has_drift: true,  // Configuration changed
    deployed_at: '2026-02-15T10:35:00Z',
    last_synced_at: '2026-03-01T17:00:00Z'
  },
  {
    id: '3',
    name: 'kv-chatbot-prod',
    resource_type: 'Microsoft.KeyVault/vaults',
    resource_group: 'rg-chatbot-prod',
    region: 'eastus',
    sku: 'Standard',
    status: 'active' as const,
    monthly_cost_estimate: 3.00,
    actual_cost_mtd: 1.20,
    has_drift: false,
    deployed_at: '2026-02-15T10:32:00Z',
    last_synced_at: '2026-03-01T17:00:00Z'
  },
  {
    id: '4',
    name: 'appi-chatbot-prod',
    resource_type: 'Microsoft.Insights/components',
    resource_group: 'rg-chatbot-prod',
    region: 'eastus',
    sku: 'Standard',
    status: 'active' as const,
    monthly_cost_estimate: 7.00,
    actual_cost_mtd: 2.80,
    has_drift: false,
    deployed_at: '2026-02-15T10:33:00Z',
    last_synced_at: '2026-03-01T17:00:00Z'
  },
  {
    id: '5',
    name: 'st-chatbot-prod',
    resource_type: 'Microsoft.Storage/storageAccounts',
    resource_group: 'rg-chatbot-prod',
    region: 'eastus',
    sku: 'Standard_LRS',
    status: 'active' as const,
    monthly_cost_estimate: 20.00,
    actual_cost_mtd: 7.80,
    has_drift: true,  // Someone enabled hierarchical namespace
    deployed_at: '2026-02-15T10:34:00Z',
    last_synced_at: '2026-03-01T17:00:00Z'
  },
  {
    id: '6',
    name: 'acr-chatbot-prod',
    resource_type: 'Microsoft.ContainerRegistry/registries',
    resource_group: 'rg-chatbot-prod',
    region: 'eastus',
    sku: 'Basic',
    status: 'active' as const,
    monthly_cost_estimate: 13.00,
    actual_cost_mtd: 4.50,
    has_drift: false,
    deployed_at: '2026-02-16T09:00:00Z',
    last_synced_at: '2026-03-01T17:00:00Z'
  },
  {
    id: '7',
    name: 'app-chatbot-dev',
    resource_type: 'Microsoft.Web/sites',
    resource_group: 'rg-chatbot-dev',
    region: 'eastus',
    sku: 'B1',
    status: 'active' as const,
    monthly_cost_estimate: 13.00,
    actual_cost_mtd: 5.00,
    has_drift: false,
    deployed_at: '2026-02-20T14:00:00Z',
    last_synced_at: '2026-03-01T17:00:00Z'
  },
  {
    id: '8',
    name: 'appi-chatbot-dev',
    resource_type: 'Microsoft.Insights/components',
    resource_group: 'rg-chatbot-dev',
    region: 'eastus',
    sku: 'Standard',
    status: 'deleted' as const,
    monthly_cost_estimate: 7.00,
    actual_cost_mtd: 0.00,
    has_drift: false,
    deployed_at: '2026-02-20T14:05:00Z',
    last_synced_at: '2026-03-01T17:00:00Z'
  }
];

export default function InfrastructurePage() {
  const params = useParams();
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  const handleRefresh = async () => {
    setLoading(true);
    // Simulate API call
    setTimeout(() => {
      setLoading(false);
    }, 2000);
  };

  const handleViewResource = (resourceId: string) => {
    console.log('View resource:', resourceId);
    // Navigate to resource details page
    // router.push(`/projects/${params.id}/resources/${resourceId}`);
  };

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          onClick={() => router.push(`/projects/${params.id}`)}
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Project
        </Button>
      </div>

      {/* Dashboard */}
      <InfrastructureDashboard
        projectId={params.id as string}
        summary={mockSummary}
        resources={mockResources}
        onRefresh={handleRefresh}
        onViewResource={handleViewResource}
        loading={loading}
      />
    </div>
  );
}
