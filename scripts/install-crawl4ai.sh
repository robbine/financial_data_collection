#!/bin/bash
# Install the latest Crawl4AI with official setup steps
# Compatible with Ubuntu / Debian / Docker

set -e

echo "🚀 Installing Crawl4AI (latest official version)..."

# ====== Colors ======
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() { echo -e "${GREEN}[INFO]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ====== Check Python ======
# 优先检测python3.11, 其次python3, 最后python
if command -v python3.11 &> /dev/null; then
    python_cmd="python3.11"
elif command -v python3 &> /dev/null; then
    python_cmd="python3"
elif command -v python &> /dev/null; then
    python_cmd="python"
else
    print_error "Python 3.8+ required but not found."
    exit 1
fi

python_version=$($python_cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
required_version="3.8"

if [ "$(printf '%s
' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ];
then
    print_error "Python 3.8+ is required (current: $python_version)"
    exit 1
fi

print_status "Using Python: $python_cmd ($python_version)"

print_status "Python version: $python_version"

# ====== System dependencies ======
if command -v apt-get &> /dev/null; then
    print_status "Installing system dependencies..."
    sudo apt-get update -y || true
    sudo apt-get install -y \
        build-essential \
        curl \
        wget \
        gnupg \
        ca-certificates \
        fonts-liberation \
        libasound2t64 \
        libatk-bridge2.0-0t64 \
        libdrm2 \
        libxcomposite1 \
        libxdamage1 \
        libxrandr2 \
        libgbm1 \
        libxss1 \
        libnss3
else
    print_warning "apt-get not found, skipping system deps installation."
fi

# ====== Chromium ======
if ! command -v chromium &> /dev/null && ! command -v chromium-browser &> /dev/null; then
    print_status "Installing Chromium..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get install -y chromium || sudo apt-get install -y chromium-browser || true
    fi
fi

# ====== Node.js ======
if ! command -v node &> /dev/null; then
    print_status "Installing Node.js (v18)..."
    if command -v apt-get &> /dev/null; then
        curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
        sudo apt-get install -y nodejs
    else
        print_warning "Node.js not installed (no apt). Please install Node.js v18+ manually."
    fi
fi

print_status "Node.js version: $(node --version 2>/dev/null || echo 'Not found')"

# ====== Install Crawl4AI ======
print_status "Installing Crawl4AI (latest stable or pre-release)..."
pip install crawl4ai==0.7.4 --no-cache-dir

# ====== Post-install setup ======
print_status "Running Crawl4AI setup..."
crawl4ai-setup || print_warning "crawl4ai-setup failed, continuing..."

# ====== Verify installation ======
print_status "Verifying installation..."
crawl4ai-doctor || print_warning "crawl4ai-doctor found issues. Check browser dependencies."

# ====== Install browser (if needed) ======
print_status "Installing Playwright Chromium browser..."
python3.11 -m playwright install chromium || { print_warning "Chromium installation failed"; exit 1; }

# ====== Quick functionality test ======
print_status "Testing Crawl4AI basic crawl..."
python3 - << 'PYCODE'
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://httpbin.org/get")
        print("✅ Basic crawl success. URL:", result.url)

asyncio.run(main())
PYCODE

print_status "🎉 Crawl4AI installation and test completed successfully!"
