/**
 * SeferFlow Obsidian Plugin - API Client
 * Handles all API interactions with the SeferFlow backend
 */

import { APIError, AuthError } from '../../types/errors';

export interface PlaylistItem {
  id: string;
  title: string;
  type: 'note' | 'pdf' | 'audio';
  path: string;
  status: string;
}

export interface UsageStats {
  user_id: string;
  tier: 'free' | 'premium';
  monthly_limit_hours: number;
  used_hours: number;
  remaining_hours: number;
  usage_percent: number;
  reset_date: string;
  sessions_played: number;
}

export interface PlaybackSession {
  session_id: string;
  current_position: number;
  is_playing: boolean;
  item: PlaylistItem;
}

/**
 * SeferFlow API Client for Obsidian Plugin
 */
export class SeferFlowAPIClient {
  private baseUrl: string;
  private token: string | null;
  private user: UserData | null;
  private tokenExpiry: Date | null;
  private rateLimitQueueLimit: number;

  constructor(baseUrl: string = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
    // Load from local storage if available
    const storedToken = localStorage.getItem('seferflow_access_token');
    const storedUser = localStorage.getItem('seferflow_user');
    
    if (storedToken && storedUser) {
      try {
        this.token = storedToken;
        this.user = JSON.parse(storedUser);
        
        // Check token expiry
        const expiry = parseInt(this.user?.expires_at || '0');
        if (expiry > 0) {
          this.tokenExpiry = new Date(expiry);
        }
      } catch (e) {
        this.logout();
      }
    }

    this.rateLimitQueueLimit = 60; // requests per minute
  }

  /**
   * Check if token is valid
   */
  isTokenValid(): boolean {
    if (!this.tokenExpiry) return true;
    return this.tokenExpiry >= new Date();
  }

  /**
   * Refresh token if needed
   */
  async refreshAuth(): Promise<boolean> {
    if (!this.token || !this.isTokenValid()) {
      try {
        const response = await this.loginUser({
          email: this.user?.email || '',
          password: '',
        });
        
        if (response.token) {
          this.token = response.token;
          this.user = response.user;
          this.tokenExpiry = new Date();
          this.tokenExpiry.setMinutes(this.tokenExpiry.getMinutes() + 180);
          this.saveCredentials();
          return true;
        }
        return false;
      } catch (error) {
        console.error('Auth refresh failed', error);
        return false;
      }
    }
    return true;
  }

  /**
   * Save credentials to local storage
   */
  private saveCredentials(): void {
    if (this.user) {
      localStorage.setItem('seferflow_access_token', this.token!);
      localStorage.setItem('seferflow_user', JSON.stringify(this.user));
    }
  }

  /**
   * Logout user
   */
  async logout(): Promise<void> {
    this.token = null;
    this.user = null;
    this.tokenExpiry = null;
    localStorage.removeItem('seferflow_access_token');
    localStorage.removeItem('seferflow_user');
  }

  /**
   * Create playback session
   */
  async createPlaybackSession(playlistItems: PlaylistItem[]): Promise<PlaybackSession> {
    return this.request('POST', '/api/v1/playback/session', {
      items: playlistItems,
      autoPlay: true,
      shuffle: false,
      voice: 'en-US-AriaNeural',
      speed: 1.0,
      buffer_size: 6,
    });
  }

  /**
   * Get playback session status
   */
  async getPlaybackSession(sessionId: string): Promise<any> {
    return this.request('GET', `/api/v1/playback/session/${sessionId}`);
  }

  /**
   * Pause playback
   */
  async pausePlayback(sessionId: string, pause: boolean): Promise<void> {
    await this.request('PATCH', `/api/v1/playback/session/${sessionId}/pause`, {
      pause,
    });
  }

  /**
   * Seek playback
   */
  async seekPlayback(sessionId: string, offset: number, direction: 'forward' | 'backward' = 'forward'): Promise<void> {
    await this.request('PATCH', `/api/v1/playback/session/${sessionId}/seek`, {
      offset,
      direction,
    });
  }

  /**
   * Stop playback
   */
  async stopPlayback(sessionId: string): Promise<void> {
    await this.request('DELETE', `/api/v1/playback/session/${sessionId}`);
  }

