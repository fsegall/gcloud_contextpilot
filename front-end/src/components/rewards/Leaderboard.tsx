import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Trophy, TrendingUp, Medal } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';

interface LeaderboardEntry {
  rank: number;
  user_id: string;
  total_points: number;
  last_updated: string;
}

const RankIcon = ({ rank }: { rank: number }) => {
  if (rank === 1) return <Trophy className="w-5 h-5 text-yellow-500" />;
  if (rank === 2) return <Medal className="w-5 h-5 text-gray-400" />;
  if (rank === 3) return <Medal className="w-5 h-5 text-orange-600" />;
  return <span className="text-sm text-gray-500">#{rank}</span>;
};

export const Leaderboard = () => {
  const { data: leaderboard, isLoading } = useQuery({
    queryKey: ['leaderboard'],
    queryFn: async () => {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/rewards/leaderboard?limit=10`);
      if (!res.ok) throw new Error('Failed to fetch leaderboard');
      return res.json() as Promise<LeaderboardEntry[]>;
    },
    refetchInterval: 30000, // Refresh every 30s
  });

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5" />
            <h3 className="font-semibold">Top Contributors</h3>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-blue-600" />
          <h3 className="font-semibold text-slate-900 dark:text-slate-100">
            Top Contributors
          </h3>
        </div>
        <p className="text-xs text-gray-500 mt-1">
          Most CPT earned this cycle
        </p>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {leaderboard && leaderboard.length > 0 ? (
            leaderboard.map((entry) => (
              <div
                key={entry.user_id}
                className={`flex items-center justify-between p-3 rounded-lg transition-colors ${
                  entry.rank <= 3
                    ? 'bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border border-blue-200 dark:border-blue-700'
                    : 'bg-gray-50 dark:bg-gray-800'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className="flex items-center justify-center w-8">
                    <RankIcon rank={entry.rank} />
                  </div>
                  <div>
                    <div className="font-medium text-sm text-slate-900 dark:text-slate-100">
                      {entry.user_id.slice(0, 8)}...{entry.user_id.slice(-6)}
                    </div>
                    <div className="text-xs text-gray-500">
                      Last active: {new Date(entry.last_updated).toLocaleDateString()}
                    </div>
                  </div>
                </div>
                <Badge
                  variant={entry.rank <= 3 ? 'default' : 'secondary'}
                  className="font-bold"
                >
                  {entry.total_points.toLocaleString()} CPT
                </Badge>
              </div>
            ))
          ) : (
            <div className="text-center py-8 text-gray-500">
              <TrendingUp className="w-12 h-12 mx-auto mb-2 opacity-30" />
              <p className="text-sm">No leaderboard data yet</p>
              <p className="text-xs mt-1">Start earning CPT to appear here!</p>
            </div>
          )}
        </div>
        
        {leaderboard && leaderboard.length > 0 && (
          <div className="mt-4 pt-4 border-t text-center">
            <p className="text-xs text-gray-500">
              Leaderboard resets every cycle (30 days)
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

