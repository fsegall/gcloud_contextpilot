import { useEffect, useState } from 'react';
import { useAccount } from 'wagmi';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Coins, TrendingUp, Clock, ExternalLink } from 'lucide-react';
import { getCPTBalance, formatCPT, isInactive } from '@/lib/viem-client';
import { useQuery } from '@tanstack/react-query';

interface RewardsData {
  total_points: number;
  pending_blockchain: number;
  on_chain_balance: number;
  recent_actions: Array<{
    action_type: string;
    points: number;
    timestamp: string;
    tx_hash?: string;
  }>;
}

export const RewardsWidget = () => {
  const { address, isConnected } = useAccount();
  const [offChainBalance, setOffChainBalance] = useState<RewardsData | null>(null);
  
  // Fetch off-chain balance from API
  const { data: apiData, isLoading: apiLoading } = useQuery({
    queryKey: ['rewards', address],
    queryFn: async () => {
      if (!address) return null;
      const res = await fetch(`${import.meta.env.VITE_API_URL}/rewards/balance/${address}`);
      if (!res.ok) throw new Error('Failed to fetch rewards');
      return res.json() as Promise<RewardsData>;
    },
    enabled: !!address,
    refetchInterval: 10000, // Refresh every 10s
  });
  
  // Fetch on-chain balance directly from contract
  const { data: onChainBalance, isLoading: blockchainLoading } = useQuery({
    queryKey: ['cpt-balance', address],
    queryFn: async () => {
      if (!address) return BigInt(0);
      return await getCPTBalance(address as `0x${string}`);
    },
    enabled: !!address && isConnected,
    refetchInterval: 15000,
  });
  
  // Check if account is inactive
  const { data: inactive } = useQuery({
    queryKey: ['cpt-inactive', address],
    queryFn: async () => {
      if (!address) return false;
      return await isInactive(address as `0x${string}`);
    },
    enabled: !!address && isConnected,
  });
  
  useEffect(() => {
    if (apiData) {
      setOffChainBalance(apiData);
    }
  }, [apiData]);
  
  if (!address || !isConnected) {
    return (
      <Card className="bg-gradient-to-br from-purple-50 to-indigo-50 dark:from-purple-900/20 dark:to-indigo-900/20">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Coins className="w-5 h-5 text-purple-600" />
            <h3 className="font-semibold">CPT Rewards</h3>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-500">
            Connect your wallet to view CPT balance
          </p>
        </CardContent>
      </Card>
    );
  }
  
  const loading = apiLoading || blockchainLoading;
  const formattedOnChain = onChainBalance ? formatCPT(onChainBalance) : '0';
  const pending = offChainBalance?.pending_blockchain || 0;
  
  return (
    <Card className="bg-gradient-to-br from-purple-50 to-indigo-50 dark:from-purple-900/20 dark:to-indigo-900/20 border-purple-200 dark:border-purple-700">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Coins className="w-5 h-5 text-purple-600 dark:text-purple-400" />
            <h3 className="font-semibold text-slate-900 dark:text-slate-100">
              CPT Rewards
            </h3>
          </div>
          {inactive && (
            <Badge variant="destructive" className="text-xs">
              ⚠️ Inactive
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* On-chain Balance */}
        <div>
          <div className="flex items-baseline gap-2">
            <div className="text-3xl font-bold text-purple-600 dark:text-purple-400">
              {loading ? '...' : formattedOnChain}
            </div>
            <span className="text-sm text-gray-500">CPT</span>
          </div>
          <p className="text-xs text-gray-500 mt-1">On-chain (Polygon)</p>
        </div>
        
        {/* Pending Balance */}
        {pending > 0 && (
          <div className="border-t pt-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-400 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                Pending mint
              </span>
              <span className="font-semibold text-orange-600 dark:text-orange-400">
                +{pending} CPT
              </span>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Will be minted in the next batch (daily)
            </p>
          </div>
        )}
        
        {/* Recent Actions */}
        {offChainBalance && offChainBalance.recent_actions.length > 0 && (
          <div className="border-t pt-3">
            <h4 className="text-xs font-semibold text-gray-600 dark:text-gray-400 mb-2 flex items-center gap-1">
              <TrendingUp className="w-3 h-3" />
              Recent Activity
            </h4>
            <div className="space-y-2">
              {offChainBalance.recent_actions.slice(0, 5).map((action, idx) => (
                <div key={idx} className="flex justify-between items-center text-xs">
                  <span className="text-gray-600 dark:text-gray-400 truncate">
                    {action.action_type.replace(/_/g, ' ')}
                  </span>
                  <div className="flex items-center gap-2">
                    <span className={action.points > 0 ? 'text-green-600' : 'text-red-600'}>
                      {action.points > 0 ? '+' : ''}{action.points}
                    </span>
                    {action.tx_hash && (
                      <a
                        href={`https://mumbai.polygonscan.com/tx/${action.tx_hash}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-purple-600 hover:text-purple-700"
                      >
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* Action Button */}
        <Button 
          variant="outline" 
          size="sm" 
          className="w-full mt-4"
          onClick={() => window.open(`https://mumbai.polygonscan.com/token/${import.meta.env.VITE_CPT_CONTRACT_MUMBAI}`, '_blank')}
        >
          View on PolygonScan
        </Button>
      </CardContent>
    </Card>
  );
};

