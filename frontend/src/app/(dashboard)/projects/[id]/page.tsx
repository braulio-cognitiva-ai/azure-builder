'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/Card';
import {
  Send, Bot, User, ArrowLeft, Check, ThumbsUp, ThumbsDown,
  Server, Database, Globe, Shield, Cpu, HardDrive, Loader2,
  CheckCircle2, XCircle, Clock, Play, RotateCcw, FileCode
} from 'lucide-react';
import { api } from '@/lib/api';
import { Project, Proposal, ProposalOption, Deployment, DeploymentResource } from '@/types';
import { formatCurrency, formatDateTime } from '@/lib/utils';
import dynamic from 'next/dynamic';

const MonacoEditor = dynamic(() => import('@monaco-editor/react').then(m => m.default), { ssr: false });

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  proposal?: Proposal;
  deployment?: Deployment;
}

const resourceIcons: Record<string, React.ElementType> = {
  'Microsoft.Web': Globe,
  'Microsoft.Sql': Database,
  'Microsoft.Compute': Cpu,
  'Microsoft.Storage': HardDrive,
  'Microsoft.Network': Shield,
};

function getResourceIcon(type: string) {
  for (const [key, Icon] of Object.entries(resourceIcons)) {
    if (type.startsWith(key)) return Icon;
  }
  return Server;
}

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [project, setProject] = useState<Project | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [activeDeployment, setActiveDeployment] = useState<Deployment | null>(null);
  const [showBicep, setShowBicep] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadProject();
  }, [id]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadProject = async () => {
    try {
      const data = await api.getProject(id);
      setProject(data);
    } catch {
      setProject({ id, name: 'Project', description: '', created_by: '1', created_at: new Date().toISOString(), updated_at: new Date().toISOString(), tags: [] });
    }
    // Add welcome message
    setMessages([{
      id: 'welcome',
      role: 'assistant',
      content: 'Hi! I\'m your Azure infrastructure assistant. Describe what you want to build and I\'ll generate architecture options for you.\n\nFor example: "I need a web app with a database and caching layer" or "Set up a microservices architecture with API gateway"',
      timestamp: new Date().toISOString(),
    }]);
  };

  const handleSend = async () => {
    if (!input.trim() || sending) return;
    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setSending(true);

    try {
      const proposal = await api.createProposal(id, input);
      // Fetch options
      const options = await api.getProposalOptions(proposal.id);
      const fullProposal: Proposal = { ...proposal, options: options.options || options };
      const assistantMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `I've analyzed your request and generated ${fullProposal.options.length} architecture options. Review them below and select the one that best fits your needs.`,
        timestamp: new Date().toISOString(),
        proposal: fullProposal,
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch {
      // Demo: generate mock proposal
      const mockProposal = generateMockProposal(input);
      const assistantMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `I've analyzed your request and generated ${mockProposal.options.length} architecture options. Review them below and select the one that best fits your needs.`,
        timestamp: new Date().toISOString(),
        proposal: mockProposal,
      };
      setMessages(prev => [...prev, assistantMsg]);
    }
    setSending(false);
  };

  const handleSelectOption = async (proposal: Proposal, optionNumber: number) => {
    const selectedOption = proposal.options.find(o => o.option_number === optionNumber);
    if (!selectedOption) return;

    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      role: 'assistant',
      content: `Great choice! You selected **${selectedOption.name}**. I'm preparing the deployment review with the Bicep template and resource breakdown.`,
      timestamp: new Date().toISOString(),
    }]);

    try {
      await api.selectProposalOption(proposal.id, optionNumber);
      const deployment = await api.createDeployment(proposal.id);
      const review = await api.getDeploymentReview(deployment.id);
      setActiveDeployment({ ...deployment, ...review });
    } catch {
      // Demo mock
      const mockDeployment: Deployment = {
        id: 'dep-' + Date.now(),
        proposal_id: proposal.id,
        status: 'pending_review',
        bicep_template: generateMockBicep(selectedOption),
        resources: selectedOption.resources.map(r => ({ name: r.name, type: r.type, status: 'pending' as const })),
        total_cost: selectedOption.monthly_cost,
        created_at: new Date().toISOString(),
      };
      setActiveDeployment(mockDeployment);
    }

    setMessages(prev => [...prev, {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: 'Deployment review is ready. Check the Bicep template and resource breakdown below, then approve to deploy.',
      timestamp: new Date().toISOString(),
      deployment: activeDeployment || undefined,
    }]);
  };

  const handleApprove = async () => {
    if (!activeDeployment) return;
    setActiveDeployment(prev => prev ? { ...prev, status: 'executing' } : null);

    try {
      await api.approveDeployment(activeDeployment.id);
      await api.executeDeployment(activeDeployment.id);
    } catch {
      // Demo: simulate deployment
    }

    // Simulate progress
    const resources = activeDeployment.resources;
    for (let i = 0; i < resources.length; i++) {
      await new Promise(r => setTimeout(r, 1000));
      setActiveDeployment(prev => {
        if (!prev) return null;
        const updated = [...prev.resources];
        updated[i] = { ...updated[i], status: 'creating' };
        return { ...prev, resources: updated };
      });
      await new Promise(r => setTimeout(r, 1500));
      setActiveDeployment(prev => {
        if (!prev) return null;
        const updated = [...prev.resources];
        updated[i] = { ...updated[i], status: 'created' };
        return { ...prev, resources: updated };
      });
    }

    setActiveDeployment(prev => prev ? { ...prev, status: 'completed', completed_at: new Date().toISOString() } : null);
    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      role: 'assistant',
      content: '🎉 Deployment completed successfully! All resources have been provisioned. You can continue to modify or extend this project.',
      timestamp: new Date().toISOString(),
    }]);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      {/* Header */}
      <div className="flex items-center gap-4 mb-4 flex-shrink-0">
        <button onClick={() => router.push('/projects')} className="text-gray-400 hover:text-gray-100 transition-smooth">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-xl font-bold text-gray-100">{project?.name || 'Loading...'}</h1>
          {project?.description && <p className="text-sm text-gray-400">{project.description}</p>}
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto space-y-4 pb-4 pr-2">
        {messages.map(msg => (
          <div key={msg.id} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            {msg.role === 'assistant' && (
              <div className="w-8 h-8 bg-[#0078D4] rounded-full flex items-center justify-center flex-shrink-0">
                <Bot className="w-4 h-4 text-white" />
              </div>
            )}
            <div className={`max-w-[80%] space-y-3 ${msg.role === 'user' ? 'items-end' : ''}`}>
              <div className={`rounded-lg px-4 py-3 ${
                msg.role === 'user'
                  ? 'bg-[#0078D4] text-white'
                  : 'bg-gray-900 border border-gray-800 text-gray-200'
              }`}>
                <p className="whitespace-pre-wrap">{msg.content}</p>
              </div>

              {/* Proposal Options */}
              {msg.proposal && msg.proposal.options && (
                <div className="grid gap-4 mt-3">
                  {msg.proposal.options.map(option => (
                    <ProposalOptionCard
                      key={option.option_number}
                      option={option}
                      onSelect={() => handleSelectOption(msg.proposal!, option.option_number)}
                    />
                  ))}
                </div>
              )}
            </div>
            {msg.role === 'user' && (
              <div className="w-8 h-8 bg-gray-700 rounded-full flex items-center justify-center flex-shrink-0">
                <User className="w-4 h-4 text-gray-300" />
              </div>
            )}
          </div>
        ))}

        {/* Deployment Review Panel */}
        {activeDeployment && (
          <DeploymentPanel
            deployment={activeDeployment}
            onApprove={handleApprove}
            showBicep={showBicep}
            onToggleBicep={() => setShowBicep(!showBicep)}
          />
        )}

        {sending && (
          <div className="flex gap-3">
            <div className="w-8 h-8 bg-[#0078D4] rounded-full flex items-center justify-center flex-shrink-0">
              <Bot className="w-4 h-4 text-white" />
            </div>
            <div className="bg-gray-900 border border-gray-800 rounded-lg px-4 py-3">
              <div className="flex items-center gap-2 text-gray-400">
                <Loader2 className="w-4 h-4 animate-spin" />
                Analyzing your request...
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="flex-shrink-0 border-t border-gray-800 pt-4">
        <div className="flex gap-3">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Describe what you want to build..."
            rows={1}
            className="flex-1 px-4 py-3 bg-gray-900 border border-gray-800 rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#0078D4] resize-none"
          />
          <Button onClick={handleSend} disabled={!input.trim() || sending} className="self-end">
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}

function ProposalOptionCard({ option, onSelect }: { option: ProposalOption; onSelect: () => void }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-5 hover:border-[#0078D4]/50 transition-smooth">
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-2">
            <Badge variant="info">Option {option.option_number}</Badge>
            <h3 className="text-lg font-semibold text-gray-100">{option.name}</h3>
          </div>
          <p className="text-sm text-gray-400 mt-1">{option.description}</p>
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold text-[#0078D4]">{formatCurrency(option.monthly_cost)}</p>
          <p className="text-xs text-gray-500">/month</p>
        </div>
      </div>

      {/* Resources */}
      <div className="mb-4">
        <p className="text-sm font-medium text-gray-300 mb-2">Resources</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {option.resources.map((r, i) => {
            const Icon = getResourceIcon(r.type);
            return (
              <div key={i} className="flex items-center gap-2 text-sm bg-gray-800/50 rounded px-3 py-2">
                <Icon className="w-4 h-4 text-[#0078D4]" />
                <span className="text-gray-200">{r.name}</span>
                <span className="text-gray-500 text-xs ml-auto">{r.sku}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Pros/Cons */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <p className="text-sm font-medium text-green-400 mb-1 flex items-center gap-1">
            <ThumbsUp className="w-3 h-3" /> Pros
          </p>
          <ul className="text-xs text-gray-400 space-y-1">
            {option.pros_cons.pros.map((p, i) => (
              <li key={i} className="flex items-start gap-1">
                <Check className="w-3 h-3 text-green-400 mt-0.5 flex-shrink-0" /> {p}
              </li>
            ))}
          </ul>
        </div>
        <div>
          <p className="text-sm font-medium text-yellow-400 mb-1 flex items-center gap-1">
            <ThumbsDown className="w-3 h-3" /> Cons
          </p>
          <ul className="text-xs text-gray-400 space-y-1">
            {option.pros_cons.cons.map((c, i) => (
              <li key={i} className="flex items-start gap-1">
                <XCircle className="w-3 h-3 text-yellow-400 mt-0.5 flex-shrink-0" /> {c}
              </li>
            ))}
          </ul>
        </div>
      </div>

      <Button onClick={onSelect} className="w-full">
        <Check className="w-4 h-4 mr-2" /> Select This Option
      </Button>
    </div>
  );
}

function DeploymentPanel({ deployment, onApprove, showBicep, onToggleBicep }: {
  deployment: Deployment;
  onApprove: () => void;
  showBicep: boolean;
  onToggleBicep: () => void;
}) {
  const statusColors: Record<string, string> = {
    pending_review: 'text-yellow-400',
    approved: 'text-blue-400',
    executing: 'text-blue-400',
    completed: 'text-green-400',
    failed: 'text-red-400',
    rolled_back: 'text-orange-400',
  };

  const statusLabels: Record<string, string> = {
    pending_review: 'Pending Review',
    approved: 'Approved',
    executing: 'Deploying...',
    completed: 'Completed',
    failed: 'Failed',
    rolled_back: 'Rolled Back',
  };

  const resourceStatusIcon = (status: string) => {
    switch (status) {
      case 'created': return <CheckCircle2 className="w-4 h-4 text-green-400" />;
      case 'creating': return <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />;
      case 'failed': return <XCircle className="w-4 h-4 text-red-400" />;
      default: return <Clock className="w-4 h-4 text-gray-500" />;
    }
  };

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-5 ml-11 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-100">Deployment Review</h3>
        <span className={`text-sm font-medium ${statusColors[deployment.status]}`}>
          {statusLabels[deployment.status]}
        </span>
      </div>

      {/* Cost */}
      <div className="bg-gray-800/50 rounded-lg p-4 flex items-center justify-between">
        <span className="text-gray-400">Estimated Monthly Cost</span>
        <span className="text-2xl font-bold text-[#0078D4]">{formatCurrency(deployment.total_cost)}</span>
      </div>

      {/* Resources */}
      <div>
        <p className="text-sm font-medium text-gray-300 mb-2">Resources</p>
        <div className="space-y-2">
          {deployment.resources.map((r, i) => (
            <div key={i} className="flex items-center justify-between bg-gray-800/50 rounded px-3 py-2">
              <div className="flex items-center gap-2">
                {resourceStatusIcon(r.status)}
                <span className="text-sm text-gray-200">{r.name}</span>
              </div>
              <span className="text-xs text-gray-500">{r.type}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Bicep Template */}
      {deployment.bicep_template && (
        <div>
          <button
            onClick={onToggleBicep}
            className="flex items-center gap-2 text-sm text-[#0078D4] hover:text-[#106EBE] transition-smooth mb-2"
          >
            <FileCode className="w-4 h-4" />
            {showBicep ? 'Hide' : 'View'} Bicep Template
          </button>
          {showBicep && (
            <div className="h-64 rounded-lg overflow-hidden border border-gray-800">
              <MonacoEditor
                height="100%"
                language="plaintext"
                theme="vs-dark"
                value={deployment.bicep_template}
                options={{ readOnly: true, minimap: { enabled: false }, fontSize: 12, scrollBeyondLastLine: false }}
              />
            </div>
          )}
        </div>
      )}

      {/* Actions */}
      {deployment.status === 'pending_review' && (
        <div className="flex gap-3">
          <Button onClick={onApprove} className="flex-1">
            <Play className="w-4 h-4 mr-2" /> Approve & Deploy
          </Button>
        </div>
      )}

      {deployment.status === 'completed' && (
        <div className="text-center py-2">
          <CheckCircle2 className="w-8 h-8 text-green-400 mx-auto mb-2" />
          <p className="text-green-400 font-medium">All resources deployed successfully</p>
        </div>
      )}
    </div>
  );
}

// Demo helpers
function generateMockProposal(request: string): Proposal {
  return {
    id: 'prop-' + Date.now(),
    project_id: '',
    user_request: request,
    status: 'options_ready',
    created_at: new Date().toISOString(),
    options: [
      {
        option_number: 1,
        name: 'Standard Architecture',
        description: 'A balanced setup with managed services for reliability and ease of management.',
        monthly_cost: 285,
        resources: [
          { name: 'App Service Plan', type: 'Microsoft.Web/serverfarms', sku: 'P1v3', monthly_cost: 138 },
          { name: 'SQL Database', type: 'Microsoft.Sql/servers', sku: 'S2', monthly_cost: 75 },
          { name: 'Redis Cache', type: 'Microsoft.Cache/Redis', sku: 'C1', monthly_cost: 42 },
          { name: 'Storage Account', type: 'Microsoft.Storage/storageAccounts', sku: 'LRS', monthly_cost: 30 },
        ],
        pros_cons: {
          pros: ['Easy to manage', 'Built-in scaling', 'High availability SLA'],
          cons: ['Higher base cost', 'Less customizable'],
        },
      },
      {
        option_number: 2,
        name: 'Cost-Optimized',
        description: 'Minimizes costs using containers and shared resources.',
        monthly_cost: 142,
        resources: [
          { name: 'Container App', type: 'Microsoft.App/containerApps', sku: 'Consumption', monthly_cost: 45 },
          { name: 'SQL Database', type: 'Microsoft.Sql/servers', sku: 'Basic', monthly_cost: 5 },
          { name: 'Storage Account', type: 'Microsoft.Storage/storageAccounts', sku: 'LRS', monthly_cost: 22 },
        ],
        pros_cons: {
          pros: ['Lowest cost', 'Pay-per-use scaling', 'Serverless containers'],
          cons: ['Cold start latency', 'Less predictable costs at scale'],
        },
      },
      {
        option_number: 3,
        name: 'Enterprise Grade',
        description: 'Full enterprise setup with premium features, VNET integration, and advanced security.',
        monthly_cost: 720,
        resources: [
          { name: 'App Service Plan', type: 'Microsoft.Web/serverfarms', sku: 'P2v3', monthly_cost: 276 },
          { name: 'SQL Database', type: 'Microsoft.Sql/servers', sku: 'P1', monthly_cost: 465 },
          { name: 'Redis Cache', type: 'Microsoft.Cache/Redis', sku: 'P1', monthly_cost: 228 },
          { name: 'Application Gateway', type: 'Microsoft.Network/applicationGateways', sku: 'WAF_v2', monthly_cost: 246 },
          { name: 'Key Vault', type: 'Microsoft.KeyVault/vaults', sku: 'Standard', monthly_cost: 5 },
        ],
        pros_cons: {
          pros: ['Enterprise SLA 99.99%', 'WAF protection', 'VNET integration', 'Premium performance'],
          cons: ['Highest cost', 'More complex management'],
        },
      },
    ],
  };
}

function generateMockBicep(option: ProposalOption): string {
  const resources = option.resources.map(r => `
resource ${r.name.replace(/\s+/g, '_').toLowerCase()} '${r.type}@2023-01-01' = {
  name: '${r.name.replace(/\s+/g, '-').toLowerCase()}'
  location: resourceGroup().location
  sku: {
    name: '${r.sku}'
  }
}`).join('\n');

  return `// Generated Bicep template for: ${option.name}
// Estimated monthly cost: ${formatCurrency(option.monthly_cost)}

param location string = resourceGroup().location
${resources}
`;
}
