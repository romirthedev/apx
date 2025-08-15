#!/bin/bash

# Cluely Setup Script for macOS
# This script sets up the AI assistant with proper permissions and dependencies

set -e

echo "🤖 Setting up Cluely AI Assistant"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}❌ This setup script is designed for macOS only${NC}"
    exit 1
fi

# Function to print status
print_status() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check for required tools
print_status "Checking prerequisites..."

# Check for Node.js
if ! command -v node &> /dev/null; then
    print_error "Node.js is required but not installed."
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed."
    echo "Please install Python 3 from https://python.org/"
    exit 1
fi

print_success "Prerequisites check passed"

# Install Node.js dependencies
print_status "Installing Node.js dependencies..."
npm install
print_success "Node.js dependencies installed"

# Set up Python virtual environment
print_status "Setting up Python virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    print_success "Virtual environment created"
else
    print_success "Virtual environment already exists"
fi

# Activate virtual environment and install Python dependencies
print_status "Installing Python dependencies..."
source .venv/bin/activate
pip install -r backend/requirements.txt
print_success "Python dependencies installed"

# Check current permissions
print_status "Checking macOS permissions..."
python backend/core/macos_permissions.py

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p logs
mkdir -p assets
print_success "Directories created"

# Set up launch script
print_status "Creating launch script..."
cat > start-cluely.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
echo "🤖 Starting Cluely AI Assistant..."
npm run dev
EOF

chmod +x start-cluely.sh
print_success "Launch script created"

echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "Next steps:"
echo "1. Grant the required permissions:"
echo "   - System Settings → Privacy & Security → Full Disk Access → Add Cluely"
echo "   - System Settings → Privacy & Security → Accessibility → Add Cluely"
echo "   - System Settings → Privacy & Security → Screen Recording → Add Cluely"
echo ""
echo "2. Start Cluely:"
echo "   ./start-cluely.sh"
echo "   OR"
echo "   npm run dev"
echo ""
echo "3. For daemon mode (background service):"
echo "   npm run install-daemon"
echo ""
echo "4. Check permissions anytime:"
echo "   npm run permissions-check"
echo ""
print_success "Cluely is ready to assist you! 🚀"
