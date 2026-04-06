/**
 * SeferFlow Obsidian Plugin
 * Main entry point
 */

// Plugin initialization
console.log('[SeferFlow] Plugin loaded v1.0.0');

/**
 * Check authentication status
 */
function checkAuthStatus() {
  const container = document.getElementById('sf-settings-container');
  if (!container) return;
  
  const token = localStorage.getItem('seferflow_access_token');
  const user = JSON.parse(localStorage.getItem('seferflow_user') || 'null');
  
  const status = container.querySelector('#sf-login-status');
  
  if (token && user) {
    status.innerHTML = '✅ Logged in';
    displayUsageStats(user);
  } else {
    status.innerHTML = 'Click "Log In" to connect to SeferFlow API';
  }
}

/**
 * Create status panel
 */
function createStatusPanel(container) {
  const status = container.querySelector('#sf-login-status');
  const usage = container.querySelector('#sf-usage-stats');
  
  if (!status || !usage) return;
  
  status.addEventListener('click', () => {});
}

/**
 * Display usage statistics
 */
function displayUsageStats(user) {
  const stats = document.getElementById('sf-usage-stats');
  if (!stats) return;
  
  const tier = user?.tier === 'free' ? 'Free (4h/mo)' : 'Premium (Unlimited)';
  const usedHours = user?.used_hours || 0;
  
  stats.innerHTML = `
    <div style="margin: 10px 0;">
      <strong>Tier:</strong> ${tier}<br/>
      <strong>Used:</strong> ${typeof usedHours === 'number' ? usedHours : 'N/A'} hour(s)
    </div>
  `;
}

/**
 * Initialize plugin when loaded
 */
// Wait for DOM to be ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

function init() {
  const container = document.getElementById('sf-settings-container');
  if (!container) {
    console.log('[SeferFlow] No container found, plugin may not be loaded properly');
    return;
  }
  
  // Check auth status
  checkAuthStatus();
  
  console.log('[SeferFlow] Initialized');
}
