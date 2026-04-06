/**
 * SeferFlow Obsidian Plugin
 * Main entry point
 */

// Plugin metadata
const plugin = {
  id: 'seferflow',
  name: 'SeferFlow - Audiobook Player',
  manifest: require('./manifest.json')
};

// API client instance
let apiClient = null;

// Plugin container elements
const container = {
  playList: null,
  playerControls: null,
  settings: null,
  usageStats: null
};

/**
 * Plugin activation
 */
function activate() {
  console.log(`[SeferFlow] Activated v1.0.0`);
  
  // Check if user is logged in
  checkAuthStatus();
  
  // Create UI components
  createPlayListComponent();
  createPlayerControls();
  createSettingsComponent();
  createUsageStatsComponent();
  
  // Register API client
  apiClient = SeferFlowAPIClient();
  
  // Set event listeners
  setupEventListeners();
}

/**
 * Plugin deactivation
 */
function deactivate() {
  console.log('[SeferFlow] Deactivated');
}

/**
 * Check authentication status
 */
function checkAuthStatus() {
  const token = localStorage.getItem('seferflow_access_token');
  const user = JSON.parse(localStorage.getItem('seferflow_user') || 'null');
  
  if (token && user) {
    // User is logged in
    displayUsageStats(user);
  }
}

/**
 * Create play list component
 */
function createPlayListComponent() {
  const container = DOM.createDiv('sf-playlist-container');
  container.classList.add('plugin-container');
  
  // Header
  const header = DOM.createDiv('sf-playlist-header');
  header.innerHTML = '📚 My Playlist';
  
  // Note/Note list
  const items = [];
  const obsidian = window.PluginAPI.app.vault;
  
  obsidian.vault.getAllLoadedFiles().forEach(async file => {
    if (file instanceof obsidian.TFile) {
      const content = await obsidian.vault.cachedRead(file);
      const note = {
        id: file.id,
        title: file.name,
        type: file.mimeType === 'text/x-markdown' ? 'markdown' : 'pdf',
        content: content
      };
      
      items.push(note);
    }
  });
  
  // Render list
  items.forEach(item => {
    const element = DOM.createDiv('sf-playlist-item');
    element.innerHTML = `
      <div class="sf-item-content">
        <span class="sf-item-title">${item.title}</span>
        <span class="sf-item-type">
          ${item.type === 'markdown' ? '📄 Note' : '📚 PDF'}
        </span>
      </div>
      <button class="sf-play-btn">▶️ Play</button>
    `;
    
    element.querySelector('.sf-play-btn').addEventListener('click', async () => {
      await playAudio(item);
    });
    
    container.appendChild(element);
  });
  
  return {
    header,
    items: container.querySelectorAll('.sf-playlist-item'),
    list: container
  };
}

/**
 * Create player controls
 */
function createPlayerControls() {
  const controls = `
    <div class="sf-player-controls">
      <button id="sf-play-pause" class="sf-control-btn">
        ▶️
      </button>
      <button id="sf-next" class="sf-control-btn">
        Next →
      </button>
      <button id="sf-prev" class="sf-control-btn">
        ← Prev
      </button>
      <span class="sf-info">
        <span class="sf-volume">🔊</span>
        <span class="sf-speed">1.0x</span>
        <span class="sf-voice">Aria</span>
      </span>
    </div>
  `;
  
  return DOM.createDiv(controls);
}

/**
 * Create settings component
 */
function createSettingsComponent() {
  const settings = `
    <div class="sf-settings-panel">
      <h3>🔐 Account</h3>
      <button id="sf-login" class="sf-btn">
        Log In
      </button>
      <button id="sf-logout" class="sf-btn sf-btn-outline">
        Log Out
      </button>
      
      <div id="sf-settings-form" class="sf-form" style="display:none;">
        <div class="sf-form-group">
          <label>Email Address</label>
          <input type="email" name="email" placeholder="you@example.com" />
        </div>
        <div class="sf-form-group">
          <label>Password</label>
          <input type="password" name="password" placeholder="••••••••" />
        </div>
        <button id="sf-submit-form" class="sf-btn">
          Submit
        </button>
      </div>
    </div>
  `;
  
  return DOM.createDiv(settings);
}

/**
 * Create usage stats component
 */
function createUsageStatsComponent() {
  const stats = `
    <div class="sf-usage-panel">
      <h4>📊 Usage Statistics</h4>
      <div id="sf-usage-stats" class="sf-usage-stats"></div>
    </div>
  `;
  
  return DOM.createDiv(stats);
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
  // Play/Pause toggle
  window.PLUGIN_API?.obsidian?.addEventRef(window.PLUGIN_API?.obsidian).ref.set(
    'play-pause',
    async () => {
      const session = await apiClient.getCurrentSession();
      if (session) {
        await playAudio(session);
      }
    }
  );
  
  // Next track
  window.PLUGIN_API?.obsidian?.addEventRef('skip-next');
}

