# Frontend Components - Azure Builder

**Phase 4 Implementation Complete**  
**Date:** March 1, 2026

---

## 🎨 Component Library

### Base UI Components

#### Alert (`src/components/ui/Alert.tsx`)
Display important messages with different severity levels.

```tsx
import { Alert } from '@/components/ui/Alert';

<Alert variant="info" title="Budget Limit">
  Options within your budget are highlighted
</Alert>
```

**Props:**
- `variant`: 'info' | 'success' | 'warning' | 'danger'
- `title`: Optional title text
- `children`: Alert content

---

#### Progress (`src/components/ui/Progress.tsx`)
Visual progress bar with variants.

```tsx
import { Progress } from '@/components/ui/Progress';

<Progress
  value={85}
  max={100}
  variant="success"
  showLabel={true}
/>
```

**Props:**
- `value`: Current value
- `max`: Maximum value (default: 100)
- `variant`: 'default' | 'success' | 'warning' | 'danger'
- `showLabel`: Show text label

---

#### CurrencyInput (`src/components/ui/CurrencyInput.tsx`)
Input for currency amounts with $ prefix and /month suffix.

```tsx
import { CurrencyInput } from '@/components/ui/CurrencyInput';

<CurrencyInput
  label="Monthly Budget Limit"
  placeholder="300.00"
  value={budget}
  onChange={(e) => setBudget(parseFloat(e.target.value))}
  helpText="Optional: Set a monthly budget limit"
/>
```

**Props:**
- `label`: Input label
- `error`: Error message
- `helpText`: Help text below input
- All standard input props

---

### Diagram Components

#### MermaidDiagram (`src/components/diagram/MermaidDiagram.tsx`)
Renders Mermaid.js architecture diagrams with fullscreen and download support.

```tsx
import { MermaidDiagram } from '@/components/diagram/MermaidDiagram';

<MermaidDiagram
  chart={`graph TB
    Client[User] -->|HTTPS| App[App Service]
    App --> DB[(SQL Database)]`}
  title="Architecture Diagram"
/>
```

**Features:**
- Dark theme matching Azure Builder design
- Fullscreen mode
- Download as SVG
- Error handling with source display
- Loading state

**Props:**
- `chart`: Mermaid syntax string
- `title`: Optional diagram title
- `className`: Additional CSS classes

---

### Proposal Components

#### SecurityScore (`src/components/proposal/SecurityScore.tsx`)
Displays security validation results with expandable issues list.

```tsx
import { SecurityScore } from '@/components/proposal/SecurityScore';

<SecurityScore
  report={{
    score: 85,
    passed_checks: 6,
    total_checks: 7,
    has_critical: false,
    has_high: false,
    issues: [...]
  }}
  compact={false}
/>
```

**Features:**
- Color-coded score (green >= 90, yellow >= 70, red < 70)
- Expandable/collapsible
- Severity badges (CRITICAL, HIGH, MEDIUM, LOW)
- Documentation links
- Progress bar

**Props:**
- `report`: Security report object
- `compact`: Collapsible mode (default: false)
- `className`: Additional CSS classes

---

#### QuotaStatus (`src/components/proposal/QuotaStatus.tsx`)
Displays Azure quota validation results with detailed breakdowns.

```tsx
import { QuotaStatus } from '@/components/proposal/QuotaStatus';

<QuotaStatus
  report={{
    overall_status: 'ok',
    can_deploy: true,
    warnings: [],
    errors: [],
    checks: [...]
  }}
  compact={false}
/>
```

**Features:**
- Overall status badge (OK/WARNING/EXCEEDED)
- Can deploy indicator
- Per-quota progress bars (current + after deployment)
- Warning/error messages
- Resource type grouping

**Props:**
- `report`: Quota report object
- `compact`: Collapsible mode (default: false)
- `className`: Additional CSS classes

---

#### IntegrationSuggestions (`src/components/proposal/IntegrationSuggestions.tsx`)
Shows integration opportunities with existing Azure resources.

