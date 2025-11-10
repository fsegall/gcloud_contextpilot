/* eslint-disable @typescript-eslint/naming-convention */
import axios, { AxiosInstance } from 'axios';

export interface ProposalDiff {
  format: 'unified' | 'git-patch';
  content: string;
}

export interface ProposedChange {
  filePath: string;
  changeType: 'create' | 'update' | 'delete';
  description: string;
  before?: string;
  after?: string;
  diff?: string;
}

export interface ChangeProposal {
  id: string;
  agentId: string;
  workspaceId: string;
  title: string;
  description: string;
  diff: ProposalDiff;
  proposedChanges: Array<ProposedChange>;
  status: 'pending' | 'approved' | 'rejected';
  createdAt: string;
  aiReview?: {
    model: string;
    verdict: 'approve' | 'reject' | 'needsChanges';
    reasoning: string;
    concerns: string[];
    suggestions: string[];
  };
}

export interface Balance {
  balance: number;
  totalEarned: number;
  pendingRewards: number;
  weeklyStreak?: number;
  achievements?: any[];
  rank?: number;
}

export interface AgentStatus {
  agentId: string;
  name: string;
  status: 'active' | 'idle' | 'error';
  lastActivity: string;
}

// Helper functions to convert API responses (snake_case) to camelCase
function convertProposedChange(change: any): ProposedChange {
  return {
    filePath: change.file_path || change.filePath,
    changeType: change.change_type || change.changeType,
    description: change.description,
    before: change.before,
    after: change.after,
    diff: change.diff
  };
}

function convertChangeProposal(proposal: any): ChangeProposal {
  return {
    id: proposal.id,
    agentId: proposal.agent_id || proposal.agentId,
    workspaceId: proposal.workspace_id || proposal.workspaceId,
    title: proposal.title,
    description: proposal.description,
    diff: proposal.diff,
    proposedChanges: (proposal.proposed_changes || proposal.proposedChanges || []).map(convertProposedChange),
    status: proposal.status,
    createdAt: proposal.created_at || proposal.createdAt,
    aiReview: proposal.ai_review || proposal.aiReview ? {
      model: (proposal.ai_review || proposal.aiReview).model,
      verdict: (proposal.ai_review || proposal.aiReview).verdict === 'needs_changes' ? 'needsChanges' : (proposal.ai_review || proposal.aiReview).verdict,
      reasoning: (proposal.ai_review || proposal.aiReview).reasoning,
      concerns: (proposal.ai_review || proposal.aiReview).concerns || [],
      suggestions: (proposal.ai_review || proposal.aiReview).suggestions || []
    } : undefined
  };
}

