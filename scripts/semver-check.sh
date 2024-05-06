#!/bin/sh
changes=$(git diff --name-only origin/main)
has_change_doc=$(echo $changes | grep .semversioner/next-release)
has_impacting_changes=$(echo $changes | grep graphrag)

if [ "$has_impacting_changes" ] && [ -z "$has_change_doc" ]; then
    echo "Check failed. Run 'poetry run semversioner add-change' to update the next release version"
    exit 1
fi
echo "OK"
