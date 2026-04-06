#!/bin/bash
# Install SeferFlow Obsidian Plugin

echo "🚀 Installing SeferFlow Obsidian Plugin..."

# Plugin directory
PLUGIN_DIR="./obsidian-plugin"

# Obsidian plugins directory (Linux/Mac)
OBSIDIAN_PLUGINS_DIR="$HOME/.config/obsidian/community-plugins"

# Or macOS (if vault-specific)
if [ -d "$HOME/Library/Application Support/Obsidian" ]; then
    OBSIDIAN_PLUGINS_DIR="$HOME/Library/Application Support/Obsidian/*/*/plugins"
    # Find first matching vault
    for vault in "$HOME/Library/Application Support/Obsidian"/*; do
        if [ -d "$vault/plugins" ]; then
            OBSIDIAN_PLUGINS_DIR="$vault"
            break
        fi
    done
fi

# Create plugins directory if it doesn't exist
mkdir -p "$OBSIDIAN_PLUGINS_DIR"

# Copy plugin files (not the whole folder!)
echo "📦 Copying plugin to $OBSIDIAN_PLUGINS_DIR..."

# Copy main files
cp "$PLUGIN_DIR/main.js" "$OBSIDIAN_PLUGINS_DIR/seferflow"
cp "$PLUGIN_DIR/manifest.json" "$OBSIDIAN_PLUGINS_DIR/seferflow"
cp "$PLUGIN_DIR/styles.css" "$OBSIDIAN_PLUGINS_DIR/seferflow"

# Enable plugin
echo "🔍 Restart Obsidian and check settings:"
echo "  1. Quit Obsidian"
echo "  2. Go to Settings → Community Plugins"
echo "  3. Find 'SeferFlow - Audiobook Player'"
echo "  4. Click 'Enable' and 'Install'"
echo "  5. Restart Obsidian"
echo "  6. Configure plugin in settings"

echo ""
echo "✅ SeferFlow plugin should now appear in installed plugins"
