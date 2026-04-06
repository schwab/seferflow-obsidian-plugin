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

### 1. Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/seferflow-obsidian-plugin.git
cd seferflow-obsidian-plugin
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Load in Obsidian

```bash
cd ~/Library/Application\ Support/Micros...
```

### 4. Enable Plugin

- Open Obsidian Settings → Community Plugins
- Browse for "SeferFlow" plugin
- Enable and configure

---

## 🔐 Setup

### First Time Login

1. **Click "Log In" in plugin**
2. **Enter email and password**
3. **Free tier**: Instant account creation
4. **Premium tier**: Purchase subscription

### Premium Upgrade

1. **Go to Settings → Subscription**
2. **Click "Upgrade to Premium"**
3. **Pay via Stripe/PayPal**
4. **Get unlimited hours + download capability**

### Usage Limits

**Free Account:**
- 4 hours/month playback
- No downloads
- Basic voice selection

**Premium Account:**
- 200 hours/month (effectively unlimited)
- Download audio files
- Priority queue processing
- Cloud sync

---

## 🎵 Creating Playlists

### Automatic Detection

The plugin will automatically scan your vault for:

- **Markdown notes** (`.md` files)
- **PDF documents** (`.pdf` files)
- **Other audio formats** (`.mp3`, `.wav`)

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

### PDF Playlist

For PDFs, you can specify:

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
- **🔊 Volume**: Adjust volume
- **1.0x Speed**: Change playback speed

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
|---------|-----------|---------|
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

Edit `config.json`:

```json
{
  "apiBaseUrl": "http://localhost:8000",
  "voice": "en-US-AriaNeural",
  "speed": 1.0,
  "autoPlay": false,
  "volume": 0.5
}
```

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

---

## 🐛 Troubleshooting

### Issue: "Failed to fetch from API"

1. Check API is running: `http://localhost:8000/health`
2. Verify token is stored: `localStorage.getItem('seferflow_access_token')`
3. Check CORS is enabled in API

### Issue: "Monthly limit reached"

1. Wait for reset (first day of month)
2. Upgrade to premium in Settings
3. Or wait for monthly reset

### Issue: "Audio not playing"

1. Check file path is accessible
2. Verify PDF can be extracted
3. Check sound device is working

---

## 📚 References

- **API Documentation**: [/docs/seferflow-api-reference](../../docs/seferflow-api-reference.md)
- **Usage Tracking**: [/docs/API_USAGE_TRACKING](../../docs/API_USAGE_TRACKING.md)
- **Authentication**: [/docs/JWT_AUTHENTICATION](../../docs/JWT_AUTHENTICATION.md)
- **Inspiration Notes**: [/docs/INSPRATION_NOTES](../../docs/INSPRATION_NOTES.md)

---

## 📄 License

MIT License - See `LICENSE` in repository

---

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Commit changes
4. Open pull request

See [/CONTRIBUTING](../../CONTRIBUTING.md) for guidelines.

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
