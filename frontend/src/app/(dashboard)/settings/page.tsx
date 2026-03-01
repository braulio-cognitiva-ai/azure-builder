'use client';

import { useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';
import { Tabs } from '@/components/ui/Tabs';
import { User, Cloud, Users, Plus, Trash2 } from 'lucide-react';

const mockConnections = [
  { id: '1', subscription_id: 'sub-prod-001', subscription_name: 'Production', status: 'active' as const, created_at: '2026-01-15T10:00:00Z' },
  { id: '2', subscription_id: 'sub-dev-002', subscription_name: 'Development', status: 'active' as const, created_at: '2026-02-01T14:00:00Z' },
];

function ProfileTab() {
  const { user } = useAuth();
  const [name, setName] = useState(user?.name || '');
  const [saved, setSaved] = useState(false);

  return (
    <div className="max-w-xl space-y-6">
      <Card>
        <h3 className="text-lg font-semibold text-gray-100 mb-4">Profile Information</h3>
        <div className="space-y-4">
          <div>
            <label className="text-sm text-gray-400 block mb-1">Display Name</label>
            <Input value={name} onChange={e => { setName(e.target.value); setSaved(false); }} placeholder="Your name" />
          </div>
          <div>
            <label className="text-sm text-gray-400 block mb-1">Email</label>
            <Input value={user?.email || ''} disabled />
          </div>
          <div>
            <label className="text-sm text-gray-400 block mb-1">Role</label>
            <Badge variant="info">Owner</Badge>
          </div>
          <Button onClick={() => setSaved(true)}>
            {saved ? '✓ Saved' : 'Save Changes'}
          </Button>
        </div>
      </Card>
    </div>
  );
}

function AzureTab() {
  const [connections, setConnections] = useState(mockConnections);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({ subscription_id: '', tenant_id: '', client_id: '', client_secret: '' });

  const handleConnect = () => {
    setConnections([...connections, {
      id: String(connections.length + 1),
      subscription_id: form.subscription_id,
      subscription_name: 'New Subscription',
      status: 'active',
      created_at: new Date().toISOString(),
    }]);
    setShowModal(false);
    setForm({ subscription_id: '', tenant_id: '', client_id: '', client_secret: '' });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-100">Azure Subscriptions</h3>
        <Button onClick={() => setShowModal(true)}>
          <Plus className="w-4 h-4 mr-2" /> Connect Subscription
        </Button>
      </div>

      <div className="space-y-4">
        {connections.map(conn => (
          <Card key={conn.id}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 bg-[#0078D4]/10 rounded-lg flex items-center justify-center">
                  <Cloud className="w-5 h-5 text-[#0078D4]" />
                </div>
                <div>
                  <p className="text-gray-100 font-medium">{conn.subscription_name}</p>
                  <p className="text-sm text-gray-500">{conn.subscription_id}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Badge variant={conn.status === 'active' ? 'success' : 'danger'}>{conn.status}</Badge>
                <button
                  onClick={() => setConnections(connections.filter(c => c.id !== conn.id))}
                  className="text-gray-500 hover:text-red-400 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          </Card>
        ))}
      </div>

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Connect Azure Subscription">
        <div className="space-y-4">
          <div>
            <label className="text-sm text-gray-400 block mb-1">Subscription ID</label>
            <Input value={form.subscription_id} onChange={e => setForm({ ...form, subscription_id: e.target.value })} placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" />
          </div>
          <div>
            <label className="text-sm text-gray-400 block mb-1">Tenant ID</label>
            <Input value={form.tenant_id} onChange={e => setForm({ ...form, tenant_id: e.target.value })} placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" />
          </div>
          <div>
            <label className="text-sm text-gray-400 block mb-1">Client ID</label>
            <Input value={form.client_id} onChange={e => setForm({ ...form, client_id: e.target.value })} placeholder="App registration client ID" />
          </div>
          <div>
            <label className="text-sm text-gray-400 block mb-1">Client Secret</label>
            <Input type="password" value={form.client_secret} onChange={e => setForm({ ...form, client_secret: e.target.value })} placeholder="••••••••" />
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <Button variant="secondary" onClick={() => setShowModal(false)}>Cancel</Button>
            <Button onClick={handleConnect}>Connect</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

function TeamTab() {
  return (
    <Card>
      <div className="text-center py-12">
        <Users className="w-12 h-12 text-gray-600 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-300">Team Management</h3>
        <p className="text-gray-500 mt-2">Coming soon. Invite team members and manage roles.</p>
      </div>
    </Card>
  );
}

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-100">Settings</h1>
        <p className="text-gray-400 mt-1">Manage your account, connections, and team.</p>
      </div>

      <Tabs
        tabs={[
          { id: 'profile', label: 'Profile', icon: <User className="w-4 h-4" />, content: <ProfileTab /> },
          { id: 'azure', label: 'Azure Connections', icon: <Cloud className="w-4 h-4" />, content: <AzureTab /> },
          { id: 'team', label: 'Team', icon: <Users className="w-4 h-4" />, content: <TeamTab /> },
        ]}
      />
    </div>
  );
}
