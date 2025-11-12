#!/bin/zsh
# Project Cleanup Script - Remove unnecessary files
# Date: November 12, 2025

echo "🧹 Starting project cleanup..."
echo ""

# Navigate to project directory
cd "/Users/navya/iCloud Drive (Archive)/Desktop/Documents/project files/BACAPSTONE copy 6"

# ============================================
# 1. Remove Python cache files
# ============================================
echo "📦 Removing Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
find . -type f -name "*.pyo" -delete 2>/dev/null
echo "   ✅ Python cache removed"

# ============================================
# 2. Remove macOS system files
# ============================================
echo "🍎 Removing macOS system files..."
find . -type f -name ".DS_Store" -delete 2>/dev/null
echo "   ✅ .DS_Store files removed"

# ============================================
# 3. Remove backup and temporary files
# ============================================
echo "📝 Removing backup and temporary files..."
find . -type f -name "*~" -delete 2>/dev/null
find . -type f -name "*.bak" -delete 2>/dev/null
find . -type f -name "*.old" -delete 2>/dev/null
find . -type f -name "*.tmp" -delete 2>/dev/null
echo "   ✅ Backup files removed"

# ============================================
# 4. Remove duplicate/test HTML files
# ============================================
echo "🗑️  Removing duplicate HTML files..."
rm -f analogies_fixed.html 2>/dev/null
echo "   ✅ analogies_fixed.html removed"

# ============================================
# 5. Remove test files
# ============================================
echo "🧪 Removing test files..."
rm -f test_complete_database_system.py 2>/dev/null
rm -f test_complete_system.py 2>/dev/null
rm -f final_integration_test.py 2>/dev/null
rm -f populate_idioms.py 2>/dev/null
echo "   ✅ Test files removed"

# ============================================
# 6. Remove README/Documentation files (optional)
# ============================================
echo "📚 Removing extra documentation files..."
rm -f COMPLETE_PROJECT_README.md 2>/dev/null
rm -f DATABASE_INTEGRATION_SUMMARY.md 2>/dev/null
rm -f MODEL_ACCURACY_REPORT.md 2>/dev/null
rm -f PLAYGROUND_INTEGRATION.md 2>/dev/null
rm -f POSTICO_VIEWING_GUIDE.md 2>/dev/null
rm -f PROJECT_CLEANUP_SUMMARY.md 2>/dev/null
rm -f SEARCH_INTEGRATION_SUCCESS.md 2>/dev/null
echo "   ✅ Extra documentation removed (keeping main README.md)"

# ============================================
# 7. Remove admin_tools directory
# ============================================
echo "🔧 Removing admin tools (can be recreated if needed)..."
rm -rf admin_tools 2>/dev/null
echo "   ✅ admin_tools directory removed"

# ============================================
# 8. Remove extra CSV files in Dataset
# ============================================
echo "📊 Cleaning up dataset directory..."
cd "Cooontext bridge/Dataset"
# Keep only English_proverbs_translation.csv (the main dataset)
rm -f Hindi_Proverbs_Translation.csv 2>/dev/null
rm -f Telugu_Proverbs_Hindi.csv 2>/dev/null
cd "../.."
echo "   ✅ Extra CSV files removed (keeping English_proverbs_translation.csv)"

# ============================================
# 9. Remove log files (if any)
# ============================================
echo "📋 Removing log files..."
find . -type f -name "*.log" -delete 2>/dev/null
echo "   ✅ Log files removed"

# ============================================
# Summary
# ============================================
echo ""
echo "✅ ============================================"
echo "✅ CLEANUP COMPLETE!"
echo "✅ ============================================"
echo ""
echo "📦 Essential files kept:"
echo "   ✓ index.html - Landing page"
echo "   ✓ signin.html - Sign in page"
echo "   ✓ playground.html - Translation UI"
echo "   ✓ analogies.html - Idiom search"
echo "   ✓ system_status.html - System monitoring"
echo "   ✓ debug_search.html - Debug interface"
echo "   ✓ analogies.js - Frontend logic"
echo "   ✓ styles.css - Styles"
echo "   ✓ logo.jpeg - Logo image"
echo "   ✓ idiom_api_server.py - Main API server"
echo "   ✓ database_config.py - Database configuration"
echo "   ✓ idiom_requirements.txt - Python dependencies"
echo "   ✓ README.md - Main documentation"
echo "   ✓ Cooontext bridge/playground_api.py - Translation API"
echo "   ✓ Cooontext bridge/requirements.txt - Translation dependencies"
echo "   ✓ Cooontext bridge/test_translation.py - Translation module"
echo "   ✓ Cooontext bridge/Dataset/English_proverbs_translation.csv - Main dataset"
echo "   ✓ Cooontext bridge/nllb_idiom_finetuned/ - Fine-tuned model"
echo ""
echo "🗑️  Files removed:"
echo "   ✗ __pycache__/ directories"
echo "   ✗ *.pyc, *.pyo files"
echo "   ✗ .DS_Store files"
echo "   ✗ Backup files (*~, *.bak, *.old)"
echo "   ✗ analogies_fixed.html (duplicate)"
echo "   ✗ Test files (test_*.py, populate_idioms.py)"
echo "   ✗ Extra documentation files"
echo "   ✗ admin_tools/ directory"
echo "   ✗ Extra CSV files (Hindi_Proverbs_Translation.csv, Telugu_Proverbs_Hindi.csv)"
echo ""
echo "💡 Your project is now clean and ready to run!"
echo "💡 To start the servers, run: python idiom_api_server.py"
echo ""
