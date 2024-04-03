---
title: genid
navtitle: genid
layout: page
tags: [post, verb]
---
Generate a unique id for each row in the tabular data.

## Usage
### json
```json
{
    "verb": "genid",
    "args": {
        "to": "id_output_column_name", /* The name of the column to output the id to */
        "method": "md5_hash", /* The method to use to generate the id */
        "hash": ["list", "of", "column", "names"] /* only if using md5_hash */,
        "seed": 034324 /* The random seed to use with UUID */
    }
}
```

### yaml
```yaml
verb: genid
args:
    to: id_output_column_name
    method: md5_hash
    hash:
        - list
        - of
        - column
        - names
    seed: 034324
```

## Code
[genid.py](https://dev.azure.com/msresearch/Resilience/_git/ire-indexing?path=/python/graphrag/graphrag/indexing/verbs/genid.py)