# SeferFlow Obsidian Plugin - Getting Started ⚡📚

## 🎯 What This Plugin Does

**SeferFlow Obsidian Plugin** turns your Obsidian vault into an audiobook player!

- 📚 **Browse your notes and PDFs** - Select any note or PDF file
- 🎤 **Listen to them aloud** - High-quality neural voices
- ⏯️ **Create playlists** - Queue multiple items for continuous playback
- ⚡ **Stream audio** - Real-time playback without waiting
- 📊 **Track usage** - See how much time you've spent listening
- 🎯 **Premium features** - Unlimited hours and downloads

**Note**: Inspired by [Obsidian Edge TTS](https://github.com/travisvn/obsidian-edge-tts) but with unique features like PDF support, usage tracking, and premium tiers.

---

## 💻 Prerequisites

### You'll Need

- ✅ **Obsidian v0.15+** (desktop app) - Download: https://obsidian.md
- ✅ **Local network** - API runs locally on your machine
- ✅ **Audio output** - Speakers/headphones connected
- ✅ **Internet** - Only for API access (optional, API can run locally)

### System Requirements

- **Mac**: macOS 10.15+
- **Linux**: Ubuntu 20.04+ with `libffi`
- **Windows**: Windows 10+
- **RAM**: 2GB minimum
- **Disk**: 100MB for plugin files

---

## 📦 Installation

### Option 1: Copy Plugin Files (Easy)

1. **Open Obsidian**
2. Go to **Settings → Appearance**
3. Click **"Show in Finder"** (Mac) or **"Show in File Explorer"** (Windows)
4. Navigate to your Obsidian vault folder
5. **Copy** the `obsidian-plugin/` folder from `/home/mcstar/projects/seferflow/` to your vault
6. Open Obsidian

### Option 2: Use Obsidian's Plugin Browser

1. Open Obsidian
2. Go to **Settings → Community Plugins**
3. Browse for "SeferFlow"
4. Click **Install** and enable it

### Option 3: Download from GitHub

1. Go to https://github.com/YOUR_USERNAME/seferflow-obsidian-plugin
2. Click **Code → Download ZIP**
3. Extract ZIP
4. Copy contents to your Obsidian vault's `Community Plugins` folder

---

## 🔐 Setup

### Step 1: Enable Plugin

1. Open Obsidian
2. Go to **Settings → Community Plugins**
3. Find "SeferFlow" in the list
4. Click **Install** if not already installed
5. Click **Enable**
6. Restart Obsidian

### Step 2: Register Account

1. Open Obsidian plugin **Settings**
2. Click **"Log In"**
3. Enter your email (any email works for now)
4. Create a password
5. Click **"Submit"**

**What happens:**
- Free account created with **4 hours/month** free tier
- JWT token stored locally (not synced to Obsidian)
- You can now play audio!

### Step 3: Configure

**Settings:**
- **Play speed**: 0.8x to 1.5x playback
- **Voice**: Choose from 4 AI voices (Aria, Guy, Libby, Ryan)
- **Auto-play**: Automatically play next item when done

**Premium:**
- Upgrade in plugin settings
- Get **unlimited hours** (200/month soft limit)
- **Download** audio files
- **Priority queue** processing

---

## 🎵 Using the Player

### Quick Start

1. **Open a note** in your Obsidian vault (or any PDF file)
2. **Click the play button** `▶️` in the ribbon
3. Audio starts playing immediately!

### Creating Playlists

**Automatic:**
- The plugin picks up PDFs and notes from your vault
- You can reorder by dragging

**Manual:**
- Right-click file → **Add to queue**
- Reorder by dragging items in queue

### Playback Controls

```
Play/Pause button        ▶️ | ⏸️
Speed dropdown           1.0x (0.8 - 1.5)
Voice selector          Aria, Guy, Libby, Ryan
Volume control          [🔊] 50%
Next track              →
Previous track          ←
```

### Using PDFs

1. **Open PDF** in Obsidian (or add to queue)
2. Plugin extracts text automatically
3. Chapters are detected and queued

### Using Notes

1. **Open markdown note**
2. Plugin picks up text
3. Generate and play audio

---

## 💳 Free Tier vs Premium

### Free Tier (4 hours/month)

| Feature | Status |
|---------|------|
| Monthly Hours | 4 hours |
| Play Speed | 0.8x - 1.3x |
| Voices | 4 AI voices |
| Downloads | No |
| Priority Queue | No |

### Premium (Unlimited)

| Feature | Status |
|---------|------|
| Monthly Hours | Unlimited |
| Play Speed | 0.8x - 1.5x |
| Voices | All voices |
| Downloads | ✅ |
| Priority Queue | ✅ |
| **Upgrade in Settings → Subscription** |

---

## 🎨 Customization

### Modify Styles

Edit `obsidian-plugin/styles.css` to customize:

```css
.sf-playlist-container {
  background-color: #242d36;
  color: #f5f5f5;
}
```

### Change Voice

In settings, choose your preferred voice:
- **Aria** (Female, US)
- **Guy** (Male, US)
- **Libby** (Female, British)
- **Ryan** (Male, British)

### Adjust Speed

```javascript
// Default: 1.0x
speed: 1.0;

// Faster: 1.2x
speed: 1.2;
```

---

## 🔧 API Configuration

The plugin connects to SeferFlow API at:

```
http://localhost:8000
```

**If API not running:**
1. Start API: `cd /home/mcstar/projects/seferflow/seferflow-api && python3 main.py`
2. Or change API endpoint in settings

**HTTPS (Recommended):**
If using HTTPS endpoint, enter in settings:

```
https://your-api-domain.com
```

---

## 🐛 Troubleshooting

### "Failed to connect to API"

**Cause**: API not running

**Solution**:
1. Open **Obsidian Settings → SeferFlow**
2. Check **API Endpoint**
3. Run API: `cd /home/mcstar/projects/seferflow/seferflow-api && python3 main.py`
4. Refresh Obsidian

### "Monthly limit reached"

**Cause**: Reached 4-hour free tier limit

**Solution**:
1. Wait for monthly reset (1st of each month)
2. Upgrade to premium in Settings

### "Audio not playing"

**Cause**: File path issues or missing PDF reader

**Solution**:
1. Install PDF reader
2. Make sure file is accessible from vault

### "Plugin not showing up"

**Cause**: Obsidian version too old

**Solution**:
1. Update Obsidian to latest version
2. Restart Obsidian

---

## 🎯 Tips for Best Experience

### Tips 1: Use Headphones
- Better sound quality
- No sound leaking to others

### Tips 2: Speed Up for Faster Listening
- Set speed to 1.2x or 1.3x
- Still very easy to follow

### Tips 3: Queue Multiple Items
- Select multiple notes/PDFs for continuous playback
- Perfect for reading while working

### Tips 4: Use Premium for Downloads
- Download PDFs
- Generate audio once for offline use
- Transfer to phone/other devices

---

## 📊 Usage Limits Explained

### Free Tier

- **Monthly**: 4 hours total
- **Tracks**: Everything you play
- **Resets**: 1st of month
- **Shows**: In plugin UI

### Premium

- **Monthly**: Effectively unlimited
- **Tracks**: Everything
- **Resets**: Annually (1/4/2027)
- **Downloads**: Unlimited

### When Limit Reached

You'll see:
```
Monthly usage limit reached.
Remaining: 0 hours

Upgrade to premium for unlimited usage.
```

To upgrade: **Settings → Upgrade to Premium**

---

## 📞 Support

### Need Help?

- **GitHub Issues**: https://github.com/seferflow/seferflow-plugin/issues
- **Email**: support@seferflow.example.com
- **Documentation**: `/docs/` folder

### Common Questions

**Q: Can I share my account?**
A: Yes! But each account has its own 4-hour limit.

**Q: Can I listen on my phone?**
A: Currently no, but mobile version coming soon.

**Q: Can I use my own audio files?**
A: Only PDFs for now. Audio files supported in future.

**Q: Why does it say "API not running"?**
A: Need to run API: `python3 main.py`

---

## 🌟 Next Steps

1. **Read the full README** in plugin folder
2. **Enable plugin** in Obsidian
3. **Register account** (free tier)
4. **Play your first note**! 🎵

### Advanced:

- Edit `styles.css` to customize
- Configure `config.json` settings
- Check API documentation in `/docs/`

---

## 📚 Related Documentation

- 🔗 **API Reference**: `/docs/seferflow-api-reference.md`
- 🔗 **Usage Tracking**: `/docs/API_USAGE_TRACKING.md`
- 🔗 **Authentication**: `/docs/JWT_AUTHENTICATION.md`
- 🔗 **Inspiration Notes**: `/docs/INSPRATION_NOTES.md`
- 🔗 **Testing**: `/tests/README.md`

---

## 📜 License

MIT License - See LICENSE in repository

---

## 🗝️ Quick Reference

```bash
# Setup Obsidian plugin
cp -r /home/mcstar/projects/seferflow/obsidian-plugin ~/.config/obsidian

# Enable plugin
cd ~/.config/obsidian
enable-plugin seferflow

# Login
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"SecurePass123"}'

# Start API
cd /home/mcstar/projects/seferflow/seferflow-api
python3 main.py
```

**Status**: ✅ Installation complete  
**Ready**: ⚡ Plugin loaded  
**Listening**: 🎵 Press play!

---

**Version**: 1.0.0  
**Last Updated**: 2026-04-06  
**Author**: Your Name
