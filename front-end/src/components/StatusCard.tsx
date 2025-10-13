
import { TrendingUp, Clock, AlertCircle } from "lucide-react";

interface StatusCardProps {
  project: {
    status: string;
    progress: number;
  };
}

export const StatusCard = ({ project }: StatusCardProps) => {
  return (
    <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-2xl p-6 border border-slate-200 dark:border-slate-700 shadow-sm">
      <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">
        Current Status
      </h3>
      
      <div className="grid sm:grid-cols-3 gap-4">
        <div className="bg-green-50 dark:bg-green-900/20 rounded-xl p-4 border border-green-200 dark:border-green-700">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-4 h-4 text-green-600 dark:text-green-400" />
            <span className="text-sm font-medium text-green-800 dark:text-green-300">
              On Track
            </span>
          </div>
          <p className="text-xs text-green-600 dark:text-green-400">
            Meeting milestones
          </p>
        </div>
        
        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-4 border border-blue-200 dark:border-blue-700">
          <div className="flex items-center gap-2 mb-2">
            <Clock className="w-4 h-4 text-blue-600 dark:text-blue-400" />
            <span className="text-sm font-medium text-blue-800 dark:text-blue-300">
              {project.status}
            </span>
          </div>
          <p className="text-xs text-blue-600 dark:text-blue-400">
            Current phase
          </p>
        </div>
        
        <div className="bg-amber-50 dark:bg-amber-900/20 rounded-xl p-4 border border-amber-200 dark:border-amber-700">
          <div className="flex items-center gap-2 mb-2">
            <AlertCircle className="w-4 h-4 text-amber-600 dark:text-amber-400" />
            <span className="text-sm font-medium text-amber-800 dark:text-amber-300">
              2 Days Left
            </span>
          </div>
          <p className="text-xs text-amber-600 dark:text-amber-400">
            Next milestone
          </p>
        </div>
      </div>
    </div>
  );
};
