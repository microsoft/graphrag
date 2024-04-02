# GraphRAG

👉 [Check out our docsite!](https://ashy-glacier-0caaba110.4.azurestaticapps.net)

## Overview

The GraphRAG project a data pipeline and transformation suite that is designed to extract meaningful, structured data from unstructured text using the power of LLMs.

## Repository Guidance
This repository presents a methodology for using knowledge graph memory structures to enhance LLM outputs. Please note that the provided code serves as a demonstration and is not an officially supported Microsoft offering.

## Quick Start

```python
pip install graphrag

mkdir -p ./ragtest/input
# A Christmas Carol by Charles Dickens
curl https://www.gutenberg.org/cache/epub/24022/pg24022.txt > ./ragtest/input/book.txt

# Set up the environment
set GRAPHRAG_API_KEY="<Your OpenAI API Key>"
set GRAPHRAG_INPUT_TYPE="text"

# For Azure OpenAI Users
set GRAPHRAG_API_BASE="http://<domain>.openai.azure.com"
set GRAPHRAG_LLM_DEPLOYMENT_NAME="gpt-4"
set GRAPHRAG_EMBEDDING_DEPLOYMENT_NAME="text-embedding-3-small"

# Run the indexer
python -m graphrag.index --root ./ragtest

# Ask some questions!
python -m graphrag.query \
--data ./ragtest/output/<timestamp>/artifacts \
--method global\
"What are the top themes in this story?"

python -m graphrag.query \
--data ./ragtest/output/<timestamp>/artifacts \
--method local \
"Who is Scrooge, and what are his main relationships?"
```

## Diving Deeper

- To read more about the indexing library, see [python/graphrag/README.md](./python/graphrag/README.md)
- To start developing _GraphRAG_, see [DEVELOPING.md](./DEVELOPING.md)

## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft
trademarks or logos is subject to and must follow
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.
