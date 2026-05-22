#!/usr/bin/env bash
set -e

HARNESS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${1:-.}"

echo "Configuring AI standards for project at: $(realpath "$TARGET_DIR")"

# The master template file
TEMPLATE_FILE="$HARNESS_DIR/project-template.md"

if [ ! -f "$TEMPLATE_FILE" ]; then
    echo "Error: Template file $TEMPLATE_FILE not found."
    exit 1
fi

# Generate the content by replacing the placeholder with the actual harness directory
CONTENT=$(sed "s|{{HARNESS_DIR}}|$HARNESS_DIR|g" "$TEMPLATE_FILE")

# List of common agent instruction files to target
TARGET_FILES=(
    ".cursorrules"
    "INSTRUCTIONS.md"
    "GEMINI.md"
    "agents.md"
    ".clinerules"
)

# Ensure GitHub directory exists if we want to write copilot instructions
mkdir -p "$TARGET_DIR/.github"
TARGET_FILES+=(".github/copilot-instructions.md")

for file in "${TARGET_FILES[@]}"; do
    target_path="$TARGET_DIR/$file"

    if [ -f "$target_path" ]; then
        echo "Appending to existing $target_path..."
        printf "\n\n---\n\n" >> "$target_path"
        echo "$CONTENT" >> "$target_path"
    else
        echo "Creating $target_path..."
        echo "$CONTENT" > "$target_path"
    fi
done

echo "Success! Broadcasted harness instructions to all agent entry points."
