#!/usr/bin/env python3
"""
Build script for Biquadr - compiles the application to a standalone binary.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        sys.exit(1)

def main():
    """Build the Biquadr application."""
    print("🚀 Building Biquadr - Frequency Response Designer")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("main.py").exists():
        print("❌ Error: main.py not found. Please run this script from the project root.")
        sys.exit(1)
    
    # Clean previous builds
    print("🧹 Cleaning previous builds...")
    for path in ["build", "dist", "__pycache__"]:
        if Path(path).exists():
            run_command(f"rm -rf {path}", f"Removing {path}")
    
    # Build with PyInstaller
    print("🔨 Building with PyInstaller...")
    run_command(
        "/Users/george/.local/bin/uv run pyinstaller biquadr.spec",
        "PyInstaller compilation"
    )
    
    # Check if build was successful
    binary_path = Path("dist/Biquadr")
    if binary_path.exists():
        print(f"✅ Build successful!")
        print(f"📦 Binary location: {binary_path.absolute()}")
        print(f"📏 Binary size: {binary_path.stat().st_size / (1024*1024):.1f} MB")
        print("\n🎉 Biquadr is ready to run as a standalone application!")
    else:
        print("❌ Build failed - binary not found")
        sys.exit(1)

if __name__ == "__main__":
    main()
