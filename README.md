# SeferFlow Obsidian Plugin ⚡📚

An Obsidian plugin that integrates with the SeferFlow API to create intelligent audiobook playlists directly from your Obsidian vault.

**Note**: Inspired by [Obsidian Edge TTS](https://github.com/travisvn/obsidian-edge-tts) but with unique features like **multi-user authentication**, **PDF support**, **usage tracking**, and **premium tiers**.

## 🎯 Features

### 🔐 Authentication & Usage Tracking
- **Free Tier**: Automatic signup with 4 hours/month
- **Premium Login**: Extended playtime + download capabilities
- **JWT Token Management**: Secure local storage
- **Usage Statistics**: Real-time display of remaining hours

### 📝 Playlist Management
- **Note Detection**: Automatically scan your vault for PDF books and markdown notes
- **Voice Selection**: Choose between 4 neural voices (Aria, Guy, Libby, Ryan)
- **Speed Control**: 0.8x - 1.5x playback speeds
- **Ordering**: Reorder playlist items via drag-and-drop

### 🎮 Player Controls
- **Play/Pause**: Standard playback controls
- **Seek**: Skip forward/backward
- **Volume**: Adjust audio volume
- **Playlist Navigation**: Next/Previous items
- **Chapter Jump**: Navigate to specific sections

### 📚 PDF Support 🆕
- **Extract Text**: Extract text from PDF files
- **Chapter Detection**: Split into chapters/sections
- **Progress Tracking**: Track progress per section
- **Resume Playback**: Resume from last position

### 🌐 Multi-device Sync
- **Web Dashboard**: Manage playlists
- **Mobile Ready**: Future mobile app support
- **Cloud Sync**: Premium users get cloud sync

---

## 📦 Installation

### Option 1: Install via Obsidian Community Plugins Browser (Recommended)

1. Open **Obsidian Settings** → **Community Plugins**
2. Click **"Browse"** tab
3. Search for "SeferFlow"
4. Click **"Install"** and **"Enable"**
5. **Restart Obsidian** to complete installation

### Option 2: Install from GitHub

### Option 2: Install from GitHub

```bash
# Clone the plugin repository
git clone https://github.com/schwab/seferflow-obsidian-plugin.git
cd seferflow-obsidian-plugin

# If you want to develop/test locally, install npm dependencies:
npm install

# Copy to your Obsidian plugins folder
mkdir -p ~/.config/obsidian/community-plugins
cp -r seferflow-obsidian-plugin ~/.config/obsidian/community-plugins/

# Enable the plugin:
# Obsidian Settings → Community Plugins → Browse → Search "SeferFlow" → Enable
# Then restart Obsidian to finish installing.
```

### Option 3: Manual Installation

```bash
# Copy the plugin folder from the cloned repository to your Obsidian plugins folder
cp -r seferflow-obsidian-plugin ~/.config/obsidian/community-plugins/

# Or if you installed from a different location, adjust the source path:
cp -r /path/to/seferflow-obsidian-plugin ~/.config/obsidian/community-plugins/

# Enable the plugin:
# Obsidian Settings → Community Plugins → Browse → Search "SeferFlow" → Enable
# Restart Obsidian to complete installation.
```

### 🛠️ Configure the Plugin

1. **Open Obsidian Settings** → **Community Plugins**
2. **Find "SeferFlow" plugin**
3. **Click "Settings"**
4. **Configure options**:
   - **Api Base URL**: `http://localhost:8000` (default)
   - **Voice**: Default AI voice
   - **Speed**: Default playback speed
   - **Auto-play**: Automatically play next item
   - **Volume**: Audio volume
   - **Token Storage**: Path for JWT token

---

## 🔐 Setup

### First Time Login

1. **Click "Log In" in plugin settings**
2. **Enter email and password**
3. **Free tier**: Instant account creation (4 hours/month)
4. **Premium tier**: Purchase subscription for unlimited hours

### Premium Upgrade

1. **Go to Settings → Subscription**
2. **Click "Upgrade to Premium"**
3. **Pay via Stripe/PayPal**
4. **Get unlimited hours + download capability**

### Usage Limits

**Free Account:**
- ✅ 4 hours/month playback
- ❌ No downloads
- ✅ Basic voice selection

**Premium Account:**
- ✅ 200 hours/month (effectively unlimited)
- ✅ Download audio files
- ✅ Priority queue processing
- ✅ Cloud sync

---

## 🎵 Creating Playlists

### Automatic Detection

The plugin will automatically scan your vault for:

- **Markdown notes** (`.md` files)
- **PDF documents** (`.pdf` files)
- **Audio files** (`.mp3`, `.wav`)

### Manual Addition

```javascript
// Add note to playlist
apiClient.createPlaylist([{
  id: note.id,
  title: note.file.name,
  type: 'markdown',
  content: note.raw
}]);
```

### PDF Playlist Configuration

For PDFs, specify chapter ranges:

```javascript
{
  id: pdf.id,
  title: pdf.file.name,
  type: 'pdf',
  chapters: [
    { title: "Ch 1", start_page: 1, end_page: 12 },
    { title: "Ch 2", start_page: 14, end_page: 28 }
  ]
}
```

---

## 🎮 Using the Player

### Basic Controls

- **▶️ Play**: Start playing current item
- **⏸️ Pause**: Pause playback
- **→ Next**: Skip to next item
- **« Prev**: Go back to previous
- **🔊 Volume**: Adjust volume slider
- **1.0x Speed**: Change playback speed dropdown

### Playlists

Create playlists by selecting items:

```javascript
// Define playlist
const playlist = [
  { id: 'note1', title: 'Chapter 1', type: 'markdown' },
  { id: 'pdf1', title: 'Book Title', type: 'pdf' },
];

// Create session
await apiClient.createPlaylist(playlist);
```

---

## 💳 Pricing Tiers

| Feature | Free Tier | Premium |
|---------|-----|----|-----|
| Monthly Hours | 4 hours | Unlimited |
| Play Speed | 0.8x - 1.3x | 0.8x - 1.5x |
| Voices | 4 neural voices | All voices |
| Downloads | ❌ | ✅ |
| Concurrent Sessions | 2 | Unlimited |
| WebSocket Streaming | ✅ | ✅ |
| Cloud Sync | ❌ | ✅ |
| Priority Queue | ❌ | ✅ |

---

## ⚙️ Configuration

### Plugin Settings

Edit `config.json` or use Obsidian settings:

```json
{
  "apiBaseUrl": "http://localhost:8000",
  "voice": "en-US-AriaNeural",
  "speed": 1.0,
  "autoPlay": false,
  "volume": 0.5
}
```

### Plugin Data Storage

The plugin stores:
- **JWT Token**: In Obsidian vault at `.seferflow-token.json`
- **Settings**: In `~/.config/obsidian/community-plugins/seferflow-obsidian-plugin/settings.json`
- **User Data**: In vault `.seferflow-metadata.json`

---

## 🔧 API Integration

### API Client Usage

```javascript
import SeferFlowAPIClient from './api/client';

const api = new SeferFlowAPIClient();

// Create playback session
const session = await api.createPlaylist([
  { type: 'pdf', path: '/path/to/book.pdf' }
]);

// Track usage (for free tier)
await api.trackUsage({
  duration_seconds: 3600,
  session_id: session.id
});

// Check usage before next play
const stats = await api.getUsageStats();
if (stats.remaining_hours === 0) {
  alert('Free tier limit reached');
}
```

---

## 🎨 Customization

### Styling

To customize plugin appearance, edit `styles.css`:

```css
.sf-playlist-container {
  background-color: #242d36;
  color: #f5f5f5;
}

.sf-playlist-item {
  padding: 0.5em 1em;
  border-radius: 3px;
  margin: 2px 0;
}

.sf-play-btn {
  background-color: #3b4c58;
  color: white;
  border: none;
  padding: 0.5em;
  border-radius: 3px;
}
```

### CSS Variables

Customize plugin colors:

```css
:root {
  --sf-primary-color: #007bff;
  --sf-background-dark: #1a1a1a;
  --sf-text-light: #f0f0f0;
}
```

---

## 🐛 Troubleshooting

### Issue: "Failed to fetch from API"

1. Check API is running: `http://localhost:8000/health`
2. Verify token is stored: Check `.seferflow-token.json`
3. Check CORS is enabled in API

### Issue: "Monthly limit reached"

1. Wait for reset (first day of month)
2. Upgrade to premium in Settings
3. Or wait for monthly reset

### Issue: "Audio not playing"

1. Check file path is accessible
2. Verify PDF can be extracted
3. Check sound device is working
4. Ensure audio system is not muted

### Issue: "Token expired"

1. Go to Settings → Log In
2. Enter new email/password
3. New token generated

### Issue: "Plugin not showing in plugin list"

1. Check Obsidian version (v0.15+ required)
2. Restart Obsidian
3. Refresh Community Plugins browser

---

## 📚 References

- **API Documentation**: https://github.com/schwab/SeferFlow/blob/main/docs/seferflow-api-reference.md
- **Usage Tracking**: https://github.com/schwab/SeferFlow/blob/main/docs/API_USAGE_TRACKING.md
- **Authentication**: https://github.com/schwab/SeferFlow/blob/main/docs/JWT_AUTHENTICATION.md
- **Inspiration Notes**: https://github.com/schwab/SeferFlow/blob/main/docs/INSPRATION_NOTES.md

**API Base URL Configuration**:
- Default: `http://localhost:8000`
- Docker: `http://host.docker.internal:8000`
- Production: Change in plugin settings

---

## 🧪 Testing

### Run Plugin Locally

1. Clone this repository
2. Copy to Obsidian plugins folder (Option 2 above)
3. Enable and test

### Check Logs

Plugin logs appear in Obsidian **Settings → Community Plugins**

### Debug Mode

Enable debug mode in plugin settings to see console logs.

---

## 🌐 Multi-User Support

### Free Tier

- ✅ Auto-signup for new users
- ✅ 4 hours playback/month
- ✅ Basic JWT token
- ❌ No downloads

### Premium Tier

- ✅ Unlimited playback (soft 200h limit)
- ✅ Download audio files
- ✅ Priority queue processing
- ✅ Cloud sync across devices
- ✅ Premium support

### User Registration

```bash
# New users register in plugin
# Free tier created automatically
# Premium: Upgrade in Settings → Subscription
```

---

## 📄 License

MIT License - See `LICENSE` in plugin repository

---

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Make your changes
4. Test in Obsidian
5. Commit with clear messages
6. Open pull request

See [/CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

---

## 📝 Version History

**v1.0.0** (2026-04-06)
- 🔐 Initial release
- ✅ Playlist management
- ✅ Usage tracking
- ✅ Voice selection
- ✅ Speed control
- ✅ PDF support
- ✅ Free tier vs Premium tiers

---

## 💝 Support

1. **GitHub Issues**: Report bugs
2. **Feature Requests**: Submit new ideas
3. **Donations**: Support development
4. **Premium**: Upgrade for advanced features

**Support Email**: support@seferflow.example.com

---

## 📞 API Server Setup

The plugin requires a running SeferFlow API server.

### Option 1: Run Locally

```bash
cd /path/to/seferflow
python3 -m venv venv
source venv/bin/activate
pip install -r seferflow-api/requirements.txt
uvicorn seferflow_api.main:app --reload
```

### Option 2: Docker

```bash
cd /path/to/seferflow/seferflow-api
docker-compose up -d
```

### Option 3: Production Deployment

Deploy API server to your production host. Point plugin to API URL:

```
http://your-api-server.com:8000
```

---

## ⚙️ Security

### Token Storage

- **Location**: Obsidian vault (not synced to cloud)
- **Encryption**: JWT tokens with secure signing
- **Expiry**: 24-hour tokens (auto-refresh with login)
- **Permissions**: User-specific rate limits

### Best Practices

1. Never share API token
2. Upgrade to premium for unlimited hours
3. Use password-protected accounts
4. Enable HTTPS in production

---

**Ready to listen? Start playing audiobooks in Obsidian!** 🎧📚
