/**
 * TypeScript type definitions
 */

export interface User {
  id: string;
  email: string;
  name?: string;
  role: 'owner' | 'admin' | 'operator' | 'viewer';
  tenant_id: string;
  created_at: string;
}

export interface Project {
  id: string;
  name: string;
  description?: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  tags: string[];
}

export interface Conversation {
  id: string;
  project_id: string;
  title?: string;
  created_at: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string;
  proposal_id?: string;
  deployment_id?: string;
}

export interface Command {
  command: string;
  description: string;
  risk_level: 'low' | 'medium' | 'high';
}

export interface Execution {
  id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  started_at?: string;
  completed_at?: string;
  error?: string;
}

export interface Template {
  id: string;
  name: string;
  description: string;
  category: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  estimated_cost_monthly?: string;
}

export interface ResourceDefinition {
  name: string;
  type: string;
  sku: string;
  region?: string;
  monthly_cost: number;
}

export interface ProsCons {
  pros: string[];
  cons: string[];
}

export interface CostEstimate {
  monthly_total: number;
  currency: string;
  breakdown: { resource: string; cost: number }[];
}

export interface ProposalOption {
  option_number: number;
  name: string;
  description: string;
  monthly_cost: number;
  resources: ResourceDefinition[];
  pros_cons: ProsCons;
}

export interface Proposal {
  id: string;
  project_id: string;
  user_request: string;
  status: 'generating' | 'options_ready' | 'selected' | 'deploying' | 'deployed' | 'failed';
  options: ProposalOption[];
  selected_option?: number;
  created_at: string;
}

export interface DeploymentResource {
  name: string;
  type: string;
  status: 'pending' | 'creating' | 'created' | 'failed';
}

export interface ExecutionLog {
  timestamp: string;
  level: 'info' | 'warning' | 'error';
  message: string;
}

export interface Deployment {
  id: string;
  proposal_id: string;
  status: 'pending_review' | 'approved' | 'executing' | 'completed' | 'failed' | 'rolled_back';
  bicep_template?: string;
  resources: DeploymentResource[];
  total_cost: number;
  created_at: string;
  completed_at?: string;
}

export interface AzureConnection {
  id: string;
  subscription_id: string;
  subscription_name: string;
  tenant_id: string;
  status: 'connected' | 'disconnected' | 'error';
  connected_at: string;
}

export interface AuditLog {
  id: string;
  timestamp: string;
  user_id: string;
  user_email: string;
  action: string;
  entity_type: string;
  entity_id: string;
  details: string;
}
