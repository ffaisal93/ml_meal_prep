#!/bin/bash
# Script to deploy frontend to GitHub Pages

echo "🚀 Deploying frontend to GitHub Pages..."

# Check if we're in a git repository
if [ ! -d .git ]; then
    echo "❌ Not a git repository. Please initialize git first."
    exit 1
fi

# Create docs directory
echo "📁 Creating docs directory..."
mkdir -p docs

# Copy frontend files
echo "📋 Copying frontend files..."
cp -r frontend/* docs/

# Ask for Railway URL
read -p "Enter your Railway API URL (or press Enter to skip): " RAILWAY_URL

if [ ! -z "$RAILWAY_URL" ]; then
    echo "🔧 Updating API URL in frontend..."
    # Update the default API URL in app.js
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s|const DEFAULT_API_URL = '.*';|const DEFAULT_API_URL = '${RAILWAY_URL}';|g" docs/app.js
    else
        # Linux
        sed -i "s|const DEFAULT_API_URL = '.*';|const DEFAULT_API_URL = '${RAILWAY_URL}';|g" docs/app.js
    fi
    echo "✅ API URL updated to: $RAILWAY_URL"
fi

echo ""
echo "✅ Frontend files ready in docs/ directory"
echo ""
echo "Next steps:"
echo "1. git add docs/"
echo "2. git commit -m 'Deploy frontend to GitHub Pages'"
echo "3. git push"
echo "4. Go to GitHub → Settings → Pages"
echo "5. Select source: Deploy from branch → main → /docs"
echo ""
echo "Your site will be available at:"
echo "https://yourusername.github.io/ml_meal_prep/"

