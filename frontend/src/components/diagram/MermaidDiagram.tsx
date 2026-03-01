'use client';

import React, { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';
import { cn } from '@/lib/utils';
import { Maximize2, Download } from 'lucide-react';

interface MermaidDiagramProps {
  chart: string;
  className?: string;
  title?: string;
}

// Initialize mermaid once
if (typeof window !== 'undefined') {
  mermaid.initialize({
    startOnLoad: false,
    theme: 'dark',
    themeVariables: {
      primaryColor: '#0078D4',
      primaryTextColor: '#fff',
      primaryBorderColor: '#106EBE',
      lineColor: '#4B5563',
      secondaryColor: '#1F2937',
      tertiaryColor: '#374151',
      background: '#111827',
      mainBkg: '#1F2937',
      secondBkg: '#111827',
      tertiaryBkg: '#374151',
      textColor: '#E5E7EB',
      fontSize: '14px',
      fontFamily: 'Inter, system-ui, sans-serif',
    },
    securityLevel: 'loose',
    flowchart: {
      curve: 'basis',
      padding: 20,
    },
  });
}

export function MermaidDiagram({ chart, className, title }: MermaidDiagramProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [svg, setSvg] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);

  useEffect(() => {
    if (!chart || typeof window === 'undefined') return;

    const renderDiagram = async () => {
      try {
        setError(null);
        const id = `mermaid-${Math.random().toString(36).substr(2, 9)}`;
        const { svg } = await mermaid.render(id, chart);
        setSvg(svg);
      } catch (err) {
        console.error('Mermaid rendering error:', err);
        setError('Failed to render diagram. Invalid syntax.');
      }
    };

    renderDiagram();
  }, [chart]);

  const downloadSvg = () => {
    if (!svg) return;
    
    const blob = new Blob([svg], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `architecture-${Date.now()}.svg`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  if (error) {
    return (
      <div className={cn(
        'rounded-lg border border-red-500/20 bg-red-500/10 p-6 text-center',
        className
      )}>
        <p className="text-red-400 text-sm">{error}</p>
        <details className="mt-2 text-xs text-gray-500">
          <summary className="cursor-pointer hover:text-gray-400">Show diagram source</summary>
          <pre className="mt-2 text-left overflow-auto max-h-40 p-2 bg-gray-900 rounded">
            {chart}
          </pre>
        </details>
      </div>
    );
  }

  const diagramContent = (
    <div className="relative">
      {title && (
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-200">{title}</h3>
          <div className="flex gap-2">
            <button
              onClick={downloadSvg}
              disabled={!svg}
              className="p-2 rounded-lg hover:bg-gray-800 text-gray-400 hover:text-gray-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title="Download SVG"
            >
              <Download className="h-4 w-4" />
            </button>
            {!isFullscreen && (
              <button
                onClick={toggleFullscreen}
                className="p-2 rounded-lg hover:bg-gray-800 text-gray-400 hover:text-gray-200 transition-colors"
                title="Fullscreen"
              >
                <Maximize2 className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>
      )}
      
      <div
        ref={containerRef}
        className={cn(
          'mermaid-diagram rounded-lg bg-gray-900/50 p-6 overflow-auto',
          !svg && 'animate-pulse min-h-[200px]'
        )}
        dangerouslySetInnerHTML={{ __html: svg }}
      />
    </div>
  );

  if (isFullscreen) {
    return (
      <div
        className="fixed inset-0 z-50 bg-gray-950/95 p-8 overflow-auto"
        onClick={toggleFullscreen}
      >
        <div className="max-w-7xl mx-auto" onClick={(e) => e.stopPropagation()}>
          {diagramContent}
          <div className="text-center mt-4">
            <button
              onClick={toggleFullscreen}
              className="px-4 py-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-200 transition-colors"
            >
              Close Fullscreen
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={className}>
      {diagramContent}
    </div>
  );
}