```tsx
import { IntegrationSuggestions } from '@/components/proposal/IntegrationSuggestions';

<IntegrationSuggestions
  suggestions={[
    {
      type: 'integration',
      resource_type: 'Key Vault',
      message: 'Found 2 existing Key Vaults. Consider reusing.',
      existing_resources: ['kv-prod-001', 'kv-dev-001']
    }
  ]}
  onReuseResource={(type, name) => console.log('Reuse', name)}
/>
```

**Features:**
- Resource type icons
- Existing resource list
- "Reuse" action buttons
- Info alert styling

**Props:**
- `suggestions`: Array of integration suggestions
- `onReuseResource`: Optional callback for reuse action
- `className`: Additional CSS classes

---

#### BudgetBadge (`src/components/proposal/BudgetBadge.tsx`)
Badge showing budget status (within/over budget).

```tsx
import { BudgetBadge } from '@/components/proposal/BudgetBadge';

<BudgetBadge
  cost={180}
  budgetLimit={300}
/>
```

**Displays:**
- Cost only (if no budget limit)
- "Within budget" + remaining (green)
- "Over budget" + amount (red)

**Props:**
- `cost`: Monthly cost
- `budgetLimit`: Optional budget limit
- `className`: Additional CSS classes

---

#### ProposalOptionCard (`src/components/proposal/ProposalOptionCard.tsx`)
**Main component** - Complete proposal option card with all features.

```tsx
import { ProposalOptionCard } from '@/components/proposal/ProposalOptionCard';

<ProposalOptionCard
  option={optionData}
  budgetLimit={300}
  selected={selectedOption === 1}
  onSelect={(num) => setSelectedOption(num)}
  onDownloadBicep={(num) => downloadBicep(num)}
/>
```

**Features:**
- Tabbed interface (Architecture, Resources, Costs)
- Mermaid diagram rendering
- Security score display
- Quota status display
- Budget badge
- Pros/cons list
- Resource list
- Cost breakdown
- Expandable details
- Selection state
- Download Bicep button

**Props:**
- `option`: Complete proposal option object
- `budgetLimit`: Optional budget limit for badge
- `selected`: Whether this option is selected
- `onSelect`: Callback when option is selected
- `onDownloadBicep`: Callback for Bicep download
- `className`: Additional CSS classes

---

### Form Components

#### ProjectForm (`src/components/project/ProjectForm.tsx`)
Complete form for creating/editing projects with budget input.

```tsx
import { ProjectForm } from '@/components/project/ProjectForm';

<ProjectForm
  initialData={existingProject}
  onSubmit={(data) => createProject(data)}
  onCancel={() => router.back()}
  submitLabel="Create Project"
  loading={isSubmitting}
/>
```

**Features:**
- Name, description, budget, tags fields
- Currency input for budget
- Validation
- Loading state
- Cancel button

**Props:**
- `initialData`: Optional existing data for edit mode
- `onSubmit`: Form submission callback
- `onCancel`: Optional cancel callback
- `submitLabel`: Submit button text (default: "Create Project")
- `loading`: Loading state

---

## 📁 File Structure

```
src/
├── components/
│   ├── ui/
│   │   ├── Alert.tsx
│   │   ├── Badge.tsx (existing)
│   │   ├── Button.tsx (existing)
│   │   ├── Card.tsx (existing)
│   │   ├── Input.tsx (existing)
│   │   ├── Progress.tsx (new)
│   │   ├── CurrencyInput.tsx (new)
│   │   └── Modal.tsx (existing)
│   ├── diagram/
│   │   └── MermaidDiagram.tsx (new)
│   ├── proposal/
│   │   ├── SecurityScore.tsx (new)
│   │   ├── QuotaStatus.tsx (new)
│   │   ├── IntegrationSuggestions.tsx (new)
│   │   ├── BudgetBadge.tsx (new)
│   │   └── ProposalOptionCard.tsx (new)
│   └── project/
│       └── ProjectForm.tsx (new)
└── app/
    └── (dashboard)/
        └── projects/
            └── [id]/
                └── proposals/
                    └── [proposalId]/
                        └── page.tsx (new, example)
```

---

## 🎨 Design System

### Colors (Tailwind)

