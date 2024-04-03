---
title: text_replace
navtitle: text_replace
layout: page
tags: [post, verb]
---
Apply a set of replacements to a piece of text.

## Usage
```yaml
verb: text_replace
args:
    column: <column name> # The name of the column containing the text to replace
    to: <column name> # The name of the column to write the replaced text to
    replacements: # A list of replacements to apply
        - pattern: <string> # The regex pattern to find
        replacement: <string> # The string to replace with
```

## Code
[replace.py](https://dev.azure.com/msresearch/Resilience/_git/ire-indexing?path=/python/graphrag/graphrag/indexing/verbs/text/replace/replace.py)