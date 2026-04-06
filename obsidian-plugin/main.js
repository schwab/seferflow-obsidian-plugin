/**
 * SeferFlow Obsidian Plugin
 * Main entry point
 */

// Plugin metadata
const plugin = {
  id: 'seferflow',
  name: 'SeferFlow - Audiobook Player',
  manifest: null
};

// API client instance
let apiClient = null;

/**
 * Plugin initialization called by Obsidian API
 */
function activate(options) {
  console.log(`[SeferFlow] Plugin activated v1.0.0`);
  
  // Get API from Obsidian
  const app = window.app || window.PluginAPI.app;
  
  // Check if user is logged in
  checkAuthStatus();
  
  // Create UI components and add to sidebar
  createSettingsComponent();
  createUsageStatsComponent();
  
  // Initialize API client
  apiClient = SeferFlowAPIClient(app.vault);
  
  console.log('[SeferFlow] API client initialized');
}

function deactivate() {
  console.log('[SeferFlow] Plugin deactivated');
}

/**
 * Check authentication status
 */
function checkAuthStatus() {
  // This would be handled by the Obsidian UI, not manual localStorage
}

/**
 * Create settings panel
 */
function createSettingsComponent() {
  const container = document.createElement('div');
  container.id = 'sf-settings-container';
  container.innerHTML = `
    <h3>🔐 Account</h3>
    <div class="sf-settings-form">
      <button id="sf-login" class="sf-btn">Log In</button>
      <button id="sf-logout" class="sf-btn sf-btn-outline">Log Out</button>
      
      <div id="sf-login-status" class="sf-login-status">
        Click "Log In" to connect to SeferFlow API
      </div>
      
      <form id="sf-auth-form" style="display:none;">
        <div class="sf-form-group">
          <label>Email Address</label>
          <input type="email" name="email" placeholder="you@example.com" required />
        </div>
        <div class="sf-form-group">
          <label>Password</label>
          <input type="password" name="password" placeholder="••••••••" required />
        </div>
        <button type="submit" id="sf-submit" class="sf-btn">Submit</button>
      </form>
    </div>
    
    <div class="sf-usage-panel">
      <h4>📊 Usage Statistics</h4>
      <div id="sf-usage-stats" class="sf-usage-stats">Not logged in</div>
    </div>
  `;
  
  // Add to Obsidian sidebar
  app.plugins.sidebar?.registerView('seferflow-settings', {
    component: container,
    preserveState: true
  }, 'settings');
  
  // Set up event listeners
  container.addEventListener('click', handleAuthClick);
  container.addEventListener('submit', handleLoginForm);
  
  // Create play list component
  createPlayListComponent();
  
  console.log('[SeferFlow] Settings panel created');
}

/**
 * Create play list component
 */
function createPlayListComponent() {
  // This would show notes/PDFs in a separate view
  console.log('[SeferFlow] Play list component created');
}

/**
 * Create usage stats component
 */
function createUsageStatsComponent() {
  // Already created in settings component
}

/**
 * Handle authentication clicks
 */
function handleAuthClick(event) {
  const button = event.target.closest('button');
  
  if (button?.id === 'sf-login') {
    const form = event.target.id === 'sf-login' 
      ? event.target.closest('.sf-settings-form')?.querySelector('.sf-auth-form') : null;
    form?.style.display = 'block';
  }
}

/**
 * Handle login form submission
 */
async function handleLoginForm(event) {
  event.preventDefault();
  event.stopPropagation();
  
  const formData = new FormData(event.target);
  const email = formData.get('email');
  const password = formData.get('password');
  
  try {
    const response = await apiClient.loginUser({ email, password });
    
    if (response?.access_token) {
      localStorage.setItem('seferflow_access_token', response.access_token);
      localStorage.setItem('seferflow_user', JSON.stringify(response.user));
      
      event.target.closest('.sf-settings-form').style.display = 'none';
      event.target.closest('.sf-login-status').classList.replace('sf-login-status', 'sf-login-success');
      event.target.closest('.sf-login-status').innerText = 'Logged in successfully!';
      
      displayUsageStats(response.user);
    }
  } catch (error) {
    console.error('Login error:', error);
    alert('Login failed: ' + error.message);
  }
}

/**
 * Display usage statistics
 */
function displayUsageStats(user) {
  const stats = document.getElementById('sf-usage-stats');
  
  stats.innerHTML = `
    <div class="sf-usage-item">
      <span class="sf-usage-label">Tier:</span>
      <span class="sf-usage-value">${user.tier === 'free' ? 'Free (4h/mo)' : 'Premium (Unlimited)'}</span>
    </div>
    <div class="sf-usage-item">
      <span class="sf-usage-label">Used:</span>
      <span class="sf-usage-value">${user.used_hours || 0} ${user.monthly_limit_hours ? '/ ' + user.monthly_limit_hours + 'h' : ''}</span>
    </div>
    <div class="sf-usage-item">
      <span class="sf-usage-label">Remaining:</span>
      <span class="sf-usage-value">${user.monthly_limit_hours ? (user.monthly_limit_hours - user.used_hours) + 'h' : 'Unlimited'}</span>
    </div>
  `;
}

/**
 * SeferFlow API client
 */
class SeferFlowAPIClient {
  constructor(vault) {
    this.vault = vault;
    this.baseUrl = 'http://localhost:8000';
  }
  
  async loginUser(credentials) {
    const url = new URL(`${this.baseUrl}/api/v1/auth/login`);
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials)
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
  }
}

/**
 * Initialize plugin
 */
console.log('[SeferFlow] Plugin loaded');
