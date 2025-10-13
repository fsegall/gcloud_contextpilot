
import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Sparkles, Save } from "lucide-react";
import { useProject } from "@/hooks/useProject";

interface UpdateModalProps {
  open: boolean;
  onClose: () => void;
  project: {
    name: string;
    objective: string;
  };
}

export const UpdateModal = ({ open, onClose, project }: UpdateModalProps) => {
  const [status, setStatus] = useState("");
  const [milestone, setMilestone] = useState("");
  const { 
    updateCheckpoint, 
    isUpdating, 
    askAI, 
    isAskingAI, 
    aiResponse,
    milestones 
  } = useProject();

  const handleAskAI = () => {
    const prompt = `Based on the project "${project.name}" with goal "${project.objective}" and current status "${status}", what should be the next steps?`;
    askAI(prompt);
  };

  const handleSave = () => {
    if (!status.trim()) return;

    const updateData = {
      project_name: project.name,
      goal: project.objective,
      current_status: status,
      milestones: milestones.map(m => ({
        id: m.id,
        title: m.title,
        status: m.status,
        dueDate: m.dueDate,
        description: m.description,
      })),
    };

    updateCheckpoint(updateData);
    
    // Reset form and close modal
    setStatus("");
    setMilestone("");
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle className="text-xl font-semibold">
            Update Progress - {project.name}
          </DialogTitle>
        </DialogHeader>
        
        <div className="space-y-6 mt-4">
          {/* Current Status */}
          <div className="space-y-2">
            <Label htmlFor="status">Current Status</Label>
            <Textarea
              id="status"
              placeholder="What's your current progress? What have you accomplished recently?"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="min-h-[100px]"
            />
          </div>
          
          {/* New Milestone */}
          <div className="space-y-2">
            <Label htmlFor="milestone">Next Milestone (Optional)</Label>
            <Input
              id="milestone"
              placeholder="What's your next goal or milestone?"
              value={milestone}
              onChange={(e) => setMilestone(e.target.value)}
            />
          </div>
          
          {/* AI Section */}
          <div className="bg-gradient-to-br from-indigo-50 to-blue-50 dark:from-indigo-900/20 dark:to-blue-900/20 rounded-xl p-4 border border-indigo-200 dark:border-indigo-700">
            <div className="flex items-center gap-2 mb-3">
              <Sparkles className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
              <h4 className="font-medium text-slate-900 dark:text-slate-100">
                AI Guidance
              </h4>
            </div>
            <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
              Get personalized suggestions for your next steps based on your progress and goals.
            </p>
            
            {aiResponse && (
              <div className="mb-4 p-3 bg-white dark:bg-slate-800 rounded-lg border">
                <p className="text-sm text-slate-700 dark:text-slate-300">
                  {typeof aiResponse === 'string' ? aiResponse : JSON.stringify(aiResponse)}
                </p>
              </div>
            )}
            
            <Button
              onClick={handleAskAI}
              disabled={isAskingAI || !status.trim()}
              variant="outline"
              className="w-full"
            >
              {isAskingAI ? (
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
                  Analyzing...
                </div>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 mr-2" />
                  Ask AI for Next Steps
                </>
              )}
            </Button>
          </div>
          
          {/* Action Buttons */}
          <div className="flex gap-3 pt-4">
            <Button variant="outline" onClick={onClose} className="flex-1">
              Cancel
            </Button>
            <Button 
              onClick={handleSave}
              disabled={!status.trim() || isUpdating}
              className="flex-1 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
            >
              {isUpdating ? (
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Saving...
                </div>
              ) : (
                <>
                  <Save className="w-4 h-4 mr-2" />
                  Save Checkpoint
                </>
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};
