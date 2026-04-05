# 🤖 JARVIS – Advanced Real-Time AI Personal Assistant (Python)

JARVIS is a powerful **real-time AI personal assistant** built in Python, capable of **answering live queries, controlling Windows OS, executing keyboard commands, opening files, storing memory, and performing system automation** — inspired by Iron Man's JARVIS.

This project is designed for **automation, speed, extensibility, and real-world usage**.

---

## 🚀 Core Features

✅ **Real-Time Voice Interaction**
- Gemini Realtime API powered voice responses
- Activate / Deactivate with voice commands
- Sleep mode — JARVIS stays silent until activated
- Noise cancellation via LiveKit BVC plugin

✅ **Windows System Control**
- Open / close applications (Chrome, Notepad, VS Code, WhatsApp Web, YouTube)
- Shutdown, restart, sleep, lock screen
- Battery info, Wi-Fi, Bluetooth status

✅ **Keyboard & Mouse Automation**
- Execute keyboard shortcuts (Ctrl+S, Alt+F4, etc.)
- Auto typing, key press, hotkey combos
- Mouse move, click, scroll, swipe gestures
- Volume control (up, down, mute)

✅ **File & Folder Management**
- Open files and folders from any path
- Fuzzy search files by name from D:/ drive
- Play media files (MP3, MP4, MKV, etc.)

✅ **Persistent Memory System**
- Store user preferences and notes
- Remember past conversations
- Context-aware responses across sessions
- Memory saved locally as JSON

✅ **Live Internet Search**
- Google Custom Search API integration
- Real-time weather via OpenWeather API
- Current date & time tool

✅ **User Authentication**
- Register / Login with email + password
- SHA-256 password hashing
- Session persistence via JSON

✅ **Animated UI**
- Pygame-based GIF display window (jarvis_ui.py)
- Login screen (jarvis_login_ui.py)

---

## 🧠 Use Cases

- Personal desktop voice assistant
- Windows automation & productivity
- AI-powered system controller
- Smart command executor
- Learning & experimentation with LiveKit + Gemini

---

## 🛠️ Tech Stack

- **Python 3.11**
- **LiveKit Agents v1.5.1** — voice pipeline
- **Google Gemini Realtime API** — LLM + voice
- **AsyncIO** — non-blocking execution
- **Pygame** — animated UI
- **pynput / pyautogui** — keyboard & mouse control
- **fuzzywuzzy** — fuzzy file search
- **dotenv** — environment config

---

## 📂 Project Structure

```
Personal-Assistant-main/
│
├── brain.py                  # Core agent — LiveKit + Gemini voice pipeline
├── jarvis_prompt.py          # Behavior prompts (sleep/active mode, personality)
├── jarvis_auth.py            # User register / login / session
├── jarvis_ui.py              # Pygame animated GIF window
├── jarvis_login_ui.py        # Login screen UI
├── jarvis_search.py          # Google Search + datetime tools
├── jarvis_get_whether.py     # OpenWeather API tool
├── jarvis_file_opner.py      # File search & open from D:/ drive
├── jarvis_music.py           # Music play / pause tools
├── jarvis_reasoning.py       # LangChain ReAct agent for complex tasks
├── Jarvis_window_CTRL.py     # Windows OS control tools
├── keyboard_mouse_CTRL.py    # Keyboard & mouse automation
├── memory_store.py           # Persistent conversation memory
├── memory_loop.py            # Background memory save loop
├── republic_day.py           # Republic Day animation (standalone)
├── jarvis_session.json       # Current login session (auto-generated)
├── jarvis_users.json         # Registered users (auto-generated)
├── requirements.txt          # Python dependencies
├── .env                      # API keys (never commit this!)
└── Untitled_design.gif       # JARVIS UI animation file
```

---

## ⚙️ Setup

### 1. Clone & create virtual environment
```bash
git clone <repo-url>
cd Personal-Assistant-main
python -m venv .venv
.venv\Scripts\activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Create `.env` file in project root
```env
LIVEKIT_URL=wss://your-livekit-url.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
GOOGLE_API_KEY=your_gemini_api_key
GOOGLE_SEARCH_API_KEY=your_google_search_api_key
SEARCH_ENGINE_ID=your_custom_search_engine_id
OPENWEATHER_API_KEY=your_openweather_api_key
```

### 4. Run JARVIS
```bash
python brain.py console
```

> ⚠️ Always use `console` mode for local testing without LiveKit Playground.
> Use `dev` mode only when connecting via LiveKit cloud room.

---

## 🎙️ Voice Activation

JARVIS starts in **sleep mode** by default — it listens but does not respond until activated.

**To activate:**
> "activate jarvis" / "hey jarvis" / "jarvis on" / "on pannu" / "jarvis wake up"

**To deactivate:**
> "deactivate jarvis" / "bye jarvis" / "jarvis off" / "sleep pannu"

---

## 🌐 Language Support

JARVIS auto-detects the language you speak and responds accordingly:

| Language | Example Input | Example Response |
|----------|--------------|-----------------|
| Tanglish | "Chrome open pannu" | "Seri panda sir, Chrome open pannuren!" |
| Tamil | "Neram enna?" | "Ippo mani 3:45 aagirukkku sir." |
| English | "What time is it?" | "It is 3:45 PM, panda." |

> No Hindi words used — ever.

---


## 📝 Notes

- `jarvis_session.json` and `jarvis_users.json` are auto-generated — do not delete them while logged in.
- Memory is stored in `conversations/jarvis_user_memory.json` — auto-created on first run.
- `agent.py` is currently unused — `brain.py` is the main entry point.
- Never commit `.env` to GitHub — add it to `.gitignore`.

---

## 🔮 Planned Upgrades

- [ ] Always-listening wake word detection (offline)
- [ ] GUI mic indicator in Pygame window
- [ ] Background service / system tray mode
- [ ] Multi-user session switching
- [ ] WhatsApp message via native app (not web)