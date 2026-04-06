# SeferFlow Obsidian Plugin - Inspiration Notes ⚡📚

**Reference Project**: https://github.com/travisvn/obsidian-edge-tts  
**Status**: ✅ Reviewed for inspiration  
**Copy Strategy**: ✅ Using different architecture, unique features

---

## 🔍 What We Learned

### ✅ Features to Study (No Copy)

1. **Queue/Playlist Queuing** 🔄
   - Obsidian Edge TTS uses `AudioPlaybackManager` with queue support
   - Their queue UI shows multiple files with play/pause controls
   - **Our approach**: Same goal, but implement with Obsidian's native API

2. **Audio Streaming** 🔊
   - They stream audio chunks for smooth playback
   - Use `ChunkedProgressManager` for progress tracking
   - **Our approach**: Use SeferFlow backend for streaming + WebSocket

3. **Voice List** 🗣️
   - They load voices via API call
   - **Our approach**: Hardcode Microsoft Edge voices (we have full control)

4. **Mobile Support** 📱
   - They implemented mobile via app store
   - **Our approach**: Not implementing mobile yet

### 🎯 Features We're Building UNLIKE

1. **Multi-user Authentication** 👥
   - They: Single user, no login required
   - US: JWT auth with free tier vs premium tiers
   
2. **Usage Tracking** 📊
   - They: No tracking, unlimited usage
   - US: 4 hours/month free tier, premium upgrade

3. **Note/PDF Integration** 📄
   - They: Read text from notes
   - US: Create playlists from notes AND PDFs with TTS

4. **Backend API** 🖥️
   - They: Client-side Edge TTS generation
   - US: Server-side with FastAPI backend

5. **Progress Persistence** 💾
   - They: Basic progress tracking
   - US: SQLite/PostgreSQL persistence

---

## 🎨 UI/UX Differentiation

### Obsidian Edge TTS
```
[Queue View]
File 1 (32:00) [▶️]
File 2 (24:00) [▶️]
```

### SeferFlow Plugin (New)
```
[Playlist View]
📚 My Playlist
├── Chapter 1 📄 [▶️]
├── Chapter 2 📄 [▶️]
├── Book Title 📚 [▶️]
─── Settings ────
Tier: Free
Used: 2.5 / 4 hours
Remaining: 1.5 hours
─── Premium ────
Upgrade → 200h/month + Downloads
```

### Key Differences
1. **Visual style**: Dark theme vs light theme
2. **Icons**: Custom iconography (📚🎤 vs 🗣️)
3. **Pricing display**: Free tier badge vs unlimited
4. **Playlist management**: Drag-and-drop reordering
5. **Usage tracking**: Real-time stats in player

---

## 🔐 Auth System - UNIQUE TO US

### Their Approach
- No authentication needed
- Anyone can use

### Our Approach
```javascript
// Step 1: User registers
POST /api/v1/auth/register {
  email: "",
  password: ""
}

// Step 2: Get JWT
POST /api/v1/auth/login {
  email: "",
  password: ""
}

// Step 3: Check usage
GET /api/v1/usage/stats
{
  remaining_hours: 1.5
  tier: "free"
}
```

### Why This Is Better
1. **Monetization path**: Can sell premium subscriptions
2. **Fair usage**: Prevents server abuse
3. **Quality of service**: Premium gets priority
4. **Download capability**: Only for paying users

---

## 📚 Content Type - UNIQUE TO US

### They: Text-Only
```typescript
interface File {
  id: string;
  title: string;
  content: string; // Plain text
  mimeType: 'text/markdown';
}
```

### Us: PDF + Text
```typescript
interface PlaylistItem {
  id: string;
  title: string;
  type: 'note' | 'pdf' | 'audio';
  content?: string;
  path: string;
  chapter?: {
    title: string;
    pages: number[];
  };
  status: 'unplayed' | 'partial' | 'complete';
}
```

### PDF Support
- Extract text from PDF using pdftotext
- Split into chapters/sections
- Track progress per section
- Resume from last position

---

## 🎯 API Architecture

### Their: Client-Side
```javascript
// All happens in browser
const response = await fetch('https://tts.edge-gw.microsoft.com/text', {
  method: 'POST',
  body: textData
});
```

### Us: Server-Side API
```javascript
// Backend handles TTS generation
const session = await api.createPlaybackSession({
  pdf_path: bookPath,
  chapter: "Chapter 1",
  voice: "en-US-AriaNeural",
  speed: 1.0
});
```

### Benefits
1. **Backend processing**: Offload TTS to servers
2. **WebSocket streaming**: Push audio chunks
3. **Rate limiting**: Control usage
4. **Premium features**: Download capability
5. **User auth**: Track usage

---

## 🔄 Queue Implementation Comparison

