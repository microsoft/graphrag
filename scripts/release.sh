#!/bin/sh
#
# Maintainers: do not change the pyproject.toml version, or CHANGELOG.md contents manually.
# This release script will automate these changes for you.
#
echo "Releasing new version"
poetry run semversioner release
echo "Updating CHANGELOG.md"
poetry run semversioner changelog > CHANGELOG.md

echo "Finding the most recently changed file in .semversioner"
most_recent_file=$(ls -Art ./.semversioner/*.json | tail -n 1)
most_recent_file=${most_recent_file#./.semversioner/}
most_recent_file=${most_recent_file%.json}
echo "The most recently version is: $most_recent_file"

echo "Updating pyproject.toml version"
poetry run update-toml --path tool.poetry.version --value $most_recent_file pyproject.toml