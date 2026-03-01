'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import { Alert } from '@/components/ui/Alert';
import { Button } from '@/components/ui/Button';
import { Lightbulb, Network, Key, Activity } from 'lucide-react';

interface IntegrationSuggestion {
  type: 'integration';
  resource_type: string;
  message: string;
  existing_resources: string[];
}

interface IntegrationSuggestionsProps {
  suggestions: IntegrationSuggestion[];
  className?: string;
  onReuseResource?: (resourceType: string, resourceName: string) => void;
}

const getIcon = (resourceType: string) => {
  switch (resourceType.toLowerCase()) {
    case 'vnet':
    case 'virtual network':
      return Network;
    case 'key vault':
      return Key;
    case 'log analytics':
      return Activity;
    default:
      return Lightbulb;
  }
};

export function IntegrationSuggestions({
  suggestions,
  className,
  onReuseResource
}: IntegrationSuggestionsProps) {
  if (suggestions.length === 0) {
    return null;
  }

  return (
    <div className={cn('space-y-3', className)}>
      <div className="flex items-center gap-2">
        <Lightbulb className="h-5 w-5 text-yellow-400" />
        <h4 className="text-sm font-semibold text-gray-300">Integration Opportunities</h4>
      </div>

      {suggestions.map((suggestion, index) => {
        const Icon = getIcon(suggestion.resource_type);
        
        return (
          <Alert key={index} variant="info">
            <div className="space-y-3">
              <div className="flex items-start gap-3">
                <Icon className="h-5 w-5 text-blue-400 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <div className="font-medium text-gray-200 mb-1">
                    {suggestion.resource_type}
                  </div>
                  <div className="text-sm text-gray-300 mb-2">
                    {suggestion.message}
                  </div>
                  
                  {suggestion.existing_resources.length > 0 && (
                    <div className="space-y-2">
                      <div className="text-xs text-gray-400 font-medium">
                        Existing resources:
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {suggestion.existing_resources.map((resource) => (
                          <div
                            key={resource}
                            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gray-800/50 border border-gray-700"
                          >
                            <span className="text-sm text-gray-300">{resource}</span>
                            {onReuseResource && (
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => onReuseResource(suggestion.resource_type, resource)}
                                className="text-xs px-2 py-1 h-auto"
                              >
                                Reuse
                              </Button>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </Alert>
        );
      })}
    </div>
  );
}
