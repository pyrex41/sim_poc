#!/bin/bash
# Deployment script for Fly.io

set -e

echo "🚀 Physics Simulator - Fly.io Deployment"
echo "========================================"
echo ""

# Check if fly CLI is installed
if ! command -v fly &> /dev/null; then
    echo "❌ Fly.io CLI not found. Please install it first:"
    echo "   curl -L https://fly.io/install.sh | sh"
    exit 1
fi

# Check if logged in
if ! fly auth whoami &> /dev/null; then
    echo "❌ Not logged in to Fly.io. Please run:"
    echo "   fly auth login"
    exit 1
fi

echo "✅ Fly.io CLI found and authenticated"
echo ""

# Check if app exists
if fly status &> /dev/null; then
    echo "📦 App exists, proceeding with deployment..."
else
    echo "🆕 App doesn't exist yet."
    echo ""
    read -p "Do you want to create a new app? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        fly launch --no-deploy
        echo ""
        echo "⚠️  Don't forget to:"
        echo "   1. Create a volume: fly volumes create physics_data --region <your-region> --size 1"
        echo "   2. Set secrets: fly secrets set REPLICATE_API_KEY=your_key_here"
        echo "   3. Run this script again to deploy"
        exit 0
    else
        echo "Deployment cancelled."
        exit 0
    fi
fi

# Check if volume exists
echo ""
echo "📂 Checking for persistent volume..."
if fly volumes list | grep -q "physics_data"; then
    echo "✅ Volume 'physics_data' found"
else
    echo "⚠️  Volume 'physics_data' not found!"
    echo ""
    read -p "Create volume now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        APP_REGION=$(fly status --json | grep -o '"Region":"[^"]*"' | cut -d'"' -f4 | head -1)
        if [ -z "$APP_REGION" ]; then
            APP_REGION="iad"
            echo "⚠️  Couldn't detect region, using default: $APP_REGION"
        fi
        echo "Creating volume in region: $APP_REGION"
        fly volumes create physics_data --region "$APP_REGION" --size 1
    else
        echo "❌ Volume required for deployment. Exiting."
        exit 1
    fi
fi

# Deploy
echo ""
echo "🚀 Deploying to Fly.io..."
fly deploy

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 Your app is available at: https://$(fly status --json | grep -o '"Hostname":"[^"]*"' | cut -d'"' -f4).fly.dev"
echo ""
echo "📊 View logs: fly logs"
echo "📈 Check status: fly status"
echo "🔓 SSH access: fly ssh console"
echo ""
