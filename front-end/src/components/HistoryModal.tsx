
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { User, Bot, ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

interface Update {
  id: number;
  author: string;
  timestamp: string;
  summary: string;
  type: "user" | "ai";
}

interface HistoryModalProps {
  open: boolean;
  onClose: () => void;
  updates: Update[];
}

export const HistoryModal = ({ open, onClose, updates }: HistoryModalProps) => {
  const [expandedUpdate, setExpandedUpdate] = useState<number | null>(null);

  const toggleExpanded = (id: number) => {
    setExpandedUpdate(expandedUpdate === id ? null : id);
  };

  const fullUpdates = [
    ...updates,
    {
      id: 4,
      author: "You",
      timestamp: "3 days ago",
      summary: "Started wireframing process after research completion",
      type: "user" as const
    },
    {
      id: 5,
      author: "AI Assistant",
      timestamp: "4 days ago", 
      summary: "Recommended prioritizing user research before design work",
      type: "ai" as const
    },
    {
      id: 6,
      author: "You",
      timestamp: "1 week ago",
      summary: "Project initiated with goal setting and timeline planning",
      type: "user" as const
    }
  ];

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[700px] h-[600px]">
        <DialogHeader>
          <DialogTitle className="text-xl font-semibold">
            Progress History
          </DialogTitle>
        </DialogHeader>
        
        <ScrollArea className="flex-1 mt-4">
          <div className="space-y-4 pr-4">
            {fullUpdates.map((update) => (
              <div
                key={update.id}
                className="border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden"
              >
                <div
                  className="flex items-start gap-4 p-4 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
                  onClick={() => toggleExpanded(update.id)}
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
                    <div className="flex items-center gap-2 mb-2">
                      <span className="font-medium text-slate-900 dark:text-slate-100">
                        {update.author}
                      </span>
                      <span className="text-sm text-slate-500 dark:text-slate-400">
                        {update.timestamp}
                      </span>
                    </div>
                    <p className="text-slate-600 dark:text-slate-400">
                      {update.summary}
                    </p>
                  </div>
                  
                  <div className="flex-shrink-0">
                    {expandedUpdate === update.id ? (
                      <ChevronUp className="w-5 h-5 text-slate-400" />
                    ) : (
                      <ChevronDown className="w-5 h-5 text-slate-400" />
                    )}
                  </div>
                </div>
                
                {expandedUpdate === update.id && (
                  <div className="px-4 pb-4 border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/30">
                    <div className="pt-4">
                      <h4 className="font-medium text-slate-900 dark:text-slate-100 mb-2">
                        Full Details
                      </h4>
                      <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                        {update.type === "ai" ? (
                          `Based on the current project trajectory and industry best practices, I recommend focusing on ${update.summary.toLowerCase()}. This approach will help ensure better user validation and reduce the risk of costly design revisions later in the process.`
                        ) : (
                          `Progress update: ${update.summary}. This milestone represents significant progress toward the overall project objective. Next steps will focus on maintaining momentum while ensuring quality standards are met.`
                        )}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
};
