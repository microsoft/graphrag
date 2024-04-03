---
title: text_split
navtitle: text_split
layout: page
tags: [post, verb]
---
Split a piece of text into a list of strings based on a delimiter. The verb outputs a new column containing a list of strings.

## Usage

```yaml
verb: text_split
args:
    column: text # The name of the column containing the text to split
    to: split_text # The name of the column to output the split text to
    separator: "," # The separator to split the text on, defaults to ","
```

## Code
[split.py](https://dev.azure.com/msresearch/Resilience/_git/ire-indexing?path=/python/graphrag/graphrag/indexing/verbs/text/split.py)