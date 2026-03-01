'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { Plus, Search, FolderKanban, Calendar, Tag } from 'lucide-react';
import { api } from '@/lib/api';
import { Project } from '@/types';
import { formatDate } from '@/lib/utils';

export default function ProjectsPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showNew, setShowNew] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      const data = await api.getProjects();
      setProjects(Array.isArray(data) ? data : data.projects || []);
    } catch {
      // Demo fallback
      setProjects([
        { id: '1', name: 'Production Web App', description: 'Main production environment with App Service, SQL Database, and Redis Cache', created_by: '1', created_at: '2026-02-20T10:00:00Z', updated_at: '2026-02-25T14:30:00Z', tags: ['production', 'web'] },
        { id: '2', name: 'ML Pipeline', description: 'Machine learning data pipeline with Azure ML and Databricks', created_by: '1', created_at: '2026-02-18T09:00:00Z', updated_at: '2026-02-24T11:00:00Z', tags: ['ml', 'data'] },
        { id: '3', name: 'Staging Environment', description: 'Staging mirror of production for testing', created_by: '1', created_at: '2026-02-15T08:00:00Z', updated_at: '2026-02-23T16:00:00Z', tags: ['staging'] },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!newName.trim()) return;
    setCreating(true);
    setError('');
    try {
      const project = await api.createProject({ name: newName, description: newDesc });
      router.push(`/projects/${project.id}`);
    } catch {
      // Demo: create locally
      const id = Date.now().toString();
      router.push(`/projects/${id}`);
    }
    setCreating(false);
    setShowNew(false);
  };

  const filtered = projects.filter(p =>
    p.name.toLowerCase().includes(search.toLowerCase()) ||
    (p.description || '').toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Projects</h1>
          <p className="text-gray-400 mt-1">Manage your Azure infrastructure projects</p>
        </div>
        <Button onClick={() => setShowNew(true)}>
          <Plus className="w-4 h-4 mr-2" /> New Project
        </Button>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
        <input
          type="text"
          placeholder="Search projects..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-10 pr-4 py-2 bg-gray-900 border border-gray-800 rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#0078D4]"
        />
      </div>

      {/* Project Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map(i => (
            <div key={i} className="glass-card animate-pulse">
              <div className="h-4 bg-gray-800 rounded w-3/4 mb-3" />
              <div className="h-3 bg-gray-800 rounded w-full mb-2" />
              <div className="h-3 bg-gray-800 rounded w-2/3" />
            </div>
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <Card>
          <div className="text-center py-12">
            <FolderKanban className="w-12 h-12 text-gray-600 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-300">No projects found</h3>
            <p className="text-gray-500 mt-1">Create your first project to get started</p>
            <Button className="mt-4" onClick={() => setShowNew(true)}>
              <Plus className="w-4 h-4 mr-2" /> Create Project
            </Button>
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filtered.map(project => (
            <div
              key={project.id}
              onClick={() => router.push(`/projects/${project.id}`)}
              className="glass-card cursor-pointer hover:border-[#0078D4]/50 transition-smooth group"
            >
              <div className="flex items-start justify-between mb-3">
                <h3 className="text-lg font-semibold text-gray-100 group-hover:text-[#0078D4] transition-smooth">
                  {project.name}
                </h3>
                <FolderKanban className="w-5 h-5 text-gray-600" />
              </div>
              <p className="text-sm text-gray-400 mb-4 line-clamp-2">{project.description}</p>
              <div className="flex items-center gap-4 text-xs text-gray-500">
                <span className="flex items-center gap-1">
                  <Calendar className="w-3 h-3" /> {formatDate(project.updated_at)}
                </span>
              </div>
              {project.tags.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mt-3">
                  {project.tags.map(tag => (
                    <Badge key={tag} variant="info">{tag}</Badge>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* New Project Modal */}
      <Modal isOpen={showNew} onClose={() => setShowNew(false)} title="Create New Project">
        <div className="space-y-4">
          <Input
            label="Project Name"
            placeholder="e.g., Production Web App"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
          />
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Description</label>
            <textarea
              placeholder="What do you want to build?"
              value={newDesc}
              onChange={(e) => setNewDesc(e.target.value)}
              rows={3}
              className="w-full px-4 py-2 bg-gray-900 border border-gray-800 rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#0078D4]"
            />
          </div>
          {error && <p className="text-sm text-red-400">{error}</p>}
          <div className="flex justify-end gap-3">
            <Button variant="ghost" onClick={() => setShowNew(false)}>Cancel</Button>
            <Button onClick={handleCreate} disabled={creating || !newName.trim()}>
              {creating ? 'Creating...' : 'Create Project'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
