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
