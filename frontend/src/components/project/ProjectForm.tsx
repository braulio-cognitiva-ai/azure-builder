'use client';

import React from 'react';
import { Input } from '@/components/ui/Input';
import { CurrencyInput } from '@/components/ui/CurrencyInput';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';

interface ProjectFormData {
  name: string;
  description: string;
  budget_limit?: number;
  tags: string[];
}

interface ProjectFormProps {
  initialData?: Partial<ProjectFormData>;
  onSubmit: (data: ProjectFormData) => void;
  onCancel?: () => void;
  submitLabel?: string;
  loading?: boolean;
}

export function ProjectForm({
  initialData,
  onSubmit,
  onCancel,
  submitLabel = 'Create Project',
  loading = false
}: ProjectFormProps) {
  const [formData, setFormData] = React.useState<ProjectFormData>({
    name: initialData?.name || '',
    description: initialData?.description || '',
    budget_limit: initialData?.budget_limit,
    tags: initialData?.tags || []
  });

  const [errors, setErrors] = React.useState<Partial<Record<keyof ProjectFormData, string>>>({});

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validation
    const newErrors: Partial<Record<keyof ProjectFormData, string>> = {};
    
    if (!formData.name.trim()) {
      newErrors.name = 'Project name is required';
    }
    
    if (formData.budget_limit && formData.budget_limit < 0) {
      newErrors.budget_limit = 'Budget must be a positive number';
    }
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <Card>
        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-200 mb-4">Project Details</h3>
            
            <div className="space-y-4">
              <Input
                label="Project Name"
                placeholder="e.g., Customer Support Bot"
                value={formData.name}
                onChange={(e) => {
                  setFormData({ ...formData, name: e.target.value });
                  setErrors({ ...errors, name: undefined });
                }}
                error={errors.name}
                required
              />

              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-300">
                  Description
                  <span className="text-gray-500 ml-1">(Optional)</span>
                </label>
                <textarea
                  placeholder="Describe what you're building..."
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                  className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                />
              </div>
            </div>
          </div>

          <div className="border-t border-gray-800 pt-6">
            <h3 className="text-lg font-semibold text-gray-200 mb-4">Budget Constraints</h3>
            
            <CurrencyInput
              label="Monthly Budget Limit"
              placeholder="300.00"
              value={formData.budget_limit || ''}
              onChange={(e) => {
                const value = e.target.value ? parseFloat(e.target.value) : undefined;
                setFormData({ ...formData, budget_limit: value });
                setErrors({ ...errors, budget_limit: undefined });
              }}
              error={errors.budget_limit}
              helpText="Optional: Set a monthly budget limit. Options exceeding this will be flagged."
            />
          </div>

          <div className="border-t border-gray-800 pt-6">
            <h3 className="text-lg font-semibold text-gray-200 mb-4">
              Tags
              <span className="text-gray-500 ml-1 text-sm font-normal">(Optional)</span>
            </h3>
            
            <Input
              placeholder="Add tags separated by commas (e.g., production, bot, support)"
              value={formData.tags.join(', ')}
              onChange={(e) => {
                const tags = e.target.value
                  .split(',')
                  .map(tag => tag.trim())
                  .filter(tag => tag.length > 0);
                setFormData({ ...formData, tags });
              }}
              helpText="Use tags to organize and filter your projects"
            />
          </div>
        </div>
      </Card>

      <div className="flex gap-3 justify-end">
        {onCancel && (
          <Button
            type="button"
            variant="ghost"
            onClick={onCancel}
            disabled={loading}
          >
            Cancel
          </Button>
        )}
        <Button
          type="submit"
          variant="primary"
          disabled={loading}
        >
          {loading ? 'Saving...' : submitLabel}
        </Button>
      </div>
    </form>
  );
}
