#!/bin/bash

# Install Crawl4AI and dependencies for Financial Data Collector

set -e

echo "🚀 Installing Crawl4AI for Financial Data Collector..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check Python version
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    print_error "Python 3.8+ is required. Current version: $python_version"
    exit 1
fi

print_status "Python version: $python_version"

# Install system dependencies (Ubuntu/Debian)
if command -v apt-get &> /dev/null; then
    print_status "Installing system dependencies..."
    sudo apt-get update
    sudo apt-get install -y \
        build-essential \
        curl \
        wget \
        gnupg \
        ca-certificates \
        chromium-browser \
        fonts-liberation \
        libasound2 \
        libatk-bridge2.0-0 \
        libdrm2 \
        libxcomposite1 \
        libxdamage1 \
        libxrandr2 \
        libgbm1 \
        libxss1 \
        libnss3
fi

# Install Node.js (required for crawl4ai)
if ! command -v node &> /dev/null; then
    print_status "Installing Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi

print_status "Node.js version: $(node --version)"

# Install Python dependencies
print_status "Installing Python dependencies..."

# Install crawl4ai
pip3 install crawl4ai==0.3.70

# Install playwright
pip3 install playwright==1.40.0

# Install other required packages
pip3 install aiohttp beautifulsoup4 lxml selenium requests

# Install playwright browsers
print_status "Installing Playwright browsers..."
python3 -m playwright install chromium
python3 -m playwright install-deps chromium

# Run crawl4ai setup
print_status "Running crawl4ai setup..."
python3 -m crawl4ai.setup

# Test installation
print_status "Testing Crawl4AI installation..."
python3 -c "
import crawl4ai
print(f'✅ Crawl4AI version: {crawl4ai.__version__}')

from crawl4ai import AsyncWebCrawler
print('✅ AsyncWebCrawler imported successfully')

from crawl4ai.extraction_strategy import LLMExtractionStrategy
print('✅ LLMExtractionStrategy imported successfully')

print('✅ Crawl4AI installation successful!')
"

# Create test script
print_status "Creating test script..."
cat > test_crawl4ai.py << 'EOF'
#!/usr/bin/env python3
"""
Test script for Crawl4AI installation
"""

import asyncio
import sys
from crawl4ai import AsyncWebCrawler

async def test_crawl4ai():
    """Test basic Crawl4AI functionality."""
    print("🧪 Testing Crawl4AI functionality...")
    
    try:
        # Create crawler
        crawler = AsyncWebCrawler(
            browser_type="chromium",
            headless=True
        )
        
        # Start crawler
        await crawler.start()
        print("✅ Crawler started successfully")
        
        # Test crawl
        result = await crawler.arun(
            url="https://httpbin.org/get",
            wait_for=1
        )
        
        print(f"✅ Test crawl successful")
        print(f"   - URL: {result.url}")
        print(f"   - Title: {result.title}")
        print(f"   - Word count: {result.word_count}")
        
        # Close crawler
        await crawler.close()
        print("✅ Crawler closed successfully")
        
        print("🎉 Crawl4AI test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_crawl4ai())
    sys.exit(0 if success else 1)
EOF

chmod +x test_crawl4ai.py

# Run test
print_status "Running Crawl4AI test..."
if python3 test_crawl4ai.py; then
    print_status "✅ Crawl4AI test passed!"
else
    print_error "❌ Crawl4AI test failed!"
    exit 1
fi

# Cleanup test files
rm -f test_crawl4ai.py

print_status "🎉 Crawl4AI installation completed successfully!"
print_status ""
print_status "Next steps:"
print_status "1. Configure your API keys in .env file"
print_status "2. Run the demo: python examples/crawl4ai_demo.py"
print_status "3. Start the system: make dev"
print_status ""
print_status "For more information, see CRAWL4AI.md"