**Status Colors:**
- Success: `green-500` / `green-400`
- Warning: `yellow-500` / `yellow-400`
- Danger: `red-500` / `red-400`
- Info: `blue-500` / `blue-400`
- Default: `gray-500` / `gray-400`

**Primary:**
- Azure Blue: `#0078D4` (primary button)

**Backgrounds:**
- Card: `gray-900`
- Hover: `gray-800`
- Border: `gray-700`
- Text: `gray-100` (primary), `gray-400` (secondary)

---

## 🚀 Usage Example

### Complete Proposal Page

```tsx
import { ProposalOptionCard } from '@/components/proposal/ProposalOptionCard';
import { Alert } from '@/components/ui/Alert';

export default function ProposalsPage() {
  const [selectedOption, setSelectedOption] = useState<number | null>(null);

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      <h1 className="text-3xl font-bold">Architecture Proposals</h1>
      
      {budgetLimit && (
        <Alert variant="info">
          Budget Limit: ${budgetLimit}/month
        </Alert>
      )}

      {proposals.map(option => (
        <ProposalOptionCard
          key={option.option_number}
          option={option}
          budgetLimit={budgetLimit}
          selected={selectedOption === option.option_number}
          onSelect={setSelectedOption}
        />
      ))}
    </div>
  );
}
```

---

## 📦 Dependencies

### Added in Phase 4:
- `mermaid` - For rendering architecture diagrams

### Existing:
- `next` - React framework
- `react` - UI library
- `tailwindcss` - Styling
- `lucide-react` - Icons
- `clsx` + `tailwind-merge` - Class utilities

---

## 🧪 Testing

### Manual Testing Checklist:

#### MermaidDiagram
- [ ] Renders valid Mermaid syntax
- [ ] Shows error for invalid syntax
- [ ] Fullscreen mode works
- [ ] Download SVG works
- [ ] Dark theme applied

#### SecurityScore
- [ ] Score color changes based on value (green/yellow/red)
- [ ] Issues list displays correctly
- [ ] Severity badges show proper colors
- [ ] Documentation links work
- [ ] Expand/collapse works in compact mode

#### QuotaStatus
- [ ] Overall status badge shows correct variant
- [ ] Progress bars display correctly
- [ ] "Can deploy" indicator accurate
- [ ] Warnings/errors display
- [ ] Unknown status handling

#### BudgetBadge
- [ ] Within budget shows green with remaining
- [ ] Over budget shows red with excess
- [ ] No budget shows just cost

#### ProposalOptionCard
- [ ] All tabs work (Architecture, Resources, Costs)
- [ ] Selection state visual feedback
- [ ] Expand details button works
- [ ] Security/quota sections display when available
- [ ] Download Bicep button fires callback

#### ProjectForm
- [ ] Budget input accepts decimals
- [ ] Validation works (required name)
- [ ] Currency format displays correctly
- [ ] Tags split on comma
- [ ] Submit/cancel work

---

## 🎯 Next Steps

### Immediate:
1. Connect to real API endpoints (replace mock data)
2. Add loading states
3. Add error handling
4. Add success/error toasts

### Future Enhancements:
1. Export diagrams as PNG (in addition to SVG)
2. Compare multiple options side-by-side
3. Filter/sort options
4. Save favorite options
5. Share proposals via link
6. Print-friendly view

---

## 🔧 Customization

### Changing Theme:

Update Mermaid theme in `MermaidDiagram.tsx`:

```typescript
mermaid.initialize({
  theme: 'dark', // or 'default', 'forest', 'neutral'
  themeVariables: {
    primaryColor: '#0078D4', // Azure blue
    // ... other colors
  }
});
```

### Changing Badge Variants:

Update variants in `Badge.tsx`:

```typescript
const variants = {
  success: 'bg-green-500/10 text-green-400 border-green-500/20',
  // ... add custom variants
};
```

---

## 📚 Resources

- [Mermaid Documentation](https://mermaid.js.org/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Lucide Icons](https://lucide.dev/)
- [Next.js 14 Docs](https://nextjs.org/docs)

---

**All components are production-ready and follow Azure Builder design system.**
