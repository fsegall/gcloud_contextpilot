
import { CheckCircle, Clock, Circle } from "lucide-react";
import { cn } from "@/lib/utils";

interface Milestone {
  id: number;
  title: string;
  status: "completed" | "in-progress" | "pending";
  dueDate: string;
  description: string;
}

interface MilestonesListProps {
  milestones: Milestone[];
}

export const MilestonesList = ({ milestones }: MilestonesListProps) => {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case "in-progress":
        return <Clock className="w-5 h-5 text-blue-500" />;
      default:
        return <Circle className="w-5 h-5 text-slate-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-700";
      case "in-progress":
        return "bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-700";
      default:
        return "bg-slate-50 dark:bg-slate-800/50 border-slate-200 dark:border-slate-700";
    }
  };

  return (
    <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-2xl p-6 border border-slate-200 dark:border-slate-700 shadow-sm">
      <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-6">
        Milestones
      </h3>
      
      <div className="space-y-4">
        {milestones.map((milestone, index) => (
          <div
            key={milestone.id}
            className={cn(
              "rounded-xl p-4 border transition-all duration-200 hover:shadow-sm",
              getStatusColor(milestone.status)
            )}
          >
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 mt-1">
                {getStatusIcon(milestone.status)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-slate-900 dark:text-slate-100">
                    {milestone.title}
                  </h4>
                  <span className="text-sm text-slate-500 dark:text-slate-400">
                    {milestone.dueDate}
                  </span>
                </div>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  {milestone.description}
                </p>
              </div>
            </div>
            
            {/* Progress connector line */}
            {index < milestones.length - 1 && (
              <div className="ml-2.5 mt-4 mb-2">
                <div className="h-6 w-px bg-slate-200 dark:bg-slate-600" />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
