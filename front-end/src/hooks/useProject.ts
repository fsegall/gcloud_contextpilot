
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiService, UpdateCheckpointRequest } from '@/services/api';
import { useToast } from '@/hooks/use-toast';

export interface Milestone {
  id: number;
  title: string;
  status: 'completed' | 'in-progress' | 'pending';
  dueDate: string;
  description: string;
}

export interface Project {
  name: string;
  objective: string;
  status: string;
  progress: number;
  nextMilestone: string;
  dueDate: string;
}

export const useProject = () => {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  // Mock data for now - would come from API in production
  const [projectData] = useState<Project>({
    name: "Mobile App Redesign",
    objective: "Create a user-friendly mobile experience that increases engagement by 40%",
    status: "Design Phase",
    progress: 35,
    nextMilestone: "Complete user testing",
    dueDate: "2025-07-15"
  });

  const [milestones] = useState<Milestone[]>([
    {
      id: 1,
      title: "Complete user research",
      status: "completed" as const,
      dueDate: "2025-06-20",
      description: "Conduct interviews and surveys with 50+ users"
    },
    {
      id: 2,
      title: "Create wireframes",
      status: "completed" as const,
      dueDate: "2025-06-30", 
      description: "Design low-fidelity mockups for all key screens"
    },
    {
      id: 3,
      title: "Complete user testing",
      status: "in-progress" as const,
      dueDate: "2025-07-15",
      description: "Test prototypes with 20 target users"
    },
    {
      id: 4,
      title: "Finalize design system",
      status: "pending" as const,
      dueDate: "2025-07-30",
      description: "Document components, colors, and guidelines"
    }
  ]);

  const updateCheckpointMutation = useMutation({
    mutationFn: (data: UpdateCheckpointRequest) => apiService.updateCheckpoint(data),
    onSuccess: () => {
      toast({
        title: "Checkpoint saved",
        description: "Your progress has been updated successfully.",
      });
      queryClient.invalidateQueries({ queryKey: ['project'] });
    },
    onError: (error) => {
      toast({
        title: "Error saving checkpoint",
        description: "Failed to save your progress. Please try again.",
        variant: "destructive",
      });
      console.error('Update checkpoint error:', error);
    },
  });

  const commitMutation = useMutation({
    mutationFn: ({ message, agent }: { message?: string; agent?: string }) => 
      apiService.manualCommit(message, agent),
    onSuccess: () => {
      toast({
        title: "Commit successful",
        description: "Manual context update completed.",
      });
    },
    onError: (error) => {
      toast({
        title: "Commit failed",
        description: "Failed to perform manual commit.",
        variant: "destructive",
      });
      console.error('Commit error:', error);
    },
  });

  const askAIMutation = useMutation({
    mutationFn: (prompt: string) => apiService.askLLM(prompt),
    onError: (error) => {
      toast({
        title: "AI request failed",
        description: "Failed to get AI suggestions.",
        variant: "destructive",
      });
      console.error('AI request error:', error);
    },
  });

  return {
    projectData,
    milestones,
    updateCheckpoint: updateCheckpointMutation.mutate,
    isUpdating: updateCheckpointMutation.isPending,
    manualCommit: commitMutation.mutate,
    isCommitting: commitMutation.isPending,
    askAI: askAIMutation.mutate,
    isAskingAI: askAIMutation.isPending,
    aiResponse: askAIMutation.data,
  };
};
