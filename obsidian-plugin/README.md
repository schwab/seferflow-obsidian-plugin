# SeferFlow Obsidian Plugin

**Install instructions for testing locally:**

1. Open Obsidian
2. Go to Settings → Community Plugins
3. Search for "seferflow-obsidian" or click "Install from GitHub"
4. Clone: `git clone https://github.com/schwab/seferflow-obsidian-plugin.git`
5. Copy the `obsidian-plugin/` folder contents to Obsidian's plugins:

```bash
# Install into Obsidian plugins folder
mkdir -p ~/.config/obsidian/community-plugins
# or on macOS:
mkdir -p ~/Library/Application\ Support/Obsidian/Vault\ Name/plugins

# Copy plugin files (not the folder, just the files):
cp obsidian-plugin/main.js ~/.config/obsidian/community-plugins/seferflow
cp obsidian-plugin/manifest.json ~/.config/obsidian/community-plugins/seferflow
cp obsidian-plugin/styles.css ~/.config/obsidian/community-plugins/seferflow

# Enable plugin in Obsidian Settings
```

**Or install from the browser:**
1. Go to Obsidian Settings → Community Plugins → Browse
2. Search for "SeferFlow"
3. Click Install and Enable
4. Restart Obsidian

---

## Features

- 📚 **Note Detection** - Scan vault for PDFs and markdown notes
- 🎤 **4 Neural Voices** - Choose from Aria, Guy, Libby, Ryan
- ⏯️ **Playback Controls** - Play, pause, seek, volume
- 📊 **Usage Tracking** - Free tier (4h/mo) and Premium
- 📚 **PDF Support** - Extract and read from PDF files

---

## Setup

1. **First-time login:**
   - Click "Log In" in plugin settings
   - Enter email and password
   - Free tier: Auto-signup (4 hours/month)
   - Premium: Subscribe for unlimited hours

2. **Configure:**
   - API Base URL: `http://localhost:8000` (or your API server)
   - Voice: Select from 4 voices
   - Speed: 0.8x - 1.5x

---

## License

MIT License
