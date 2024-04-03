#!/bin/sh
echo "Releasing new version"
#poetry run semversioner release
echo "Updating CHANGELOG.md"
poetry run semversioner changelog > CHANGELOG.md

echo "Finding the most recently changed file in .semversioner"
most_recent_file=$(ls -Art ./.semversioner/*.json | tail -n 1)
most_recent_file=${most_recent_file#./.semversioner/}
most_recent_file=${most_recent_file%.json}
echo "The most recently version is: $most_recent_file"

echo "Updating pyproject.toml version"
sed -i '' "s/\(version *= *\).*/\1\"$most_recent_file\"/" pyproject.toml