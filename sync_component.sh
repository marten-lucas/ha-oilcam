#!/bin/bash

# Source and destination directories
SOURCE_DIR="/workspaces/homeassistant-dev-core/config/custom_components/ha_oilcam/"
DEST_DIR="/workspaces/repos/ha-oilcam/custom_components/ha_oilcam/"

# Exit on any error
set -e

# Function to check if a directory exists
check_dir() {
    if [ ! -d "$1" ]; then
        echo "Error: Directory $1 does not exist."
        exit 1
    fi
}

# Check if source directory exists
check_dir "$SOURCE_DIR"

# Navigate to the destination repo directory
cd /workspaces/repos/ha-oilcam || {
    echo "Error: Could not change to /workspaces/repos/ha-oilcam"
    exit 1
}

# Pull the latest changes from origin/main with rebase to avoid merge commits
echo "Pulling latest changes from origin/main..."
git pull --rebase origin main || {
    echo "Error: Git pull failed. Resolve conflicts manually and try again."
    exit 1
}

# Ensure destination directory exists
mkdir -p "$DEST_DIR"

# Sync files from source to destination, excluding .git directories
echo "Syncing files from $SOURCE_DIR to $DEST_DIR..."
rsync -av --delete --exclude='.git' "$SOURCE_DIR" "$DEST_DIR"

# Check if there are any changes to commit
if git status --porcelain | grep -q .; then
    # Stage all changes
    echo "Staging changes..."
    git add .

    # Commit changes with a timestamped message
    COMMIT_MSG="Sync ha_oilcam updates - $(date '+%Y-%m-%d %H:%M:%S')"
    echo "Committing changes with message: $COMMIT_MSG"
    git commit -m "$COMMIT_MSG"

    # Push to origin/main
    echo "Pushing changes to origin/main..."
    git push origin main || {
        echo "Error: Git push failed. Check your network or permissions."
        exit 1
    }
else
    echo "No changes to commit."
fi

echo "Sync and push completed successfully!"