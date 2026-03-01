import React from 'react';
import { Badge } from '@/components/ui/Badge';
import { formatCurrency } from '@/lib/utils';
import { DollarSign, TrendingUp, TrendingDown } from 'lucide-react';

interface BudgetBadgeProps {
  cost: number;
  budgetLimit?: number;
  className?: string;
}

export function BudgetBadge({ cost, budgetLimit, className }: BudgetBadgeProps) {
  if (!budgetLimit) {
    return (
      <Badge variant="info" className={className}>
        <DollarSign className="h-3 w-3 mr-1" />
        {formatCurrency(cost)}/month
      </Badge>
    );
  }

  const exceeded = cost > budgetLimit;
  const diff = Math.abs(cost - budgetLimit);
  const percentOfBudget = (cost / budgetLimit) * 100;

  if (exceeded) {
    return (
      <Badge variant="danger" className={className}>
        <TrendingUp className="h-3 w-3 mr-1" />
        {formatCurrency(diff)} over budget
      </Badge>
    );
  }

  // Show green badge if within budget
  return (
    <Badge variant="success" className={className}>
      <TrendingDown className="h-3 w-3 mr-1" />
      Within budget ({formatCurrency(diff)} remaining)
    </Badge>
  );
}