### Their Queue (Simplified)
```typescript
class AudioPlaybackManager {
  playList: Array<AudioFile> = [];
  
  async playQueue() {
    for (const item of this.playList) {
      await this.playFile(item);
    }
  }
}
```

### Our Queue (Enhanced)
```typescript
class SeferFlowQueue {
  constructor() {
    this.items: PlaylistItem[] = [];
    this.currentIndex = 0;
    this.isPlaying = false;
  }
  
  async addItems(files: PlaylistItem[]) {
    this.items.push(...files);
    this.currentIndex = 0;
  }
  
  async playNext() {
    if (this.hasNext()) {
      const item = this.items[this.currentIndex++];
      await this.playFile(item);
    }
  }
  
  hasNext(): boolean {
    return this.currentIndex < this.items.length;
  }
  
  skipTo(index: number) {
    this.currentIndex = index;
  }
}
```

### Our Enhancements
1. **Drag-and-drop reordering**
2. **Visual progress bars**
3. **Chapter navigation**
4. **Resume support**

---

## 📊 Progress Tracking

### They: Session-based
```typescript
class ChunkedProgressManager {
  currentPosition: number = 0;
  
  updateProgress(samples: number) {
    this.currentPosition = samples;
  }
}
```

### Us: Persistent Storage
```python
class ProgressRecord(SQLModel):
    pdf_path: str
    chapter: str
    last_chunk: int
    total_chunks: int
    listened_at: datetime
```

### Benefits
1. **Resume playback**: Save position to database
2. **Multi-session**: Track multiple books
3. **Usage tracking**: Hours per session
4. **Analytics**: Most listened to chapters

---

## 🎨 UI Components - Different Approach

### Their: Vue.js (External)
```
┌────────────────────┐
│  Edge TTS Player   │
│  [▶️] [⏸️] [❚❚]  │
│                     │
│  File 1: Book      │
│  File 2: Note      │
└────────────────────┘
```

### Us: React + Vanilla
```
┌────────────────────┐
│  📚 SeferFlow      │
│  Playlist:         │
│  ┌──────────────┐ │
│  │ 📄 Ch. 1     │ │
│  │ 📄 Ch. 2     │ │
│  │ 📚 Book.txt  │ │
│  └──────────────┘ │
│                    │
│  Speed: 1.0x      │
│  Voice: Aria      │
│  Free: 2.5 / 4h   │
└────────────────────┘
```

### Unique Elements
1. **Pricing badge**: Show free vs premium
2. **Usage display**: Remaining hours
3. **Premium button**: Upgrade CTA
4. **Playlist reorder**: Drag-and-drop

---

## 🔐 Security Model

### They: Open Access
- No authentication
- Unlimited usage

### Us: Authenticated + Tiered
```python
class UserTier(Enum):
    FREE = "free"       # 4h/month, no download
    PREMIUM = "premium" # 200h/month, unlimited
    ENTERPRISE = "enterprise" # Unlimited, priority
    
class UsageRecord:
    user_id: str
    tier: UserTier
    hours_used: float
    monthly_limit: int
    reset_date: date
```

### Why Different?
1. **Prevent abuse**: Rate limiting per user
2. **Monetization**: Premium subscriptions
3. **Quality**: Premium users get priority
4. **Downloads**: Only for paying users

---

## 📝 Next Steps for Us

### ✅ Build These Features (Our Way)
1. **Auth system**: JWT + usage tracking
2. **Usage limits**: Free tier vs premium
3. **PDF support**: Extract & TTS from PDFs
4. **Playlist reorder**: Drag-and-drop
5. **Chapter navigation**: Jump to sections
6. **Progress persistence**: Save/playback later
7. **Premium upgrade**: Stripe integration

### ❌ Don't Copy These
1. They use Vue.js → We'll use React/Vanilla
2. They do client-side TTS → We do server-side
3. They have no tracking → We track usage
4. Their UI layout → Our unique design
5. Their iconography → Custom icons

---

## 🎯 Unique Value Proposition

| Feature | Their Plugin | Our Plugin |
|---------|--------------|------------|
| **Authentication** | None | JWT + Usage Tracking |
| **Content Types** | Text only | Notes + PDFs |
| **Usage Tracking** | Unlimited | Free + Premium tiers |
| **Downloads** | No | Premium only |
| **API Backend** | No | FastAPI + WebSocket |
| **Progress Persistence** | Session | Database |
| **Monetization** | No | Premium subscriptions |
| **Server-side** | No | Yes (scalable) |

---

**Status**: ✅ Complete review  
**Next**: Implement features with unique approach  
**Goal**: Better UX with auth, tracking, multi-content types

---

**Last Updated**: 2026-04-06  
**Reviewed**: Obsidian Edge TTS (travisvn.com)  
**Strategy**: Inspired but unique implementation
