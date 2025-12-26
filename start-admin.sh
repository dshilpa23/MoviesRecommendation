#!/bin/bash

# Admin Dashboard Launcher
# This script starts the local-only admin dashboard at http://127.0.0.1:5000

set -e

echo "🎬 Movies Recommendation - Admin Dashboard Launcher"
echo "=================================================="
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "admin/app.py" ]; then
    echo "❌ Please run this script from the MoviesRecommendation root directory"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "admin/.venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv admin/.venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source admin/.venv/bin/activate

# Install/upgrade dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r admin/requirements.txt
echo "✓ Dependencies installed"

# Check for Excel file
if [ ! -f "movies_master.xlsx" ]; then
    echo "⚠️  Warning: movies_master.xlsx not found in project root"
    echo "   The admin dashboard expects this file to exist."
fi

# Check for data files
if [ ! -d "data" ]; then
    echo "⚠️  Warning: 'data' directory not found. Some features may not work."
fi

echo ""
echo "=================================================="
echo "✅ Setup complete! Starting admin dashboard..."
echo ""
echo "📍 Local access: http://127.0.0.1:5000"
echo "🔐 Not publicly accessible (local network only)"
echo ""
echo "💡 Features:"
echo "   • Edit movies_master.xlsx in web UI"
echo "   • Filter by status, language, region, completeness"
echo "   • Run enrichment pipeline"
echo "   • Generate and preview JSON"
echo "   • Manage backups"
echo "   • Publish to S3 (optional)"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=================================================="
echo ""

# Run Flask app
cd admin
python3 app.py
