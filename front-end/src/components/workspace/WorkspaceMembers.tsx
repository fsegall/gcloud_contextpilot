
import { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/hooks/useAuth';
import { usePermissions } from '@/hooks/usePermissions';
import { useToast } from '@/hooks/use-toast';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { UserPlus, MoreVertical, Crown, Edit, Eye } from 'lucide-react';
import { InviteUserModal } from './InviteUserModal';

interface WorkspaceMember {
  id: string;
  user_id: string;
  role: 'owner' | 'contributor' | 'viewer';
  created_at: string;
  profiles: {
    full_name: string | null;
    email: string;
    avatar_url: string | null;
  } | null;
}

interface WorkspaceMembersProps {
  workspaceId: string;
  workspaceName: string;
}

export const WorkspaceMembers = ({ workspaceId, workspaceName }: WorkspaceMembersProps) => {
  const [members, setMembers] = useState<WorkspaceMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const { user } = useAuth();
  const { hasPermission } = usePermissions();
  const { toast } = useToast();

  const canInviteUsers = hasPermission(workspaceId, 'invite_user');
  const canAssignRoles = hasPermission(workspaceId, 'assign_role');

  useEffect(() => {
    fetchMembers();
  }, [workspaceId]);

  const fetchMembers = async () => {
    try {
      // First get workspace members
      const { data: membersData, error: membersError } = await supabase
        .from('workspace_members')
        .select('id, user_id, role, created_at')
        .eq('workspace_id', workspaceId)
        .order('created_at', { ascending: true });

      if (membersError) throw membersError;

      if (!membersData || membersData.length === 0) {
        setMembers([]);
        return;
      }

      // Get user IDs
      const userIds = membersData.map(member => member.user_id);

      // Fetch profiles separately
      const { data: profilesData, error: profilesError } = await supabase
        .from('profiles')
        .select('id, full_name, email, avatar_url')
        .in('id', userIds);

      if (profilesError) throw profilesError;

      // Combine the data
      const combinedData = membersData.map(member => {
        const profile = profilesData?.find(p => p.id === member.user_id);
        return {
          ...member,
          profiles: profile ? {
            full_name: profile.full_name,
            email: profile.email,
            avatar_url: profile.avatar_url
          } : null
        };
      });

      setMembers(combinedData);
    } catch (error: any) {
      console.error('Error fetching members:', error);
      toast({
        title: "Error",
        description: "Failed to load workspace members",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleRoleChange = async (memberId: string, newRole: 'contributor' | 'viewer') => {
    try {
      const { error } = await supabase
        .from('workspace_members')
        .update({ role: newRole })
        .eq('id', memberId);

      if (error) throw error;

      toast({
        title: "Success",
        description: "Member role updated successfully",
      });

      fetchMembers();
    } catch (error: any) {
      console.error('Error updating role:', error);
      toast({
        title: "Error",
        description: "Failed to update member role",
        variant: "destructive",
      });
    }
  };

  const handleRemoveMember = async (memberId: string) => {
    try {
      const { error } = await supabase
        .from('workspace_members')
        .delete()
        .eq('id', memberId);

      if (error) throw error;

      toast({
        title: "Success",
        description: "Member removed from workspace",
      });

      fetchMembers();
    } catch (error: any) {
      console.error('Error removing member:', error);
      toast({
        title: "Error",
        description: "Failed to remove member",
        variant: "destructive",
      });
    }
  };

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'owner':
        return <Crown className="w-4 h-4" />;
      case 'contributor':
        return <Edit className="w-4 h-4" />;
      case 'viewer':
        return <Eye className="w-4 h-4" />;
      default:
        return null;
    }
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'owner':
        return 'bg-yellow-100 text-yellow-800';
      case 'contributor':
        return 'bg-blue-100 text-blue-800';
      case 'viewer':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return <div className="animate-pulse h-40 bg-gray-200 rounded"></div>;
  }

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Workspace Members ({members.length})</CardTitle>
            {canInviteUsers && (
              <Button
                onClick={() => setShowInviteModal(true)}
                size="sm"
                className="flex items-center gap-2"
              >
                <UserPlus className="w-4 h-4" />
                Invite User
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {members.map((member) => {
              const profile = member.profiles;
              if (!profile) return null;

              return (
                <div
                  key={member.id}
                  className="flex items-center justify-between p-3 border rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <Avatar>
                      <AvatarImage src={profile.avatar_url || undefined} />
                      <AvatarFallback>
                        {profile.full_name?.charAt(0) || profile.email.charAt(0)}
                      </AvatarFallback>
                    </Avatar>
                    <div>
                      <div className="font-medium">
                        {profile.full_name || profile.email}
                      </div>
                      <div className="text-sm text-gray-500">
                        {profile.email}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge className={`flex items-center gap-1 ${getRoleColor(member.role)}`}>
                      {getRoleIcon(member.role)}
                      {member.role}
                    </Badge>
                    {canAssignRoles && member.role !== 'owner' && member.user_id !== user?.id && (
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm">
                            <MoreVertical className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          {member.role !== 'contributor' && (
                            <DropdownMenuItem
                              onClick={() => handleRoleChange(member.id, 'contributor')}
                            >
                              Make Contributor
                            </DropdownMenuItem>
                          )}
                          {member.role !== 'viewer' && (
                            <DropdownMenuItem
                              onClick={() => handleRoleChange(member.id, 'viewer')}
                            >
                              Make Viewer
                            </DropdownMenuItem>
                          )}
                          <DropdownMenuItem
                            onClick={() => handleRemoveMember(member.id)}
                            className="text-red-600"
                          >
                            Remove from Workspace
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      <InviteUserModal
        open={showInviteModal}
        onClose={() => setShowInviteModal(false)}
        workspaceId={workspaceId}
        workspaceName={workspaceName}
      />
    </>
  );
};
