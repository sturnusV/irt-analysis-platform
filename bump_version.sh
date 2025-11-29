#!/bin/bash
# bump_version.sh - Semantic version bumping

if [ $# -ne 1 ]; then
    echo "Usage: $0 [major|minor|patch]"
    exit 1
fi

CURRENT_VERSION=$(cat VERSION)
IFS='.' read -ra VERSION_PARTS <<< "$CURRENT_VERSION"
MAJOR=${VERSION_PARTS[0]}
MINOR=${VERSION_PARTS[1]}
PATCH=${VERSION_PARTS[2]}

case $1 in
    "major")
        MAJOR=$((MAJOR + 1))
        MINOR=0
        PATCH=0
        ;;
    "minor")
        MINOR=$((MINOR + 1))
        PATCH=0
        ;;
    "patch")
        PATCH=$((PATCH + 1))
        ;;
    *)
        echo "Invalid version type: $1"
        exit 1
        ;;
esac

NEW_VERSION="$MAJOR.$MINOR.$PATCH"
echo "Bumping version: $CURRENT_VERSION → $NEW_VERSION"
echo $NEW_VERSION > VERSION

# Update CHANGELOG placeholder
sed -i "s/## \[Unreleased\]/## [Unreleased]\n\n## [$NEW_VERSION] - $(date +%Y-%m-%d)/" CHANGELOG.md

echo "Version bumped to $NEW_VERSION"