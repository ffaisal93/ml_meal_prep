#!/bin/bash
# Script to organize documentation files into docs/ folder

echo "📁 Organizing documentation files..."

# Create docs directory if it doesn't exist
mkdir -p docs

# Move documentation files to docs/
if [ -f "DEPLOYMENT.md" ]; then
    mv DEPLOYMENT.md docs/
    echo "✅ Moved DEPLOYMENT.md"
fi

if [ -f "UPDATE_DEPLOYMENT.md" ]; then
    mv UPDATE_DEPLOYMENT.md docs/
    echo "✅ Moved UPDATE_DEPLOYMENT.md"
fi

if [ -f "TESTING.md" ]; then
    mv TESTING.md docs/
    echo "✅ Moved TESTING.md"
fi

if [ -f "PRE_COMMIT_CHECKLIST.md" ]; then
    mv PRE_COMMIT_CHECKLIST.md docs/
    echo "✅ Moved PRE_COMMIT_CHECKLIST.md"
fi

if [ -f "QUICK_START.md" ]; then
    mv QUICK_START.md docs/
    echo "✅ Moved QUICK_START.md"
fi

echo ""
echo "✅ Documentation organized!"
echo "📚 All docs are now in docs/ folder"
echo ""
echo "Project structure:"
echo "  ├── README.md (main overview)"
echo "  ├── docs/"
echo "  │   ├── README.md (docs index)"
echo "  │   ├── QUICK_START.md"
echo "  │   ├── TESTING.md"
echo "  │   ├── DEPLOYMENT.md"
echo "  │   ├── UPDATE_DEPLOYMENT.md"
echo "  │   └── PRE_COMMIT_CHECKLIST.md"
echo "  ├── app/ (Python code)"
echo "  ├── frontend/ (Frontend code)"
echo "  └── ... (config files)"

