# 🧠 Cluely - AI Desktop Assistant

Cluely is a cross-platform desktop AI assistant that provides instant, always-available computer and web control through natural language commands.

## ✨ Features

### 🚀 Instant Activation
- Global keyboard shortcut (Cmd+Space on macOS, Ctrl+Space on Windows/Linux)
- Minimal overlay interface that appears over any application
- Quick command input with immediate execution

### 🗣️ Natural Language Commands
- Accept any text command and translate into actions
- Context-aware follow-up queries
- Intelligent command interpretation

### 💻 Full Local Control
- Browse, read, edit, delete, and create files/folders
- Launch and control installed applications
- Search files by name, type, or content
- System information and status monitoring

### 🌐 Web Control
- Live web searches with instant results
- URL browsing and content extraction
- File downloads from web sources
- API interactions with custom endpoints

### ⚡ Script Execution
- Run Python, Bash, PowerShell, JavaScript, and Ruby scripts
- Execute system commands safely
- Automate multi-step tasks

## 🏗️ Architecture

- **Frontend**: Electron-based overlay UI with modern, transparent design
- **Backend**: Python Flask server with modular plugin system
- **Plugins**: Extensible modules for different capabilities
- **Security**: Permission management and action logging

## 🚀 Quick Start

### Prerequisites

- Node.js 16+ and npm
- Python 3.8+ and pip
- macOS 10.15+, Windows 10+, or Linux with X11

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd cluely
   ```

2. **Install Python dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   cd ..
   ```

3. **Install Node.js dependencies**
   ```bash
   npm install
   ```

4. **Start the application**
   ```bash
   npm run dev
   ```

### First Run

1. The app will start and show a system tray icon
2. Press `Cmd+Space` (macOS) or `Ctrl+Space` (Windows/Linux) to activate
3. Type your first command: "help" to see available features
4. Grant necessary permissions when prompted

## 🎯 Example Commands

### File Operations
- "open my documents folder"
- "create a new file called notes.txt"
- "find all PDF files in downloads"
- "delete old screenshots"
- "copy budget.xlsx to desktop"

### App Control
- "launch chrome"
- "switch to vscode"
- "close all terminal windows"
- "open calculator"

### Web Operations
- "google latest tech news"
- "browse github.com"
- "download https://example.com/file.pdf"
- "search web for python tutorials"

### System & Scripts
- "what time is it"
- "show system information"
- "run my backup script"
- "python print('hello world')"

## ⚙️ Configuration

Configuration is stored in `~/.cluely/config.json`. You can modify:

- Keyboard shortcuts
- UI appearance and behavior
- Security settings
- Plugin configurations
- API keys and endpoints

## 🔒 Security Features

- **Permission Management**: Requests only necessary system permissions
- **Action Logging**: Keeps detailed logs of all commands and outcomes
- **Safe Execution**: Validates commands before execution
- **Sandboxed Scripts**: Runs scripts in controlled environments

## 🔧 Development

### Project Structure

```
cluely/
├── src/                    # Electron frontend
│   ├── main.js            # Main process
│   ├── main.html          # Settings window
│   └── overlay.html       # Command overlay
├── backend/               # Python backend
│   ├── main.py           # Flask server
│   ├── core/             # Core functionality
│   ├── plugins/          # Feature plugins
│   └── utils/            # Utilities
├── package.json          # Node.js config
└── README.md            # This file
```

### Adding New Features

1. Create a new plugin in `backend/plugins/`
2. Implement the plugin interface
3. Register the plugin in `core/command_processor.py`
4. Add command patterns and handlers
5. Test thoroughly

### Building for Distribution

```bash
# Build Python backend
npm run build-backend

# Build Electron app
npm run build

# Create installer
npm run package
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙋‍♂️ Support

- **Issues**: Report bugs and request features on GitHub
- **Documentation**: Check the wiki for detailed guides
- **Community**: Join our Discord for help and discussions

## 🗺️ Roadmap

### Upcoming Features
- [ ] Voice command support
- [ ] Custom plugin marketplace
- [ ] Team collaboration features
- [ ] Advanced automation workflows
- [ ] Mobile companion app
- [ ] Cloud sync and backup

### Platform Enhancements
- [ ] Linux Wayland support
- [ ] Windows PowerToys integration
- [ ] macOS Shortcuts integration
- [ ] Chrome extension companion

# How to Start
## For Backend
### cd /Users/romirpatel/apx && pkill -f electron || true; pkill -f backend/main.py || true; sleep 1; npm run dev --silent
## For Frontend, if backend works
### npm run dev 
---

**Made with ❤️ for productivity enthusiasts**