  /**
   * Track usage duration
   */
  async trackUsage(durationSeconds: number): Promise<void> {
    await this.request('POST', '/api/v1/usage/track', {
      duration_seconds: durationSeconds,
      session_id: '',
    });
  }

  /**
   * Get usage statistics
   */
  async getUsageStats(): Promise<UsageStats> {
    return this.request('GET', '/api/v1/usage/stats');
  }

  /**
   * Check premium status
   */
  async checkPremiumStatus(): Promise<boolean> {
    return this.request('GET', '/api/v1/premium/status').then(
      response => response.is_premium
    );
  }

  /**
   * Download audio (premium only)
   */
  async downloadAudio(audioId: string): Promise<Blob> {
    return this.fetch(`/api/v1/download/${audioId}`, {
      headers: {
        'Authorization': `Bearer ${this.tokens!}`,
      },
    }).then(r => r.blob());
  }

  /**
   * Register new user
   */
  async registerUser(email: string, password: string): Promise<any> {
    return this.request('POST', '/api/v1/auth/register', {
      email,
      password,
      role: 'listener',
    });
  }

  /**
   * Login
   */
  async loginUser(credentials: { email: string; password: string }): Promise<any> {
    return this.request('POST', '/api/v1/auth/login', {
      email: credentials.email,
      password: credentials.password,
    });
  }

  /**
   * Get current user info
   */
  async getCurrentUserInfo(): Promise<any> {
    return this.request('GET', '/api/v1/auth/me');
  }

  /**
   * Upload session note
   */
  async uploadNote(noteContent: string, path: string): Promise<any> {
    return this.request('POST', '/api/v1/upload/note', {
      content: noteContent,
      path: path,
    });
  }

  /**
   * Make authenticated API request
   */
  private async request<T>(method: string, path: string, body?: any): Promise<T> {
    // Check rate limiting
    await this.checkRateLimit();

    // Check authentication
    if (!this.isTokenValid()) {
      await this.refreshAuth();
    }

    // Make request
    const response = await fetch(this.baseUrl + path, {
      method,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.token!}`,
      },
      body: body ? JSON.stringify(body) : undefined,
    });

    // Handle errors
    if (!response.ok) {
      const error = await this.handleError(response);
      throw error;
    }

    const data = await response.json();
    return data as T;
  }

  /**
   * Fetch request (for downloads)
   */
  private async fetch(path: string, options?: RequestInit): Promise<Response> {
    const response = await fetch(this.baseUrl + path, {
      headers: {
        'Authorization': `Bearer ${this.token!}`,
      },
      ...options,
    });
    return response;
  }

  /**
   * Handle HTTP errors
   */
  private async handleError(response: Response): Promise<APIError> {
    const errorBody = await response.text();
    let error;

    try {
      error = JSON.parse(errorBody);
    } catch {
      error = { detail: errorBody };
    }

    // Handle specific status codes
    switch (response.status) {
      case 401:
        throw new AuthError('Token expired or invalid');
      case 403:
        throw new AuthError('Permission denied');
      case 429:
        const retryAfterMinutes = Math.ceil((response.headers.get('Retry-After') || '60') / 60);
        throw new Error(
          `Rate limit exceeded. Try again in ${retryAfterMinutes} minutes`
        );
      default:
        throw new Error(error.detail || 'Unknown error');
    }
  }

  /**
   * Check rate limiting
   */
  private async checkRateLimit(): Promise<void> {
    const now = Date.now();
    const oneMinuteAgo = now - 60000;

    // Check if we've made too many requests
    if (oneMinuteAgo < now) {
      const requests = this.user?.monthly_requests || 0;
      const limit = this.user?.tier === 'premium'
        ? 1000
        : this.user?.tier === 'free'
        ? 60
        : 30;

      if (requests >= limit) {
        throw new Error('Too many requests. Please try again later.');
      }
    }
  }

  /**
   * Get token
   */
  get tokens(): string | null {
    return this.token;
  }

  /**
   * Get user data
   */
  getUser() {
    return this.user;
  }
}
