
import { useState } from 'react';
import { usePermissions } from '@/hooks/usePermissions';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Settings, Users, FolderOpen } from 'lucide-react';
import { WorkspaceMembers } from './WorkspaceMembers';

interface Workspace {
  id: string;
  name: string;
  description: string | null;
}

interface WorkspaceDetailsProps {
  workspace: Workspace;
}

export const WorkspaceDetails = ({ workspace }: WorkspaceDetailsProps) => {
  const { hasPermission } = usePermissions();
  const [activeTab, setActiveTab] = useState('overview');

  const canManageWorkspace = hasPermission(workspace.id, 'delete_workspace');

  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold">{workspace.name}</h2>
            {workspace.description && (
              <p className="text-sm text-gray-600 mt-1">{workspace.description}</p>
            )}
          </div>
          {canManageWorkspace && (
            <Button variant="outline" size="sm">
              <Settings className="w-4 h-4 mr-2" />
              Settings
            </Button>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="overview" className="flex items-center gap-2">
              <FolderOpen className="w-4 h-4" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="members" className="flex items-center gap-2">
              <Users className="w-4 h-4" />
              Members
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="overview" className="mt-4">
            <div className="text-center py-8 text-gray-500">
              <FolderOpen className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>Workspace overview and project statistics will be displayed here.</p>
            </div>
          </TabsContent>
          
          <TabsContent value="members" className="mt-4">
            <WorkspaceMembers 
              workspaceId={workspace.id} 
              workspaceName={workspace.name}
            />
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};
