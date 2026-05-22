#!/usr/bin/env bash
# validate-harness.sh
# Verifies that all files referenced in project-template.md exist.

set -e

HARNESS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_FILE="$HARNESS_DIR/project-template.md"

echo "Validating Agentic Harness integrity..."

# Use sed to expand the {{HARNESS_DIR}} in the template content first, then grep the paths
CONTENT=$(sed "s|{{HARNESS_DIR}}|$HARNESS_DIR|g" "$TEMPLATE_FILE")
PATHS=$(echo "$CONTENT" | grep -oE "/[a-zA-Z0-9._/-]*(rules|skills)/[a-zA-Z0-9._/-]*")

MISSING_COUNT=0

# Also check the /skills/ directory specifically
PATHS="$PATHS $HARNESS_DIR/skills/"

for full_path in $PATHS; do
    # Remove any trailing punctuation or markdown artifacts (backticks, dots, closing brackets)
    clean_path=$(echo "$full_path" | sed 's/[[:punct:]]$//')

    if [ ! -e "$clean_path" ]; then
        # Check if it's a comment or intentional placeholder (like typescript.md)
        if [[ "$clean_path" == *"typescript.md"* ]]; then
            echo "ℹ️ OPTIONAL (Commented): $clean_path"
        else
            echo "❌ MISSING: $clean_path"
            MISSING_COUNT=$((MISSING_COUNT + 1))
        fi
    else
        echo "✅ FOUND: $clean_path"
    fi
done

if [ $MISSING_COUNT -gt 0 ]; then
    echo "Validation FAILED: $MISSING_COUNT files missing."
    exit 1
else
    echo "Validation SUCCESS: All harness references are intact."
fi
