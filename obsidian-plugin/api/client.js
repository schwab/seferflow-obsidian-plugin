/**
 * SeferFlow API Client for Obsidian Plugin
 * Handles all API interactions with the SeferFlow backend
 */

class SeferFlowAPIClient {
  constructor() {
    // API Configuration
    this.baseUrl = 'http://localhost:8000';

    // API paths
    this.authPath = \`${this.baseUrl}/api/v1/auth\`;
    this.playbackPath = \`${this.baseUrl}/api/v1/playback/session\`;
    this.usagePath = \`${this.baseUrl}/api/v1/usage\`;
    this.premiumPath = \`${this.baseUrl}/api/v1/premium\`;
    this.downloadPath = \`${this.baseUrl}/api/v1/download\`;

    // State
    this.token = localStorage.getItem('seferflow_access_token') || null;
    this.user = JSON.parse(localStorage.getItem('seferflow_user') || 'null');

    // Rate limiting for free tier
    this.requestsRemaining = 60;
    this.requestsReset = Date.now() + 60000;
  }

  /**
   * Check if user has API rate limit available
   */
  async checkRateLimit() {
    const now = Date.now();
    
    if (now >= this.requestsReset) {
      // Reset rate limit
      this.requestsRemaining = this.user?.tier === 'premium' 
        ? this.user.premium?.requestsPerHour || 1000
        : this.user.tier === 'free' ? 60 : 100;
      this.requestsReset = now + (this.user.tier === 'premium' 
        ? 3600000 * 60
        : 60000);
      
      return true;
    }
    
    if (this.requestsRemaining > 0) {
      this.requestsRemaining--;
      return true;
    }
    
    const retryAfter = Math.ceil((this.requestsReset - now) / 1000);
    return { 
      allowed: false, 
      retryAfter 
    };
  }

  /**
   * Make authenticated API request
   */
  async fetch(path, options = {}) {
    // Check rate limit
    const rateLimit = await this.checkRateLimit();
    if (!rateLimit.allowed) {
      throw new Error(
        \`Rate limit exceeded. Try again in \${rateLimit.retryAfter} seconds\`
      );
    }

    // Prepare headers
    const headers = {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': \`Bearer \${this.token}\`,
        'User-Agent': \`SeferFlow-Obsidian-Plugin/\${this.pluginVersion}\`,
      },
    };

    // Add body if provided
    if (options.body) {
      headers.body = options.body;
    }

    // Make request
    const response = await fetch(path, options);

    // Handle HTTP status codes
    if (!response.ok) {
      const errorBody = await response.text();
      let error;
      
      try {
        error = JSON.parse(errorBody);
      } catch {
        error = { detail: errorBody };
      }

      // Throw standard errors
      if (response.status === 401) {
        throw new AuthError('Token expired or invalid');
      }
      
      if (response.status === 403) {
        throw new PermissionError(detail);
      }
      
      if (response.status === 429) {
        throw new RateLimitError();
      }

      throw new Error(error.detail || 'Unknown error');
    }

    const data = await response.json();
    return data;
  }

  /**
   * Create playlist with notes and PDFs from user's vault
   */
  async createPlaylist(items) {
    return this.fetch(this.playbackPath, {
      method: 'POST',
      body: JSON.stringify({
        items: items,
        autoPlay: true,
        shuffle: false,
        voice: 'en-US-AriaNeural',
        speed: 1.0,
      }),
    });
  }

  /**
   * Get playlist playback session
   */
  async getPlaybackSession(sessionId) {
    return this.fetch(\`\${this.playbackPath}/\${sessionId}\`, {
      method: 'GET'
    });
  }

  /**
   * Track usage (hours, minutes tracked)
   */
  async trackUsage(usageData) {
    return this.fetch(\`\${this.usagePath}/track\`, {
      method: 'POST',
      body: JSON.stringify(usageData)
    });
  }

  /**
   * Check usage statistics (hours remaining, premium status)
   */
  async getUsageStats() {
    return this.fetch(this.usagePath, {
      method: 'GET'
    });
  }

  /**
   * Check premium user status
   */
  async checkPremium() {
    return this.fetch(this.premiumPath, {
      method: 'GET'
    });
  }

  /**
   * Download audio file from cached URL
   */
  async downloadAudio(audioId) {
    // Requires premium subscription
    if (!this.user?.tier === 'premium') {
      throw new Error('Premium subscription required for downloads');
    }

    return this.fetch(\`\${this.downloadPath}/\${audioId}\`, {
      method: 'GET'
    });
  }

  /**
   * Register new free tier user
   */
  async registerUser(userData) {
    const response = await this.fetch(\`\${this.authPath}/register\`, {
      method: 'POST',
      body: JSON.stringify({
        email: userData.email,
        password: userData.password,
        role: userData.role || 'listener',
      }),
    });

    // Save token and user info
    if (response.token) {
      this.token = response.token;
      this.user = response.user;
      localStorage.setItem('seferflow_access_token', this.token);
      localStorage.setItem('seferflow_user', JSON.stringify(this.user));
    }

    return response;
  }

  /**
   * Login with email/password
   */
  async loginUser(credentials) {
    const response = await this.fetch(\`\${this.authPath}/login\`, {
      method: 'POST',
      body: \${formDataToFormUrlencoded({
        username: credentials.email,
        password: credentials.password,
      })},
    });

    // Save token and user info
    if (response.token) {
      this.token = response.token;
      this.user = response.user;
      localStorage.setItem('seferflow_access_token', this.token);
      localStorage.setItem('seferflow_user', JSON.stringify(this.user));
    }

    return response;
  }

  /**
   * Logout user
   */
  async logout() {
    this.token = null;
    this.user = null;
    localStorage.removeItem('seferflow_access_token');
    localStorage.removeItem('seferflow_user');
    return {
      status: 'success',
      message: 'Logged out successfully',
    };
  }

  /**
   * Get user profile
   */
  async getUserProfile() {
    return this.fetch(\`\${this.authPath}/me\`, {
      method: 'GET',
    });
  }

  /**
   * Check API health
   */
  async checkHealth() {
    return fetch(\`\${this.baseUrl}/api/v1/health\`, {
      method: 'GET',
    });
  }
}

// Export
export default SeferFlowAPIClient;
