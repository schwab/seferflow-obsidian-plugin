/**
 * SeferFlow Obsidian Plugin - Main Entry Point
 */

import { Plugin, Workspace, Editor, MarkdownView, TFile } from 'obsidian';
import { SeferFlowAPIClient, SeferFlowAPIClientConstructor } from '../api/client';

/**
 * Main SeferFlow Plugin
 */
export default class SeferFlowPlugin extends Plugin {
  private api: SeferFlowAPIClient | null = null;
  private workspace: Workspace;
  private activeSession: PlaybackSession | null = null;
  private note: MarkdownView | null = null;
  private editor: Editor | null = null;

  async onload() {
    console.log('[SeferFlow] Plugin loaded');

    this.workspace = this.app.workspace;
    this.api = new SeferFlowAPIClientConstructor();

    this.addCommand({
      id: 'play-note',
      name: 'Start playing current note',
      callback: async (data) => {
        await this.playCurrentFile(data.editor);
      },
    });

    this.addCommand({
      id: 'pause-playback',
      name: 'Pause/unpause playback',
      callback: async (data) => {},
    });

    this.addCommand({
      id: 'next-track',
      name: 'Next track',
      callback: async (data) => {
        if (this.api) {
          await this.api.nextTrack();
        }
      },
    });

    // Add tab button
    this.addTabButton(
      '🎵',
      'SeferFlow',
      () => this.addTab('TabView', {
        position: this.workspace.getTabState(this.workspace?.getTabPosition(this) || 0)
      })
    );

    // Add settings tab
    this.addSettingTab(new SeferFlowSettingTab(this.app, this));

    // Register events
    this.registerDomEvent(document, 'keydown', (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        this.hideControls();
      }
    });

    // Open floating UI
    this.addRibbonIcon('🎵', 'Play audiobook', () => {
      this.showControls();
    });

    this.app.vault.on('modify', this.onModify);
    this.app.vault.on('create', this.onCreate);
    this.app.vault.on('delete', this.onDelete);

    console.log('[SeferFlow] Plugin loaded successfully');
  }

  onunload() {
    console.log('[SeferFlow] Plugin unloaded');
    this.api?.logout();
  }

  /**
   * Play current file
   */
  async playCurrentFile(editor: Editor): Promise<void> {
    const leaf = this.workspace.activeLeaf;
    if (!leaf) return;

    const note = leaf.view as MarkdownView;
    const file = note.file as TFile;

    if (!(file instanceof TFile)) return;

    // Create playlist item
    const item: PlaylistItem = {
      id: file.id,
      title: file.basename,
      type: 'note',
      path: file.path,
      status: 'unplayed',
    };

    // Create playlist and play
    if (this.api) {
      const playlist = [item];
      await this.api.createPlaybackSession(playlist);
      this.activeSession = await this.api.getCurrentSession();
    }

    console.log('[SeferFlow] Started playback:', file.basename);
  }

  /**
   * Show/hide controls
   */
  showControls() {
    // TODO: Show floating UI
  }

  hideControls() {
    // TODO: Hide floating UI
  }

  /**
   * Handle file modification
   */
  onModify(file: TFile): void {
    // Handle file changes
  }

  /**
   * Handle new file creation
   */
  onCreate(file: TFile): void {
    // Handle new files
  }

  /**
   * Handle file deletion
   */
  onDelete(file: TFile): void {
    // Handle deleted files
  }

  /**
   * Get playback session
   */
  async getCurrentSession(): Promise<PlaybackSession> {
    if (!this.api) throw new Error('Not logged in');

    const session = await this.api.getPlaybackSession('current');
    this.activeSession = session;
    return session;
  }

  /**
   * Get current user
   */
  async getCurrentUser(): Promise<UserData> {
    if (!this.api) throw new Error('Not logged in');

    const user = await this.api.getCurrentUser();
    return user;
  }
}
