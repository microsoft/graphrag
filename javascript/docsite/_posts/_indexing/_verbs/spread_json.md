---
title: spread_json
navtitle: spread_json
layout: page
tags: [post, verb]
---
Unpack a column containing a tuple into multiple columns.

id|json|b
1|{"x":5,"y":6}|b

is converted to

id|x|y|b
--------
1|5|6|b

## Code
[spread_json.py](https://dev.azure.com/msresearch/Resilience/_git/ire-indexing?path=/python/graphrag/graphrag/indexing/verbs/spread_json.py)