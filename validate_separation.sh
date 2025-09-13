#!/bin/bash

echo "=========================================="
echo "🔍 VALIDATING APP SEPARATION"
echo "=========================================="

ERRORS=0

# Check if both directories exist
echo "Checking directory structure..."
if [ ! -d "builder-agno-system" ]; then
    echo "❌ builder-agno-system directory missing!"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ builder-agno-system exists"
fi

if [ ! -d "sophia-intel-app" ]; then
    echo "❌ sophia-intel-app directory missing!"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ sophia-intel-app exists"
fi

# Check for separate package.json files
echo -e "\nChecking package.json files..."
if [ ! -f "builder-agno-system/package.json" ]; then
    echo "❌ builder-agno-system/package.json missing!"
    ERRORS=$((ERRORS + 1))
else
    NAME=$(grep '"name"' builder-agno-system/package.json | head -1)
    if [[ $NAME == *"@builder-agno/system"* ]]; then
        echo "✅ Builder package.json has correct name"
    else
        echo "❌ Builder package.json has wrong name: $NAME"
        ERRORS=$((ERRORS + 1))
    fi
fi

if [ ! -f "sophia-intel-app/package.json" ]; then
    echo "❌ sophia-intel-app/package.json missing!"
    ERRORS=$((ERRORS + 1))
else
    NAME=$(grep '"name"' sophia-intel-app/package.json | head -1)
    if [[ $NAME == *"sophia-intel"* ]]; then
        echo "✅ Sophia package.json has correct name"
    else
        echo "❌ Sophia package.json has wrong name: $NAME"
        ERRORS=$((ERRORS + 1))
    fi
fi

# Check for cross-imports
echo -e "\nChecking for cross-imports..."
BUILDER_IN_SOPHIA=$(grep -r "builder-agno\|BuilderAgno" sophia-intel-app/src 2>/dev/null | wc -l)
if [ "$BUILDER_IN_SOPHIA" -gt 0 ]; then
    echo "❌ Found $BUILDER_IN_SOPHIA Builder references in Sophia app!"
    grep -r "builder-agno\|BuilderAgno" sophia-intel-app/src 2>/dev/null | head -3
    ERRORS=$((ERRORS + 1))
else
    echo "✅ No Builder references in Sophia app"
fi

SOPHIA_IN_BUILDER=$(grep -r "sophia-intel\|SophiaIntel" builder-agno-system/src 2>/dev/null | wc -l)
if [ "$SOPHIA_IN_BUILDER" -gt 0 ]; then
    echo "❌ Found $SOPHIA_IN_BUILDER Sophia references in Builder app!"
    grep -r "sophia-intel\|SophiaIntel" builder-agno-system/src 2>/dev/null | head -3
    ERRORS=$((ERRORS + 1))
else
    echo "✅ No Sophia references in Builder app"
fi

# Check startup scripts
echo -e "\nChecking startup scripts..."
if [ ! -f "start_builder_agno.sh" ]; then
    echo "❌ start_builder_agno.sh missing!"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ start_builder_agno.sh exists"
fi

if [ ! -f "start_sophia_intel.sh" ]; then
    echo "❌ start_sophia_intel.sh missing!"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ start_sophia_intel.sh exists"
fi

# Check for consolidation files
echo -e "\nChecking for consolidation attempts..."
if [ -f "start_unified.sh" ] || [ -f "start_combined.sh" ]; then
    echo "❌ Found unified/combined startup scripts!"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ No unified startup scripts found"
fi

# Check port configurations
echo -e "\nChecking port configurations..."
if [ -f "builder-agno-system/package.json" ]; then
    BUILDER_PORT=$(grep -E "dev.*-p\s*8005" builder-agno-system/package.json)
    if [[ -n "$BUILDER_PORT" ]]; then
        echo "✅ Builder configured for port 8005"
    else
        echo "❌ Builder not configured for port 8005"
        ERRORS=$((ERRORS + 1))
    fi
fi

if [ -f "sophia-intel-app/package.json" ]; then
    SOPHIA_PORT=$(grep -E "dev.*-p\s*3000|dev.*port\s*3000" sophia-intel-app/package.json)
    if [[ -n "$SOPHIA_PORT" ]]; then
        echo "✅ Sophia configured for port 3000"
    else
        echo "❌ Sophia not configured for port 3000"
        ERRORS=$((ERRORS + 1))
    fi
fi

# Summary
echo -e "\n=========================================="
if [ $ERRORS -eq 0 ]; then
    echo "✅ VALIDATION PASSED - Apps are properly separated!"
else
    echo "❌ VALIDATION FAILED - Found $ERRORS separation violations!"
    echo "Please review TWO_APPS_SEPARATION_GUIDE.md"
fi
echo "=========================================="

exit $ERRORS