#!/usr/bin/env bash
set -e

HARNESS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="."
COPY_MODE=false

# Simple argument parsing
while [[ $# -gt 0 ]]; do
    case "$1" in
        --copy)
            COPY_MODE=true
            shift
            ;;
        *)
            TARGET_DIR="$1"
            shift
            ;;
    esac
done

echo "Configuring AI standards for project at: $(realpath "$TARGET_DIR")"

# The master template file
TEMPLATE_FILE="$HARNESS_DIR/project-template.md"

if [ ! -f "$TEMPLATE_FILE" ]; then
    echo "Error: Template file $TEMPLATE_FILE not found."
    exit 1
fi

if [ "$COPY_MODE" = true ]; then
    echo "Copy mode enabled. Copying harness files to $TARGET_DIR/.harness..."
    mkdir -p "$TARGET_DIR/.harness"
    cp -r "$HARNESS_DIR/rules" "$TARGET_DIR/.harness/"
    cp -r "$HARNESS_DIR/skills" "$TARGET_DIR/.harness/"
fi

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
    target_dir_path=$(dirname "$target_path")

    if [ "$COPY_MODE" = true ]; then
        HARNESS_PATH=$(realpath --relative-to="$(realpath "$target_dir_path")" "$(realpath "$TARGET_DIR")/.harness" 2>/dev/null || realpath "$TARGET_DIR/.harness")
    else
        HARNESS_PATH="$HARNESS_DIR"
    fi

    CONTENT=$(sed "s|{{HARNESS_DIR}}|$HARNESS_PATH|g" "$TEMPLATE_FILE")

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