/**
 * Play audio from note/PDF
 */
async function playAudio(item) {
  try {
    await createPlaybackSession(item);
  } catch (error) {
    console.error('Error playing audio:', error);
  }
}

/**
 * Create new playback session
 */
async function createPlaybackSession(item) {
  if (!apiClient) {
    return;
  }
  
  await fetch(`${apiClient.baseUrl}/api/v1/playback/session`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('seferflow_access_token')}`,
      'X-Requested-With': 'X'
    },
    body: JSON.stringify({
      pdf_path: item.type === 'pdf' ? item.path : '',
      chapter: item.title,
      voice: 'en-US-AriaNeural',
      speed: 1.0,
      buffer_size: 6
    })
  });
}

/**
 * Display usage statistics
 */
function displayUsageStats(user) {
  const remainingHours = user.monthly_limit_hours - user.used_hours;
  
  // Calculate usage percentage
  const usagePercent = (user.used_hours / user.monthly_limit_hours) * 100;
  
  // Display in settings
  document.getElementById('sf-usage-stats').innerHTML = `
    <div class="sf-usage-item">
      <span class="sf-usage-label">Tier:</span>
      <span class="sf-usage-value">${user.tier === 'free' ? 'Free' : 'Premium'}</span>
    </div>
    <div class="sf-usage-item">
      <span class="sf-usage-label">Used:</span>
      <span class="sf-usage-value">${user.used_hours} / ${user.monthly_limit_hours} hours</span>
    </div>
    <div class="sf-usage-item">
      <span class="sf-usage-label">Remaining:</span>
      <span class="sf-usage-value">
        ${remainingHours} hours 
        (${(100 - usagePercent).toFixed(0)}%)
      </span>
    </div>
    <div class="sf-usage-item">
      <span class="sf-usage-label">Sessions:</span>
      <span class="sf-usage-value">${user.sessions_played || 0}</span>
    </div>
  `;
  
  // If monthly limit is reached, disable play buttons
  if (remainingHours <= 0 && user.tier === 'free') {
    alert('Monthly usage limit reached. Please wait for reset on ' + 
          new Date(user.reset_date).toLocaleDateString());
    return;
  }
}

/**
 * Submit login form
 */
function submitLoginForm(event) {
  const formData = new FormData(event.target);
  
  const email = formData.get('email');
  const password = formData.get('password');
  
  apiClient.loginUser({
    email,
    password
  }).then(response => {
    alert('Logged in successfully!');
    displayUsageStats(response.user);
  });
}

/**
 * Submit registration form
 */
function submitRegisterForm(event) {
  const formData = new FormData(event.target);
  
  const email = formData.get('email');
  const password = formData.get('password');
  
  apiClient.registerUser({
    email,
    password,
    role: 'listener'
  }).then(response => {
    alert('Account created successfully! You are now logged in.');
    displayUsageStats(response.user);
  });
}

/**
 * Handle form submissions
 */
function handleFormSubmission(event) {
  if (event.target.id === 'sf-login') {
    const form = event.target.closest('.sf-settings-form');
    if (form && form.style.display !== 'block') {
      form.style.display = 'block';
      
      const loginBtn = event.target;
      loginBtn.innerText = 'Logging in...';
    }
  }
  
  // Handle form submission
  event.preventDefault();
  const btn = event.target.closest('.sf-btn')?.parentElement?.closest('button')?.querySelector('button');
  submitLoginForm?.(event);
}

/**
 * Setup form submissions
 */
function setupFormSubmissions() {
  const forms = document.querySelectorAll('.sf-settings-form');
  forms.forEach((form, index) => {
    const email = form.querySelector('input[type="email"]');
    const password = form.querySelector('input[type="password"]');
    const loginBtn = form.closest('.sf-settings-form')?.querySelector('.sf-btn');
    
    if (email && password && loginBtn) {
      email.addEventListener('input', () => {
        loginBtn.innerText = email.value ? 'Log in' : 'Log in';
      });
      
      password.addEventListener('input', () => {
        loginBtn.innerText = password.value ? 'Log in' : 'Log in';
      });
    }
  });
}

// Initialize plugin on activation
on.activate = activate;
on.deactivate = deactivate;
on.update = (options) => {
  console.log('[SeferFlow] Updated', options?.version);
};

on.autoSave = true; // Save to file on every change
on.excludeFromAutosave = false;
