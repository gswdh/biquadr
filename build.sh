#!/bin/bash
# Build script for Biquadr - compiles to standalone binary

echo "🚀 Building Biquadr - Frequency Response Designer"
echo "=================================================="

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build dist __pycache__

# Build with PyInstaller
echo "🔨 Building with PyInstaller..."
/Users/george/.local/bin/uv run pyinstaller biquadr.spec

# Check if build was successful
if [ -f "dist/Biquadr" ]; then
    echo "✅ Build successful!"
    echo "📦 Binary location: $(pwd)/dist/Biquadr"
    echo "📏 Binary size: $(du -h dist/Biquadr | cut -f1)"
    echo ""
    echo "🎉 Biquadr is ready to run as a standalone application!"
    echo "💡 Run it with: ./dist/Biquadr"
else
    echo "❌ Build failed - binary not found"
    exit 1
fi
