import axios, { AxiosInstance } from 'axios';

export interface ChangeProposal {
  id: string;
  agent_id: string;
  title: string;
  description: string;
  proposed_changes: Array<{
    file_path: string;
    change_type: string;
    description: string;
  }>;
  status: 'pending' | 'approved' | 'rejected';
  created_at: string;
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
      timeout: 10000,
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
      const response = await this.client.get('/health');
      this.connected = response.status === 200;
      return this.connected;
    } catch (error) {
      this.connected = false;
      throw new Error('Failed to connect to ContextPilot API');
    }
  }

  disconnect() {
    this.connected = false;
  }

  isConnected(): boolean {
    return this.connected;
  }

  async getProposals(): Promise<ChangeProposal[]> {
    try {
      // Use mock endpoint if in test mode or if regular endpoint fails
      const endpoint = this.testMode ? '/proposals/mock' : '/proposals';
      const response = await this.client.get(endpoint, {
        params: this.testMode ? {} : { user_id: this.userId },
      });
      console.log(`[ContextPilot] Fetched ${response.data.length} proposals`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch proposals:', error);
      // Fallback to mock endpoint
      try {
        const response = await this.client.get('/proposals/mock');
        console.log(`[ContextPilot] Using mock proposals (fallback)`);
        return response.data;
      } catch {
        return [];
      }
    }
  }

  async getProposal(proposalId: string): Promise<ChangeProposal | null> {
    try {
      const response = await this.client.get(`/proposals/${proposalId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch proposal:', error);
      return null;
    }
  }

  async approveProposal(proposalId: string): Promise<boolean> {
    try {
      await this.client.post(`/proposals/${proposalId}/approve`, {
        user_id: this.userId,
      });
      return true;
    } catch (error) {
      console.error('Failed to approve proposal:', error);
      return false;
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

