# 🧠 Apx - AI Desktop Assistant

## Project Overview

**Apx** is a sophisticated cross-platform desktop AI assistant that provides instant access to computer and web control through natural language commands. Built with Electron for the frontend and Python Flask for the backend, it features a modular plugin architecture for extensibility.

## 🌟 Key Features Implemented

### ✅ Core Architecture
- **Electron Frontend**: Modern, transparent overlay UI with global hotkey support
- **Python Backend**: Flask REST API with comprehensive plugin system
- **Cross-Platform**: Supports macOS, Windows, and Linux
- **Security**: Permission management and action logging
- **Configuration**: JSON-based configuration with validation

### ✅ Command Processing
- **Natural Language Understanding**: Advanced NLP processing with intent extraction
- **Pattern Matching**: Regex-based command recognition
- **Context Awareness**: Maintains conversation context for follow-up queries
- **Error Handling**: Graceful error management with user feedback

### ✅ File Management Plugin
- Create, read, update, delete files and folders
- File search by name patterns
- Copy and move operations
- File information and metadata
- Safe path validation

### ✅ Application Control Plugin
- Launch applications by name
- Close running applications
- Switch between applications (platform-specific)
- List running processes
- Cross-platform app name mapping

### ✅ Web Control Plugin
- Web search with instant results
- URL browsing and content extraction
- File downloads from web sources
- Website status checking
- API request capabilities

### ✅ Script Execution Plugin
- Python code and script execution
- Bash/Shell command execution
- Multi-language script support (JS, Ruby, PowerShell)
- Sandboxed execution with timeouts
- Security validation

### ✅ System Information Plugin
- Comprehensive system status
- CPU, memory, and disk usage
- Network interface information
- Running process monitoring
- Battery status (if available)
- Current time and uptime

## 🏗️ Project Structure

```
cluely/
├── src/                          # Electron Frontend
│   ├── main.js                  # Main Electron process
│   ├── main.html               # Settings window
│   └── overlay.html            # Command overlay UI
├── backend/                     # Python Backend
│   ├── main.py                 # Flask server entry point
│   ├── core/                   # Core functionality
│   │   ├── command_processor.py # Command processing engine
│   │   ├── action_logger.py     # Action logging system
│   │   ├── security_manager.py  # Security and permissions
│   │   └── nlp_processor.py     # Natural language processing
│   ├── plugins/                # Feature plugins
│   │   ├── file_manager.py     # File operations
│   │   ├── app_controller.py   # Application control
│   │   ├── web_controller.py   # Web operations
│   │   ├── script_runner.py    # Script execution
│   │   └── system_info.py      # System information
│   └── utils/                  # Utilities
│       └── config.py           # Configuration management
├── .venv/                      # Python virtual environment
├── node_modules/               # Node.js dependencies
├── package.json               # Node.js configuration
├── requirements.txt           # Python dependencies
├── README.md                  # Documentation
├── demo.py                    # Demo script
└── start-cluely.sh           # Launcher script
```

## 🚀 Running the Application

### Option 1: Development Mode
```bash
# Start both backend and frontend
npm run dev
```

### Option 2: Individual Components
```bash
# Backend only
npm run backend

# Frontend only  
npm run electron-dev
```

### Option 3: Using the Launcher
```bash
# Use the convenient launcher script
./start-cluely.sh
```

## 🎯 Command Examples

### File Operations
- `"create file shopping-list.txt"`
- `"open my documents folder"`
- `"search for *.pdf"`
- `"copy budget.xlsx to desktop"`

### Application Control
- `"launch chrome"`
- `"switch to terminal"`
- `"close all safari windows"`

### Web Operations
- `"google latest AI research"`
- `"browse stackoverflow.com"`
- `"download https://example.com/file.pdf"`

### Script Execution
- `"python print('Hello World!')"`
- `"run backup-script.sh"`
- `"bash ls -la"`

### System Information
- `"what time is it"`
- `"show system information"`
- `"list running processes"`

## 🔧 Technical Implementation Details

### Backend Architecture
- **Flask REST API**: Handles HTTP requests from frontend
- **Plugin System**: Modular architecture for easy extension
- **Security Layer**: Validates commands and file paths
- **Action Logging**: Comprehensive audit trail
- **Configuration Management**: JSON-based settings

### Frontend Architecture
- **Electron Main Process**: Manages application lifecycle
- **Overlay Window**: Transparent, always-on-top command interface
- **Global Shortcuts**: System-wide hotkey registration
- **IPC Communication**: Secure communication with backend

### Security Features
- **Path Validation**: Prevents access to sensitive directories
- **Command Sanitization**: Blocks dangerous operations
- **Permission Checks**: Platform-specific permission validation
- **Execution Timeouts**: Prevents runaway processes

## 📊 Current Status

✅ **Completed Features:**
- Core backend infrastructure
- Plugin system with 5 major plugins
- Electron frontend with overlay UI
- Natural language command processing
- Security and logging systems
- Configuration management
- Demo and testing scripts

🔄 **In Progress:**
- Enhanced UI animations and feedback
- Voice command support
- Advanced automation workflows

🎯 **Future Enhancements:**
- Custom plugin marketplace
- Cloud sync and backup
- Team collaboration features
- Mobile companion app
- Advanced AI integration

## 🧪 Testing

The application includes comprehensive testing capabilities:

1. **Backend Health Check**: `curl http://localhost:8888/health`
2. **Demo Script**: `python demo.py` - Tests all major features
3. **Manual Testing**: Use the overlay UI with global hotkey

## 🏆 Achievement Summary

This implementation successfully delivers:

1. **Cross-platform desktop application** with Electron + Python architecture
2. **Global hotkey activation** (Cmd+Space / Ctrl+Space)
3. **Natural language command processing** with advanced NLP
4. **Full computer control** through file, app, and system management
5. **Web automation capabilities** with search, browse, and download
6. **Script execution environment** supporting multiple languages
7. **Security and logging systems** for safe operation
8. **Modular plugin architecture** for easy extension
9. **Professional UI/UX** with modern overlay design
10. **Complete development workflow** with tasks, dependencies, and documentation

The application is production-ready and provides a solid foundation for an AI-powered desktop assistant with extensive automation capabilities.
