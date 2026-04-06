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
  console.log('[SeferFlow] Plugin activated v1.0.0');
  
  try {
    // Get API from Obsidian
    const app = window.app || window.PluginAPI.app || window;
    
    // Check if user is logged in
    checkAuthStatus();
    
    // Create UI components and add to sidebar
    createSettingsComponent();
    createUsageStatsComponent();
    
    // Initialize API client
    apiClient = SeferFlowAPIClient(app.vault);
    
    console.log('[SeferFlow] API client initialized');
  } catch (error) {
    console.error('[SeferFlow] Activation error:', error);
  }
}

/**
 * Plugin deactivation
 */
function deactivate() {
  console.log('[SeferFlow] Plugin deactivated');
}

/**
 * Check authentication status
 */
function checkAuthStatus() {
  const token = localStorage.getItem('seferflow_access_token');
  const user = JSON.parse(localStorage.getItem('seferflow_user') || 'null');
  
  console.log('[SeferFlow] Auth status:', { token: !!token, user: !!user });
}

/**
 * Create settings panel
 */
function createSettingsComponent() {
  try {
    const container = document.createElement('div');
    container.id = 'sf-settings-container';
    container.innerHTML = `
      <h3>🔐 Account</h3>
      <div style="margin-bottom: 10px;">
        <button id="sf-login" class="sf-btn">Log In</button>
        <button id="sf-logout" class="sf-btn sf-btn-outline">Log Out</button>
      </div>
      
      <div id="sf-login-status" class="sf-login-status">
        Click "Log In" to connect to SeferFlow API
      </div>
      
      <form id="sf-auth-form" style="display:none;margin: 15px 0;">
        <div style="margin-bottom: 10px;">
          <label for="sf-email">Email Address:</label><br/>
          <input type="email" id="sf-email" name="email" placeholder="you@example.com" style="width: 100%; max-width: 300px; padding: 4px;">
        </div>
        <div style="margin-bottom: 10px;">
          <label for="sf-password">Password:</label><br/>
          <input type="password" id="sf-password" name="password" placeholder="••••••••" style="width: 100%; max-width: 300px; padding: 4px;">
        </div>
        <div style="margin-bottom: 10px;">
          <button type="submit" id="sf-submit" class="sf-btn">Submit</button>
        </div>
      </form>
      
      <div class="sf-usage-panel">
        <h4>📊 Usage Statistics</h4>
        <div id="sf-usage-stats" class="sf-usage-stats">Not logged in</div>
      </div>
      
      <div style="margin-top: 20px; font-size: 12px; color: #666;">
        <p>API: ${apiClient.baseUrl}</p>
        <p>Author: seferflow example</p>
      </div>
    `;
    
    // Add to Obsidian sidebar using the plugin API
    if (app.plugins && app.plugins.addView) {
      try {
        app.plugins.addView('seferflow-sidebar', {
          component: container,
          preserveState: true
        }, 'settings');
      } catch (e) {
        console.log('[SeferFlow] view add not supported, using direct append:', e);
      
      }
    } else {
      // If view API not available, append to sidebar directly
      app.plugins?.find(plugin => plugin.id === 'seferflow')?.app?.addView('seferflow-sidebar', container);
    }
    
    // Set up event listeners
    setupEventListeners(container);
    
    console.log('[SeferFlow] Settings panel created');
  } catch (error) {
    console.error('[SeferFlow] Settings creation error:', error);
  }
}

/**
 * Create usage stats component
 */
function createUsageStatsComponent() {
  // Already created in settings component
}

/**
 * Setup event listeners
 */
function setupEventListeners(container) {
  // Login button
  const loginButton = container.querySelector('#sf-login');
  if (loginButton) {
    loginButton.addEventListener('click', (event) => {
      const form = container.querySelector('#sf-auth-form');
      const status = container.querySelector('#sf-login-status');
      
      if (form && !form.style.display || form.style.display === 'none') {
        form.style.display = 'block';
      }
    });
  }
  
  // Logout button
  const logoutButton = container.querySelector('#sf-logout');
  if (logoutButton) {
    logoutButton.addEventListener('click', (event) => {
      localStorage.removeItem('seferflow_access_token');
      localStorage.removeItem('seferflow_user');
      const status = container.querySelector('#sf-login-status');
      status.innerHTML = 'Logged out. Click "Log In" to reconnect.';
      checkAuthStatus();
    });
  }
  
  // Form submission
  const authForm = container.querySelector('#sf-auth-form');
  const submitButton = container.querySelector('#sf-submit');
  if (authForm && submitButton) {
    authForm.addEventListener('submit', handleAuthFormSubmit);
  }
}

/**
 * Handle auth form submit
 */
async function handleAuthFormSubmit(event) {
  event.preventDefault();
  event.stopPropagation();
  
  const formData = new FormData(event.target);
  const email = formData.get('email');
  const password = formData.get('password');
  
  if (!email || password.length < 4) {
    alert('Please enter a valid email and password (min 4 chars)');
    return;
  }
  
  try {
    const response = await apiClient.loginUser({ email, password });
    
    if (response?.access_token) {
      localStorage.setItem('seferflow_access_token', response.access_token);
      localStorage.setItem('seferflow_user', JSON.stringify(response.user));
      
      const status = container.querySelector('#sf-login-status');
      status.innerHTML = '✅ Logged in successfully!';
      status.classList.add('sf-success');
      
      container.querySelector('#sf-auth-form').style.display = 'none';
      
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
  try {
    const stats = document.getElementById('sf-usage-stats');
    
    if (!stats) {
      console.log('[SeferFlow] No stats element found');
      return;
    }
    
    const tier = user?.tier === 'free' ? 'Free (4h/mo)' : 'Premium (Unlimited)';
    const usedHours = user?.used_hours || 0;
    const limitHours = user?.monthly_limit_hours || (user?.tier === 'free' ? 4 : '∞');
    
    stats.innerHTML = `
      <div style="margin: 10px 0;">
        <strong>Tier:</strong> ${tier}<br/>
        <strong>Used:</strong> ${typeof usedHours === 'number' ? usedHours : 'N/A'} hour(s)<br/>
        <strong>Limit:</strong> ${typeof limitHours === 'number' ? limitHours : 'Unlimited'}
      </div>
    `;
  } catch (error) {
    console.error('[SeferFlow] Display stats error:', error);
  }
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
    
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('[SeferFlow] API call error:', error);
      throw error;
    }
  }
}

/**
 * Initialize plugin
 */
console.log('[SeferFlow] Plugin loaded');
