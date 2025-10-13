
import { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from './useAuth';

export type Permission = 
  | 'create_workspace'
  | 'delete_workspace'
  | 'create_project'
  | 'delete_project'
  | 'update_checkpoint'
  | 'commit_context'
  | 'push_to_llm'
  | 'invite_user'
  | 'assign_role'
  | 'view_history'
  | 'view_project';

export type Role = 'owner' | 'contributor' | 'viewer';

interface WorkspacePermissions {
  [workspaceId: string]: {
    role: Role;
    permissions: Permission[];
  };
}

export const usePermissions = () => {
  const { user } = useAuth();
  const [workspacePermissions, setWorkspacePermissions] = useState<WorkspacePermissions>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) {
      setWorkspacePermissions({});
      setLoading(false);
      return;
    }

    fetchUserPermissions();
  }, [user]);

  const fetchUserPermissions = async () => {
    if (!user) return;

    try {
      const { data: memberships } = await supabase
        .from('workspace_members')
        .select(`
          workspace_id,
          role,
          workspaces (
            id,
            name
          )
        `)
        .eq('user_id', user.id);

      const permissions: WorkspacePermissions = {};
      
      memberships?.forEach((membership) => {
        const role = membership.role as Role;
        permissions[membership.workspace_id] = {
          role,
          permissions: getRolePermissions(role)
        };
      });

      setWorkspacePermissions(permissions);
    } catch (error) {
      console.error('Error fetching permissions:', error);
    } finally {
      setLoading(false);
    }
  };

  const getRolePermissions = (role: Role): Permission[] => {
    switch (role) {
      case 'owner':
        return [
          'create_workspace',
          'delete_workspace',
          'create_project',
          'delete_project',
          'update_checkpoint',
          'commit_context',
          'push_to_llm',
          'invite_user',
          'assign_role',
          'view_history',
          'view_project'
        ];
      case 'contributor':
        return [
          'update_checkpoint',
          'commit_context',
          'view_history',
          'push_to_llm',
          'view_project'
        ];
      case 'viewer':
        return [
          'view_project',
          'view_history'
        ];
      default:
        return [];
    }
  };

  const hasPermission = (workspaceId: string, permission: Permission): boolean => {
    return workspacePermissions[workspaceId]?.permissions.includes(permission) || false;
  };

  const getUserRole = (workspaceId: string): Role | null => {
    return workspacePermissions[workspaceId]?.role || null;
  };

  return {
    workspacePermissions,
    hasPermission,
    getUserRole,
    loading,
    refetch: fetchUserPermissions
  };
};
