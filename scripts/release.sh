#!/bin/sh
echo "Releasing new version"
poetry run semversioner release
echo "Updating CHANGELOG.md"
poetry run semversioner changelog > CHANGELOG.md