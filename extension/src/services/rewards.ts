/**
 * ContextPilot Rewards System (Offchain)
 * 
 * Manages CPT tokens, achievements, and gamification
 * Future: Migrate to blockchain (Polygon/Base)
 */

export interface UserReward {
  userId: string;
  cptBalance: number;
  totalEarned: number;
  achievements: Achievement[];
  rank: number;
  weeklyStreak: number;
  lastActivity: string;
}

export interface Achievement {
  id: string;
  name: string;
  description: string;
  icon: string;
  earnedAt: string;
  cptReward: number;
}

export interface LeaderboardEntry {
  userId: string;
  username: string;
  cptBalance: number;
  rank: number;
  avatar?: string;
}

export class RewardsService {
  private storageKey = 'contextpilot_rewards';
  
  constructor() {}

  private getStorageItem(key: string): string | null {
    // For now, use a simple in-memory storage
    // Future: Use VSCode's Memento API or file system
    return this.memoryStorage.get(key) || null;
  }

  private setStorageItem(key: string, value: string): void {
    // For now, use a simple in-memory storage
    // Future: Use VSCode's Memento API or file system
    this.memoryStorage.set(key, value);
  }

  private memoryStorage = new Map<string, string>();

  async getUserReward(userId: string): Promise<UserReward> {
    const stored = this.getStorageItem(`${this.storageKey}_${userId}`);
    if (stored) {
      return JSON.parse(stored);
    }
    
    // Default new user
    return {
      userId,
      cptBalance: 100, // Starting bonus
      totalEarned: 100,
      achievements: [],
      rank: 999,
      weeklyStreak: 0,
      lastActivity: new Date().toISOString()
    };
  }

  async addCPT(userId: string, amount: number, reason: string): Promise<UserReward> {
    const user = await this.getUserReward(userId);
    user.cptBalance += amount;
    user.totalEarned += amount;
    user.lastActivity = new Date().toISOString();
    
    // Check for achievements
    await this.checkAchievements(user, reason);
    
    // Save
    this.setStorageItem(`${this.storageKey}_${userId}`, JSON.stringify(user));
    
    return user;
  }

  async checkAchievements(user: UserReward, reason: string): Promise<void> {
    const newAchievements: Achievement[] = [];

    // First proposal approval
    if (reason === 'approve_proposal' && user.totalEarned >= 110) {
      if (!user.achievements.find(a => a.id === 'first_approval')) {
        newAchievements.push({
          id: 'first_approval',
          name: 'First Approval',
          description: 'Approved your first proposal',
          icon: '✓',
          earnedAt: new Date().toISOString(),
          cptReward: 0
        });
        user.cptBalance += 25;
        user.totalEarned += 25;
      }
    }

    // Documentation master
    if (reason === 'create_docs' && user.totalEarned >= 150) {
      if (!user.achievements.find(a => a.id === 'doc_master')) {
        newAchievements.push({
          id: 'doc_master',
          name: 'Documentation Master',
          description: 'Created comprehensive documentation',
          icon: '📚',
          earnedAt: new Date().toISOString(),
          cptReward: 0
        });
        user.cptBalance += 50;
        user.totalEarned += 50;
      }
    }

    // Daily streak
    if (this.isNewDay(user.lastActivity)) {
      user.weeklyStreak++;
      if (user.weeklyStreak === 7) {
        newAchievements.push({
          id: 'week_warrior',
          name: 'Week Warrior',
          description: '7-day activity streak',
          icon: '🔥',
          earnedAt: new Date().toISOString(),
          cptReward: 100
        });
        user.cptBalance += 100;
        user.totalEarned += 100;
      }
    }

    user.achievements.push(...newAchievements);
  }

  private isNewDay(lastActivity: string): boolean {
    const last = new Date(lastActivity);
    const now = new Date();
    return last.toDateString() !== now.toDateString();
  }

  async getLeaderboard(): Promise<LeaderboardEntry[]> {
    // For now, return mock data
    // Future: Fetch from Firestore
    return [
      { userId: 'user1', username: 'DevMaster', cptBalance: 1250, rank: 1 },
      { userId: 'user2', username: 'CodeNinja', cptBalance: 980, rank: 2 },
      { userId: 'user3', username: 'DocWizard', cptBalance: 750, rank: 3 }
    ];
  }

  // Future: Blockchain migration
  async migrateToBlockchain(userId: string, network: 'polygon' | 'base' | 'arbitrum'): Promise<string> {
    // TODO: Implement blockchain migration
    throw new Error('Blockchain migration not implemented yet');
  }
}
