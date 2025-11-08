import axios, { AxiosInstance } from 'axios';

export interface ProposalDiff {
  format: 'unified' | 'git-patch';
  content: string;
}

export interface ProposedChange {
  file_path: string;
  change_type: 'create' | 'update' | 'delete';
  description: string;
  before?: string;
  after?: string;
  diff?: string;
}

export interface ChangeProposal {
  id: string;
  agent_id: string;
  workspace_id: string;
  title: string;
  description: string;
  diff: ProposalDiff;
  proposed_changes: Array<ProposedChange>;
  status: 'pending' | 'approved' | 'rejected';
  created_at: string;
  ai_review?: {
    model: string;
    verdict: 'approve' | 'reject' | 'needs_changes';
    reasoning: string;
    concerns: string[];
    suggestions: string[];
  };
}

export interface Balance {
  balance: number;
  total_earned: number;
  pending_rewards: number;
  weeklyStreak?: number;
  achievements?: any[];
  rank?: number;
}

export interface AgentStatus {
  agent_id: string;
  name: string;
  status: 'active' | 'idle' | 'error';
  last_activity: string;
}

export class ContextPilotService {
  private client: AxiosInstance;
  private connected: boolean = false;
  private userId: string;
  private workspaceId: string = 'contextpilot'; // Default workspace
  private walletAddress: string;
  private testMode: boolean = false;

  constructor(apiUrl: string, userId: string, walletAddress: string, testMode: boolean = false) {
    this.client = axios.create({
      baseURL: apiUrl,
      timeout: 30000, // Increased for Cloud Run cold starts
      headers: {
        'Content-Type': 'application/json',
      },
    });
    this.userId = userId || 'test-user';
    this.walletAddress = walletAddress || '0xtest...';
    this.testMode = testMode;
    
    console.log(`[ContextPilot] Initialized with URL: ${apiUrl}, Test Mode: ${testMode}`);
  }

