
import { Calendar, Target } from "lucide-react";

interface ProjectHeaderProps {
  project: {
    name: string;
    objective: string;
    status: string;
    progress: number;
    nextMilestone: string;
    dueDate: string;
  };
}

export const ProjectHeader = ({ project }: ProjectHeaderProps) => {
  return (
    <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-2xl p-6 border border-slate-200 dark:border-slate-700 shadow-sm">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div className="flex-1">
          <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-2">
            {project.name}
          </h2>
          <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400 mb-4">
            <Target className="w-4 h-4" />
            <p className="text-sm">{project.objective}</p>
          </div>
        </div>
        
        <div className="flex flex-col sm:flex-row gap-4 lg:gap-8">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
              {project.progress}%
            </div>
            <div className="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-wide">
              Complete
            </div>
          </div>
          <div className="text-center">
            <div className="text-sm font-semibold text-slate-900 dark:text-slate-100">
              {project.nextMilestone}
            </div>
            <div className="flex items-center gap-1 text-xs text-slate-500 dark:text-slate-400 mt-1">
              <Calendar className="w-3 h-3" />
              Due {project.dueDate}
            </div>
          </div>
        </div>
      </div>
      
      {/* Progress Bar */}
      <div className="mt-4">
        <div className="h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
          <div 
            className="h-full bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full transition-all duration-500"
            style={{ width: `${project.progress}%` }}
          />
        </div>
      </div>
    </div>
  );
};
