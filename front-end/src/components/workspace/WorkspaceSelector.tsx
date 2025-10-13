
import { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/hooks/useAuth';
import { usePermissions } from '@/hooks/usePermissions';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Plus } from 'lucide-react';
import { CreateWorkspaceModal } from './CreateWorkspaceModal';

interface Workspace {
  id: string;
  name: string;
  description: string;
}

interface WorkspaceSelectorProps {
  selectedWorkspace: string | null;
  onWorkspaceChange: (workspaceId: string) => void;
}

export const WorkspaceSelector = ({ 
  selectedWorkspace, 
  onWorkspaceChange
}: WorkspaceSelectorProps) => {
  const { user } = useAuth();
  const { hasPermission } = usePermissions();
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);

  useEffect(() => {
    if (user) {
      fetchWorkspaces();
    }
  }, [user]);

  const fetchWorkspaces = async () => {
    try {
      const { data } = await supabase
        .from('workspace_members')
        .select(`
          workspaces (
            id,
            name,
            description
          )
        `)
        .eq('user_id', user?.id);

      const workspaceData = data?.map(item => item.workspaces).filter(Boolean) || [];
      setWorkspaces(workspaceData);
      
      if (workspaceData.length > 0 && !selectedWorkspace) {
        onWorkspaceChange(workspaceData[0].id);
      }
    } catch (error) {
      console.error('Error fetching workspaces:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleWorkspaceCreated = (workspaceId: string) => {
    fetchWorkspaces();
    onWorkspaceChange(workspaceId);
  };

  if (loading) {
    return <div className="animate-pulse h-20 bg-gray-200 rounded"></div>;
  }

  return (
    <>
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Workspace</span>
            <Button
              onClick={() => setShowCreateModal(true)}
              size="sm"
              className="flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              New Workspace
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {workspaces.length > 0 ? (
            <Select value={selectedWorkspace || ''} onValueChange={onWorkspaceChange}>
              <SelectTrigger>
                <SelectValue placeholder="Select a workspace" />
              </SelectTrigger>
              <SelectContent>
                {workspaces.map((workspace) => (
                  <SelectItem key={workspace.id} value={workspace.id}>
                    <div>
                      <div className="font-medium">{workspace.name}</div>
                      {workspace.description && (
                        <div className="text-xs text-gray-500">{workspace.description}</div>
                      )}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          ) : (
            <p className="text-gray-500 text-center py-4">
              No workspaces found. Create your first workspace to get started.
            </p>
          )}
        </CardContent>
      </Card>

      <CreateWorkspaceModal
        open={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onWorkspaceCreated={handleWorkspaceCreated}
      />
    </>
  );
};
