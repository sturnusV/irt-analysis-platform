#!/bin/bash
# build.sh - Build with version tracking
BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
COMMIT_HASH=$(git rev-parse --short HEAD)

echo "Building IRT AnalyzeR v$(cat VERSION)"
echo "Build date: $BUILD_DATE"
echo "Commit hash: $COMMIT_HASH"

docker-compose build --build-arg BUILD_DATE=$BUILD_DATE --build-arg COMMIT_HASH=$COMMIT_HASH
docker-compose up -d