  async connect(): Promise<boolean> {
    try {
      console.log(`[ContextPilot] Attempting to connect to: ${this.client.defaults.baseURL}`);
      
      // Add retry logic for Cloud Run cold starts
      let lastError: any;
      for (let attempt = 1; attempt <= 3; attempt++) {
        try {
          console.log(`[ContextPilot] Connection attempt ${attempt}/3...`);
          const response = await this.client.get('/health', {
            validateStatus: (status) => status === 200,
            // Add explicit HTTP adapter config for Node.js compatibility
            httpAgent: undefined,
            httpsAgent: undefined,
          });
          console.log(`[ContextPilot] Connect response: ${response.status}`, response.data);
          this.connected = response.status === 200;
          return this.connected;
        } catch (err) {
          lastError = err;
          console.warn(`[ContextPilot] Attempt ${attempt} failed:`, err);
          if (attempt < 3) {
            await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2s before retry
          }
        }
      }
      
      throw lastError;
    } catch (error) {
      console.error(`[ContextPilot] Connection failed after 3 attempts:`, error);
      if (error instanceof Error) {
        console.error(`[ContextPilot] Error message: ${error.message}`);
      }
      this.connected = false;
      throw new Error(`Failed to connect to ContextPilot API: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  disconnect() {
    this.connected = false;
  }

  isConnected(): boolean {
    return this.connected;
  }

  async getProposals(): Promise<ChangeProposal[]> {
    console.log('[ContextPilot] getProposals() called');
    try {
      // Fetch proposals for both the user and system-generated proposals
      const [userProposals, systemProposals] = await Promise.all([
        // User's proposals
        this.client.get('/proposals/list', {
          params: { 
            workspace_id: this.workspaceId || 'contextpilot',
            user_id: this.userId,
            status: 'pending'
          }
        }).catch(err => {
          console.warn('[ContextPilot] Failed to fetch user proposals:', err);
          return { data: { proposals: [] } };
        }),
        // System proposals (from agents)
        this.client.get('/proposals/list', {
          params: { 
            workspace_id: this.workspaceId || 'contextpilot',
            user_id: 'system',
            status: 'pending'
          }
        }).catch(err => {
          console.warn('[ContextPilot] Failed to fetch system proposals:', err);
          return { data: { proposals: [] } };
        })
      ]);

      // Combine and deduplicate
      const userArr = Array.isArray(userProposals.data) ? userProposals.data : userProposals.data?.proposals || [];
      const systemArr = Array.isArray(systemProposals.data) ? systemProposals.data : systemProposals.data?.proposals || [];
      
      const combined = [...userArr, ...systemArr];
      const uniqueMap = new Map();
      combined.forEach(p => uniqueMap.set(p.id, p));
      const arr = Array.from(uniqueMap.values());
      
      console.log(`[ContextPilot] Fetched ${arr.length} proposals (${userArr.length} user + ${systemArr.length} system):`, 
        arr.map((p: any) => ({ id: p.id, title: p.title, user_id: p.user_id })));
      return arr;
    } catch (error) {
      console.error('Failed to fetch proposals:', error);
      return []; // Return empty array instead of throwing to avoid breaking the UI
    }
  }

  async getProposal(proposalId: string): Promise<ChangeProposal | null> {
    try {
      console.log(`[ContextPilot] getProposal called with ID: ${proposalId}`);
      const response = await this.client.get(`/proposals/${proposalId}`, {
        params: { workspace_id: 'contextpilot' }
      });
      console.log(`[ContextPilot] getProposal response status: ${response.status}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch proposal:', error);
      return null;
    }
  }

  async approveProposal(proposalId: string): Promise<{ ok: boolean; autoCommitted: boolean; commitHash?: string }> {
    try {
      // Check if we're in CLOUD mode by checking health
      const health = await this.getHealth();
      const isCloudMode = health.config?.storage_mode === 'cloud';
      
      let response;
      if (isCloudMode) {
        // CLOUD mode: Send ProposalApprovalRequest object
        response = await this.client.post(`/proposals/${proposalId}/approve`, {
          user_id: this.userId,
          comment: 'Approved via VS Code extension'
        });
      } else {
        // LOCAL mode: Send without body (only proposal_id in URL)
        response = await this.client.post(`/proposals/${proposalId}/approve`, null, {
          params: { workspace_id: this.workspaceId || 'contextpilot' }
        });
      }
      
      const autoCommitted = !!response.data?.auto_committed;
      const commitHash = response.data?.commit_hash;
      return { ok: true, autoCommitted, commitHash };
    } catch (error) {
      console.error('Failed to approve proposal:', error);
      return { ok: false, autoCommitted: false };
    }
  }

  async rejectProposal(proposalId: string, reason?: string): Promise<boolean> {
    try {
      // Check if we're in CLOUD mode by checking health
      const health = await this.getHealth();
      const isCloudMode = health.config?.storage_mode === 'cloud';
      
      if (isCloudMode) {
        // CLOUD mode: Send ProposalRejectionRequest object
        await this.client.post(`/proposals/${proposalId}/reject`, {
          user_id: this.userId,
          reason: reason || 'Rejected by user'
        });
      } else {
        // LOCAL mode: Send reason as string directly with workspace param
        await this.client.post(`/proposals/${proposalId}/reject`, reason || 'Rejected by user', {
          params: { workspace_id: this.workspaceId || 'contextpilot' }
        });
      }
      
      return true;
    } catch (error) {
      console.error('Failed to reject proposal:', error);
      return false;
    }
  }

  async getHealth() {
    try {
      const response = await this.client.get('/health');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch health:', error);
      return { 
        status: 'error', 
        version: '2.0.0',
        agents: [],
        config: null
      };
    }
  }

  async getBalance(): Promise<Balance> {
    try {
      // Use real rewards endpoint
      const response = await this.client.get(`/rewards/balance/${this.userId}`);
      console.log(`[ContextPilot] Balance: ${response.data.total_points} CPT`);
      return {
        balance: response.data.total_points,
        total_earned: response.data.total_points,
        pending_rewards: response.data.pending_blockchain,
        weeklyStreak: 0, // Not available in API yet
        achievements: [], // Not available in API yet
        rank: 999 // Not available in API yet
      };
    } catch (error) {
      console.error('Failed to fetch balance:', error);
      return { balance: 0, total_earned: 0, pending_rewards: 0 };
    }
  }

  async getLeaderboard(): Promise<any[]> {
    try {
      const response = await this.client.get('/rewards/leaderboard');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch leaderboard:', error);
      return [];
    }
  }

  async getAgentsStatus(): Promise<AgentStatus[]> {
    try {
      const response = await this.client.get('/agents/status', {
        params: { workspace_id: this.workspaceId || 'contextpilot' }
      });
      return response.data;
    } catch (error) {
      console.error('Failed to fetch agents status:', error);
      return [];
    }
  }

  async resetAgentMetrics(agentId?: string): Promise<boolean> {
    try {
      if (agentId) {
        // Reset specific agent
        await this.client.post(`/agents/${agentId}/reset-metrics`, null, {
          params: { workspace_id: this.workspaceId || 'contextpilot' }
        });
      } else {
        // Reset all agents
        await this.client.post('/agents/reset-metrics', null, {
          params: { workspace_id: this.workspaceId || 'contextpilot' }
        });
      }
      return true;
    } catch (error) {
      console.error('Failed to reset agent metrics:', error);
      return false;
    }
  }

  async askCoach(question: string): Promise<string> {
    try {
      const response = await this.client.post('/agents/coach/ask', {
        user_id: this.userId,
        question,
      });
      return response.data.answer;
    } catch (error) {
      console.error('Failed to ask coach:', error);
      throw error;
    }
  }

  async commitContext(): Promise<void> {
    try {
      await this.client.post('/context/commit', {
        user_id: this.userId,
        workspace_path: process.cwd(),
      });
    } catch (error) {
      console.error('Failed to commit context:', error);
      throw error;
    }
  }

  async trackChange(): Promise<void> {
    // Debounced change tracking
    // Implementation would track file changes and send to API
  }

  setUserId(userId: string) {
    this.userId = userId;
  }

  setWalletAddress(address: string) {
    this.walletAddress = address;
  }

  // ===== REAL API INTEGRATION (existing endpoints) =====

  async getContextReal(workspaceId: string = 'default'): Promise<any> {
    try {
      const response = await this.client.get('/context', {
        params: { workspace_id: workspaceId }
      });
      console.log('[ContextPilot] Context loaded:', response.data);
      return response.data;
    } catch (error) {
      console.error('Failed to get context:', error);
      return null;
    }
  }

  async commitChangesReal(message: string, agent: string = 'extension', workspaceId: string = 'default'): Promise<boolean> {
    try {
      const response = await this.client.post('/commit', null, {
        params: {
          message,
          agent,
          workspace_id: workspaceId
        }
      });
      
      console.log('[ContextPilot] Commit successful:', response.data);
      return response.status === 200;
    } catch (error) {
      console.error('Failed to commit:', error);
      return false;
    }
  }

  async getCoachTipReal(workspaceId: string = 'default'): Promise<string> {
    try {
      const response = await this.client.get('/coach', {
        params: { workspace_id: workspaceId }
      });
      return response.data.tip || 'No tips available';
    } catch (error) {
      console.error('Failed to get coach tip:', error);
      return 'Error loading tip';
    }
  }

  async triggerRetrospective(workspaceId: string = 'default', topic?: string): Promise<any> {
    try {
      const response = await this.client.post('/agents/retrospective/trigger', {
        trigger: 'manual',
        trigger_topic: topic,  // The discussion topic for agents
        use_llm: true  // Enable AI-powered insights
      }, {
        params: { workspace_id: workspaceId },
        timeout: 900000 // Allow up to 15 minutes to match backend timeout
      });
      
      console.log('[ContextPilot] Retrospective triggered:', response.data);
      return response.data;
    } catch (error) {
      console.error('Failed to trigger retrospective:', error);
      throw error;
    }
  }

  async getMilestonesReal(workspaceId: string = 'default'): Promise<any[]> {
    try {
      const response = await this.client.get('/context/milestones', {
        params: { workspace_id: workspaceId }
      });
      return response.data.milestones || [];
    } catch (error) {
      console.error('Failed to get milestones:', error);
      return [];
    }
  }

  async getRetrospectiveStatus(workspaceId: string = 'default', since?: string): Promise<{
    latest_retrospective: {
      retrospective_id: string;
      timestamp: string;
      proposal_id?: string;
      has_proposal: boolean;
    } | null;
    latest_proposal: {
      proposal_id: string;
      created_at: string;
      status: string;
      title: string;
    } | null;
    has_new_proposal: boolean;
  }> {
    try {
      const params: any = { workspace_id: workspaceId };
      if (since) {
        params.since = since;
      }
      const response = await this.client.get('/agents/retrospective/status', { params });
      return response.data;
    } catch (error) {
      console.error('Failed to get retrospective status:', error);
      return {
        latest_retrospective: null,
        latest_proposal: null,
        has_new_proposal: false
      };
    }
  }
}

