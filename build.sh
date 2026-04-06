#!/bin/bash
set -euo pipefail

REGISTRY="quay.io/mylastres0rt05"

VERSIONS=(
  "v1.44.0-jammy v1.44.0 v1.44"
  "v1.43.0-jammy v1.43.0 v1.43"
  "v1.42.0-jammy v1.42.0 v1.42"
  "v1.41.0-jammy v1.41.0 v1.41"
  "v1.40.0-jammy v1.40.0 v1.40"
  "v1.39.0-jammy v1.39.0 v1.39"
)

echo "==> Building tor-proxy"
docker build -t "${REGISTRY}/tor-proxy:latest" tor-proxy/

for entry in "${VERSIONS[@]}"; do
  read -r tag ver label <<< "$entry"
  echo "==> Building thor-session:${label}"
  docker build \
    --build-arg PLAYWRIGHT_TAG="${tag}" \
    --build-arg PLAYWRIGHT_VERSION="${ver}" \
    -t "${REGISTRY}/thor-session:${label}" .
done

echo "==> Pushing all images"
docker push "${REGISTRY}/tor-proxy:latest"
for entry in "${VERSIONS[@]}"; do
  read -r _ _ label <<< "$entry"
  docker push "${REGISTRY}/thor-session:${label}"
done

echo "==> Done"
