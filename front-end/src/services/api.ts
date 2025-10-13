
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface CommitResponse {
  status: string;
  message: string;
}

export interface UpdateCheckpointRequest {
  project_name: string;
  goal: string;
  current_status: string;
  milestones: Array<{
    id?: number;
    title: string;
    status: 'completed' | 'in-progress' | 'pending';
    dueDate: string;
    description: string;
  }>;
}

export interface LLMRequest {
  prompt: string;
}

class ApiService {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  async manualCommit(message?: string, agent?: string): Promise<CommitResponse> {
    const params = new URLSearchParams();
    if (message) params.append('message', message);
    if (agent) params.append('agent', agent);

    return this.request<CommitResponse>(`/commit?${params.toString()}`, {
      method: 'POST',
    });
  }

  async updateCheckpoint(data: UpdateCheckpointRequest): Promise<any> {
    return this.request('/update', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async askLLM(prompt: string): Promise<any> {
    return this.request('/llm', {
      method: 'POST',
      body: JSON.stringify({ prompt }),
    });
  }
}

export const apiService = new ApiService();
