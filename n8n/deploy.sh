#!/bin/bash
# Quick deploy script for n8n to Fly.io

set -e

echo "🚀 n8n Fly.io Deployment Script"
echo "================================"
echo ""

# Check if flyctl is installed
if ! command -v fly &> /dev/null; then
    echo "❌ Fly.io CLI not found. Install it first:"
    echo "   https://fly.io/docs/hands-on/install-flyctl/"
    exit 1
fi

# Check if logged in
if ! fly auth whoami &> /dev/null; then
    echo "❌ Not logged in to Fly.io. Run: fly auth login"
    exit 1
fi

# Get app name from fly.toml or prompt
APP_NAME=$(grep "^app = " fly.toml | cut -d'"' -f2)

if [ -z "$APP_NAME" ] || [ "$APP_NAME" == "your-app-n8n" ]; then
    echo "Enter your n8n app name (must be unique across Fly.io):"
    read -r APP_NAME

    # Update fly.toml
    sed -i.bak "s/app = \"your-app-n8n\"/app = \"$APP_NAME\"/" fly.toml
    sed -i.bak "s|WEBHOOK_URL = \"https://your-app-n8n.fly.dev/\"|WEBHOOK_URL = \"https://$APP_NAME.fly.dev/\"|" fly.toml
    echo "✅ Updated fly.toml with app name: $APP_NAME"
fi

# Check if app exists
if ! fly apps list | grep -q "^$APP_NAME"; then
    echo "📦 Creating Fly.io app: $APP_NAME"
    fly apps create "$APP_NAME" --org personal
else
    echo "✅ App already exists: $APP_NAME"
fi

# Check if volume exists
if ! fly volumes list -a "$APP_NAME" | grep -q "n8n_data"; then
    echo "💾 Creating persistent volume..."
    fly volumes create n8n_data --size 1 --region sjc -a "$APP_NAME"
else
    echo "✅ Volume already exists"
fi

# Set secrets if not already set
echo "🔐 Setting up secrets..."

# Generate encryption key if needed
if ! fly secrets list -a "$APP_NAME" | grep -q "N8N_ENCRYPTION_KEY"; then
    ENCRYPTION_KEY=$(openssl rand -hex 32)
    fly secrets set N8N_ENCRYPTION_KEY="$ENCRYPTION_KEY" -a "$APP_NAME"
    echo "✅ Set encryption key"
else
    echo "✅ Encryption key already set"
fi

# Optionally set basic auth
echo ""
echo "Do you want to enable basic authentication? (y/n)"
read -r ENABLE_AUTH

if [ "$ENABLE_AUTH" == "y" ]; then
    echo "Enter admin username (default: admin):"
    read -r AUTH_USER
    AUTH_USER=${AUTH_USER:-admin}

    echo "Enter admin password:"
    read -s AUTH_PASS

    fly secrets set \
        N8N_BASIC_AUTH_ACTIVE=true \
        N8N_BASIC_AUTH_USER="$AUTH_USER" \
        N8N_BASIC_AUTH_PASSWORD="$AUTH_PASS" \
        -a "$APP_NAME"

    echo "✅ Basic auth configured"
fi

# Ask for generation API URL
echo ""
echo "Enter your Generation API URL (e.g., https://your-api.fly.dev):"
echo "(Press enter to skip and configure later)"
read -r API_URL

if [ -n "$API_URL" ]; then
    sed -i.bak "s|GENERATION_API_URL = \"http://localhost:8000\"|GENERATION_API_URL = \"$API_URL\"|" fly.toml
    echo "✅ Updated API URL in fly.toml"
fi

# Deploy
echo ""
echo "🚢 Deploying n8n to Fly.io..."
fly deploy -a "$APP_NAME"

echo ""
echo "✨ Deployment complete!"
echo ""
echo "Access your n8n instance at: https://$APP_NAME.fly.dev"
echo ""
echo "To open in browser: fly open -a $APP_NAME"
echo "To view logs: fly logs -a $APP_NAME"
echo "To scale up: fly scale vm shared-cpu-1x --memory 1024 -a $APP_NAME"
echo ""
echo "Next steps:"
echo "1. Open n8n and create your owner account"
echo "2. Import workflows from ./workflows/ directory"
echo "3. Update API URLs in workflows if needed"
echo ""