function convertAgentStatus(agent: any): AgentStatus {
  return {
    agentId: agent.agent_id || agent.agentId,
    name: agent.name,
    status: agent.status,
    lastActivity: agent.last_activity || agent.lastActivity
  };
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
        // eslint-disable-next-line @typescript-eslint/naming-convention
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
          // eslint-disable-next-line @typescript-eslint/naming-convention
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
          // eslint-disable-next-line @typescript-eslint/naming-convention
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
      
      // Convert API responses (snake_case) to camelCase
      const converted = arr.map((p: any) => convertChangeProposal(p));
      
      console.log(`[ContextPilot] Fetched ${converted.length} proposals (${userArr.length} user + ${systemArr.length} system):`, 
        converted.map((p: ChangeProposal) => ({ id: p.id, title: p.title, agentId: p.agentId })));
      return converted;
    } catch (error) {
      console.error('Failed to fetch proposals:', error);
      return []; // Return empty array instead of throwing to avoid breaking the UI
    }
  }

  async getProposal(proposalId: string): Promise<ChangeProposal | null> {
    try {
      console.log(`[ContextPilot] getProposal called with ID: ${proposalId}`);
      const response = await this.client.get(`/proposals/${proposalId}`, {
        // eslint-disable-next-line @typescript-eslint/naming-convention
        params: { workspace_id: 'contextpilot' }
      });
      console.log(`[ContextPilot] getProposal response status: ${response.status}`);
      // Convert API response (snake_case) to camelCase
      return convertChangeProposal(response.data);
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
        // eslint-disable-next-line @typescript-eslint/naming-convention
        response = await this.client.post(`/proposals/${proposalId}/approve`, {
          user_id: this.userId,
          comment: 'Approved via VS Code extension'
        });
      } else {
        // LOCAL mode: Send without body (only proposal_id in URL)
        response = await this.client.post(`/proposals/${proposalId}/approve`, null, {
          // eslint-disable-next-line @typescript-eslint/naming-convention
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
        // eslint-disable-next-line @typescript-eslint/naming-convention
        await this.client.post(`/proposals/${proposalId}/reject`, {
          user_id: this.userId,
          reason: reason || 'Rejected by user'
        });
      } else {
        // LOCAL mode: Send reason as string directly with workspace param
        await this.client.post(`/proposals/${proposalId}/reject`, reason || 'Rejected by user', {
          // eslint-disable-next-line @typescript-eslint/naming-convention
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
    const response = await this.client.get(`/rewards/balance/${this.userId}`);
    const totalPoints = response.data?.total_points ?? 0;
    const pendingRewards = response.data?.pending_blockchain ?? 0;
    console.log(`[ContextPilot] Balance: ${totalPoints} CPT`);
    return {
      balance: totalPoints,
      totalEarned: totalPoints,
      pendingRewards: pendingRewards,
      weeklyStreak: 0,
      achievements: [],
      rank: 999
    };
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
        // eslint-disable-next-line @typescript-eslint/naming-convention
        params: { workspace_id: this.workspaceId || 'contextpilot' }
      });
      // Convert API responses (snake_case) to camelCase
      const agents = Array.isArray(response.data) ? response.data : [];
      return agents.map((agent: any) => convertAgentStatus(agent));
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
          // eslint-disable-next-line @typescript-eslint/naming-convention
          params: { workspace_id: this.workspaceId || 'contextpilot' }
        });
      } else {
        // Reset all agents
        await this.client.post('/agents/reset-metrics', null, {
          // eslint-disable-next-line @typescript-eslint/naming-convention
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
      // eslint-disable-next-line @typescript-eslint/naming-convention
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
      // eslint-disable-next-line @typescript-eslint/naming-convention
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
        // eslint-disable-next-line @typescript-eslint/naming-convention
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
        // eslint-disable-next-line @typescript-eslint/naming-convention
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
        // eslint-disable-next-line @typescript-eslint/naming-convention
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
      // eslint-disable-next-line @typescript-eslint/naming-convention
      const response = await this.client.post('/agents/retrospective/trigger', {
        trigger: 'manual',
        trigger_topic: topic,  // The discussion topic for agents
        use_llm: true  // Enable AI-powered insights
      }, {
        // eslint-disable-next-line @typescript-eslint/naming-convention
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
        // eslint-disable-next-line @typescript-eslint/naming-convention
        params: { workspace_id: workspaceId }
      });
      return response.data.milestones || [];
    } catch (error) {
      console.error('Failed to get milestones:', error);
      return [];
    }
  }

  async getRetrospectiveStatus(workspaceId: string = 'default', since?: string): Promise<{
    latestRetrospective: {
      retrospectiveId: string;
      timestamp: string;
      proposalId?: string;
      hasProposal: boolean;
    } | null;
    latestProposal: {
      proposalId: string;
      createdAt: string;
      status: string;
      title: string;
    } | null;
    hasNewProposal: boolean;
  }> {
    try {
      // eslint-disable-next-line @typescript-eslint/naming-convention
      const params: any = { workspace_id: workspaceId };
      if (since) {
        params.since = since;
      }
      const response = await this.client.get('/agents/retrospective/status', { params });
      const data = response.data;
      // Convert snake_case from API to camelCase
      return {
        latestRetrospective: data.latest_retrospective ? {
          retrospectiveId: data.latest_retrospective.retrospective_id,
          timestamp: data.latest_retrospective.timestamp,
          proposalId: data.latest_retrospective.proposal_id,
          hasProposal: data.latest_retrospective.has_proposal
        } : null,
        latestProposal: data.latest_proposal ? {
          proposalId: data.latest_proposal.proposal_id,
          createdAt: data.latest_proposal.created_at,
          status: data.latest_proposal.status,
          title: data.latest_proposal.title
        } : null,
        hasNewProposal: data.has_new_proposal || false
      };
    } catch (error) {
      console.error('Failed to get retrospective status:', error);
      return {
        latestRetrospective: null,
        latestProposal: null,
        hasNewProposal: false
      };
    }
  }

  async updateGitHubRepo(githubRepo: string): Promise<{ status: string; message: string; githubRepo?: string }> {
    try {
      // eslint-disable-next-line @typescript-eslint/naming-convention
      const response = await this.client.post('/admin/config/github-repo', { github_repo: githubRepo });
      const data = response.data;
      return {
        status: data.status,
        message: data.message,
        githubRepo: data.github_repo
      };
    } catch (error: any) {
      console.error('[ContextPilot] Error updating GitHub repo config:', error);
      throw new Error(error.response?.data?.detail || error.message || 'Failed to update GitHub repository configuration');
    }
  }
}

