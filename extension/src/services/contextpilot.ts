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
      // Force real endpoint for testing
      const response = await this.client.get('/proposals', {
        params: { workspace_id: 'default', status: 'pending' }
      });
      console.log('[ContextPilot] Raw response:', response.data);
      const arr = Array.isArray(response.data) ? response.data : response.data?.proposals || [];
      console.log(`[ContextPilot] Fetched ${arr.length} proposals:`, arr.map((p: any) => ({ id: p.id, title: p.title })));
      return arr;
    } catch (error) {
      console.error('Failed to fetch proposals:', error);
      try {
        const response = await this.client.get('/proposals/mock');
        return response.data;
      } catch {
        return [];
      }
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
      const response = await this.client.post(`/proposals/${proposalId}/approve`);
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
      await this.client.post(`/proposals/${proposalId}/reject`, {
        user_id: this.userId,
        reason: reason || 'Rejected by user',
      });
      return true;
    } catch (error) {
      console.error('Failed to reject proposal:', error);
      return false;
    }
  }

  async getBalance(): Promise<Balance> {
    try {
      // Use mock endpoint if in test mode or if regular endpoint fails
      const endpoint = this.testMode ? '/rewards/balance/mock' : '/rewards/balance';
      const response = await this.client.get(endpoint, {
        params: { user_id: this.userId },
      });
      console.log(`[ContextPilot] Balance: ${response.data.balance} CPT`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch balance:', error);
      // Fallback to mock endpoint
      try {
        const response = await this.client.get('/rewards/balance/mock');
        console.log(`[ContextPilot] Using mock balance (fallback)`);
        return response.data;
      } catch {
        return { balance: 0, total_earned: 0, pending_rewards: 0 };
      }
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
      const response = await this.client.get('/agents/status');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch agents status:', error);
      return [];
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
        trigger: topic || 'manual',
        use_llm: true  // Enable AI-powered insights
      }, {
        params: { workspace_id: workspaceId }
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
}

