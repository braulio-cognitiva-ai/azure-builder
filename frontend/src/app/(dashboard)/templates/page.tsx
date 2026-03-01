'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Tabs } from '@/components/ui/Tabs';
import { LayoutGrid, Globe, Server, Database, Brain, Layers } from 'lucide-react';

const templates = [
  { id: '1', name: 'Static Web App + CDN', description: 'Azure Static Web Apps with global CDN and custom domain. Perfect for SPAs and JAMstack sites.', category: 'web-apps', difficulty: 'beginner' as const, cost: '$5–$25/mo', resources: 3 },
  { id: '2', name: 'Full-Stack Web App', description: 'App Service + SQL Database + Redis Cache with staging slots and auto-scaling.', category: 'web-apps', difficulty: 'intermediate' as const, cost: '$50–$200/mo', resources: 5 },
  { id: '3', name: 'Container Microservices', description: 'AKS cluster with Ingress controller, service mesh, and container registry.', category: 'microservices', difficulty: 'advanced' as const, cost: '$150–$500/mo', resources: 7 },
  { id: '4', name: 'Serverless API', description: 'Azure Functions + API Management + Cosmos DB for event-driven microservices.', category: 'microservices', difficulty: 'intermediate' as const, cost: '$30–$150/mo', resources: 4 },
  { id: '5', name: 'ETL Pipeline', description: 'Data Factory + Synapse Analytics + Data Lake for batch data processing.', category: 'data-pipelines', difficulty: 'intermediate' as const, cost: '$100–$400/mo', resources: 5 },
  { id: '6', name: 'Real-Time Streaming', description: 'Event Hubs + Stream Analytics + Power BI for real-time data ingestion and visualization.', category: 'data-pipelines', difficulty: 'advanced' as const, cost: '$200–$600/mo', resources: 6 },
  { id: '7', name: 'ML Training Pipeline', description: 'Azure ML Workspace + Compute Clusters + Blob Storage for model training.', category: 'ai-ml', difficulty: 'advanced' as const, cost: '$100–$1000/mo', resources: 5 },
  { id: '8', name: 'OpenAI Chatbot', description: 'Azure OpenAI + App Service + Cosmos DB for a production-ready AI chatbot.', category: 'ai-ml', difficulty: 'beginner' as const, cost: '$30–$200/mo', resources: 4 },
];

const difficultyVariant = { beginner: 'success' as const, intermediate: 'warning' as const, advanced: 'danger' as const };

const categoryIcons: Record<string, React.ReactNode> = {
  'all': <LayoutGrid className="w-4 h-4" />,
  'web-apps': <Globe className="w-4 h-4" />,
  'microservices': <Server className="w-4 h-4" />,
  'data-pipelines': <Database className="w-4 h-4" />,
  'ai-ml': <Brain className="w-4 h-4" />,
};

export default function TemplatesPage() {
  const router = useRouter();
  const [category, setCategory] = useState('all');

  const filtered = category === 'all' ? templates : templates.filter(t => t.category === category);

  const categories = [
    { id: 'all', label: 'All Templates' },
    { id: 'web-apps', label: 'Web Apps' },
    { id: 'microservices', label: 'Microservices' },
    { id: 'data-pipelines', label: 'Data Pipelines' },
    { id: 'ai-ml', label: 'AI & ML' },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-100">Templates</h1>
        <p className="text-gray-400 mt-1">Start with a proven architecture and customize it to your needs.</p>
      </div>

      {/* Category Tabs */}
      <div className="border-b border-gray-800">
        <nav className="flex space-x-4">
          {categories.map(cat => (
            <button
              key={cat.id}
              onClick={() => setCategory(cat.id)}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-all ${
                category === cat.id
                  ? 'border-[#0078D4] text-[#0078D4]'
                  : 'border-transparent text-gray-400 hover:text-gray-200 hover:border-gray-700'
              }`}
            >
              {categoryIcons[cat.id]}
              {cat.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Template Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {filtered.map(template => (
          <Card key={template.id} className="flex flex-col justify-between hover:border-gray-700 transition-all cursor-pointer group">
            <div>
              <div className="flex items-center justify-between mb-3">
                <Badge variant={difficultyVariant[template.difficulty]}>{template.difficulty}</Badge>
                <span className="text-xs text-gray-500 flex items-center gap-1">
                  <Layers className="w-3 h-3" /> {template.resources} resources
                </span>
              </div>
              <h3 className="text-lg font-semibold text-gray-100 mb-2 group-hover:text-[#0078D4] transition-colors">{template.name}</h3>
              <p className="text-sm text-gray-400 mb-4">{template.description}</p>
            </div>
            <div className="flex items-center justify-between mt-auto pt-4 border-t border-gray-800">
              <span className="text-sm text-gray-500">{template.cost}</span>
              <Button variant="secondary" size="sm" onClick={() => router.push('/projects')}>
                Use Template
              </Button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
