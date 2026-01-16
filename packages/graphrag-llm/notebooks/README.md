To run the notebooks you need to add a `.env` file to the `notebooks` directory with the following information

```
GRAPHRAG_MODEL="..."
GRAPHRAG_EMBEDDING_MODEL="..."
GRAPHRAG_API_BASE="..."
# API Key and version are optional
# If not provided, Azure managed identity will be used
GRAPHRAG_API_KEY="..."
GRAPHRAG_API_VERSION="..."
```