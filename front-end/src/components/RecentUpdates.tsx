
import { User, Bot, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

interface Update {
  id: number;
  author: string;
  timestamp: string;
  summary: string;
  type: "user" | "ai";
}

interface RecentUpdatesProps {
  updates: Update[];
}

export const RecentUpdates = ({ updates }: RecentUpdatesProps) => {
  return (
    <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-2xl p-6 border border-slate-200 dark:border-slate-700 shadow-sm">
      <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">
        Recent Updates
      </h3>
      
      <div className="space-y-3">
        {updates.map((update) => (
          <div
            key={update.id}
            className="group flex items-start gap-3 p-3 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors cursor-pointer"
          >
            <div className={cn(
              "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
              update.type === "ai" 
                ? "bg-gradient-to-r from-indigo-500 to-purple-500" 
                : "bg-blue-500"
            )}>
              {update.type === "ai" ? (
                <Bot className="w-4 h-4 text-white" />
              ) : (
                <User className="w-4 h-4 text-white" />
              )}
            </div>
            
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-sm font-medium text-slate-900 dark:text-slate-100">
                  {update.author}
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400">
                  {update.timestamp}
                </span>
              </div>
              <p className="text-sm text-slate-600 dark:text-slate-400 line-clamp-2">
                {update.summary}
              </p>
            </div>
            
            <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-slate-600 dark:group-hover:text-slate-300 transition-colors" />
          </div>
        ))}
      </div>
    </div>
  );
};
