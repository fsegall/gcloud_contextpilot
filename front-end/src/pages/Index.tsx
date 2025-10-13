
import { useState } from "react";
import { ProjectHeader } from "@/components/ProjectHeader";
import { StatusCard } from "@/components/StatusCard";
import { MilestonesList } from "@/components/MilestonesList";
import { RecentUpdates } from "@/components/RecentUpdates";
import { UpdateModal } from "@/components/UpdateModal";
import { HistoryModal } from "@/components/HistoryModal";
import { WorkspaceSelector } from "@/components/workspace/WorkspaceSelector";
import { WorkspaceDetails } from "@/components/workspace/WorkspaceDetails";
import { Button } from "@/components/ui/button";
import { Plus, History, Target, GitCommit, LogOut, User } from "lucide-react";
import { useProject } from "@/hooks/useProject";
import { useAuth } from "@/hooks/useAuth";
import { usePermissions } from "@/hooks/usePermissions";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { supabase } from "@/integrations/supabase/client";
import { useEffect } from "react";

interface Workspace {
  id: string;
  name: string;
  description: string | null;
}

const Index = () => {
  const [showUpdateModal, setShowUpdateModal] = useState(false);
  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const [selectedWorkspace, setSelectedWorkspace] = useState<string | null>(null);
  const [currentWorkspace, setCurrentWorkspace] = useState<Workspace | null>(null);
  
  const { user, profile, signOut } = useAuth();
  const { hasPermission } = usePermissions();
  const { 
    projectData, 
    milestones, 
    manualCommit, 
    isCommitting 
  } = useProject();

  // Fetch workspace details when selectedWorkspace changes
  useEffect(() => {
    if (selectedWorkspace) {
      fetchWorkspaceDetails();
    }
  }, [selectedWorkspace]);

  const fetchWorkspaceDetails = async () => {
    if (!selectedWorkspace) return;

    try {
      const { data } = await supabase
        .from('workspaces')
        .select('id, name, description')
        .eq('id', selectedWorkspace)
        .single();

      setCurrentWorkspace(data);
    } catch (error) {
      console.error('Error fetching workspace details:', error);
    }
  };

  const recentUpdates = [
    {
      id: 1,
      author: "You",
      timestamp: "2 hours ago",
      summary: "Completed wireframes for checkout flow",
      type: "user" as const
    },
    {
      id: 2,
      author: "AI Assistant", 
      timestamp: "3 hours ago",
      summary: "Suggested focusing on mobile-first approach for better conversion",
      type: "ai" as const
    },
    {
      id: 3,
      author: "You",
      timestamp: "1 day ago", 
      summary: "User interviews reveal navigation confusion",
      type: "user" as const
    }
  ];

  const handleManualCommit = () => {
    if (selectedWorkspace && hasPermission(selectedWorkspace, 'commit_context')) {
      manualCommit({
        message: "Manual context update from UI",
        agent: "user"
      });
    }
  };

  const canUpdateCheckpoint = selectedWorkspace ? hasPermission(selectedWorkspace, 'update_checkpoint') : false;
  const canCommitContext = selectedWorkspace ? hasPermission(selectedWorkspace, 'commit_context') : false;
  const canViewHistory = selectedWorkspace ? hasPermission(selectedWorkspace, 'view_history') : false;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900">
      <div className="container mx-auto px-4 py-6 max-w-7xl">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">
              ContextPilot
            </h1>
            <p className="text-slate-600 dark:text-slate-400 mt-1">
              Intelligent project guidance
            </p>
          </div>
          <div className="flex items-center gap-3">
            {canCommitContext && (
              <Button
                onClick={handleManualCommit}
                disabled={isCommitting}
                variant="outline"
                className="flex items-center gap-2"
              >
                {isCommitting ? (
                  <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                ) : (
                  <GitCommit className="w-4 h-4" />
                )}
                {isCommitting ? "Committing..." : "Manual Commit"}
              </Button>
            )}
            {canViewHistory && (
              <Button
                onClick={() => setShowHistoryModal(true)}
                variant="outline"
                className="flex items-center gap-2"
              >
                <History className="w-4 h-4" />
                History
              </Button>
            )}
            {canUpdateCheckpoint && (
              <Button
                onClick={() => setShowUpdateModal(true)}
                className="flex items-center gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
              >
                <Plus className="w-4 h-4" />
                Update Progress
              </Button>
            )}
            
            {/* User Menu */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="flex items-center gap-2">
                  <Avatar className="w-8 h-8">
                    <AvatarImage src={profile?.avatar_url} />
                    <AvatarFallback>
                      {profile?.full_name?.charAt(0) || user?.email?.charAt(0) || 'U'}
                    </AvatarFallback>
                  </Avatar>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem className="flex items-center gap-2">
                  <User className="w-4 h-4" />
                  {profile?.full_name || user?.email}
                </DropdownMenuItem>
                <DropdownMenuItem onClick={signOut} className="flex items-center gap-2">
                  <LogOut className="w-4 h-4" />
                  Sign Out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        {/* Workspace Selector */}
        <WorkspaceSelector
          selectedWorkspace={selectedWorkspace}
          onWorkspaceChange={setSelectedWorkspace}
        />

        {selectedWorkspace && currentWorkspace ? (
          <>
            {/* Workspace Details */}
            <WorkspaceDetails workspace={currentWorkspace} />

            {/* Project Header */}
            <ProjectHeader project={projectData} />

            {/* Main Content Grid */}
            <div className="grid lg:grid-cols-3 gap-6 mt-8">
              {/* Left Column - Status & Milestones */}
              <div className="lg:col-span-2 space-y-6">
                <StatusCard project={projectData} />
                <MilestonesList milestones={milestones} />
              </div>

              {/* Right Column - Recent Updates */}
              <div className="space-y-6">
                {canViewHistory && <RecentUpdates updates={recentUpdates} />}
                
                {/* AI Insights Card */}
                <div className="bg-gradient-to-br from-indigo-50 to-blue-50 dark:from-indigo-900/20 dark:to-blue-900/20 rounded-xl p-6 border border-indigo-200 dark:border-indigo-700">
                  <div className="flex items-center gap-3 mb-4">
                    <Target className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
                    <h3 className="font-semibold text-slate-900 dark:text-slate-100">AI Insights</h3>
                  </div>
                  <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
                    Based on your progress, consider scheduling user testing sessions early to validate wireframe decisions before moving to high-fidelity designs.
                  </p>
                  {hasPermission(selectedWorkspace, 'push_to_llm') && (
                    <Button variant="outline" size="sm" className="w-full">
                      Get More Suggestions
                    </Button>
                  )}
                </div>
              </div>
            </div>
          </>
        ) : (
          <div className="text-center py-12">
            <p className="text-gray-500 mb-4">Please select a workspace to continue</p>
          </div>
        )}
      </div>

      {/* Modals */}
      {canUpdateCheckpoint && (
        <UpdateModal 
          open={showUpdateModal} 
          onClose={() => setShowUpdateModal(false)}
          project={projectData}
        />
      )}
      {canViewHistory && (
        <HistoryModal 
          open={showHistoryModal}
          onClose={() => setShowHistoryModal(false)}
          updates={recentUpdates}
        />
      )}
    </div>
  );
};

export default Index;
