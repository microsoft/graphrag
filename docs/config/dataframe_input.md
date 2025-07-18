# DataFrame Input Support

GraphRAG now supports using pandas DataFrames as input instead of files. This allows you to use your own custom file loaders that can process various file formats (PDF, HTML, XML, Markdown, etc.) and convert them to a standardized DataFrame format for GraphRAG processing.

## Overview

The DataFrame input feature enables you to:

- Use custom file loaders for unsupported file formats
- Preprocess and clean your data before indexing
- Combine data from multiple sources into a single DataFrame
- Have full control over the data transformation pipeline

## Basic Usage

```python
import pandas as pd
from graphrag.api import build_index

# Create your DataFrame (from your custom file loader)
documents_df = pd.DataFrame([
    {
        "text": "Your document content here...",
        "title": "Document Title",
        "source": "source_file.pdf",
        "category": "research"
    },
    # ... more documents
])

config = {
    "llm": {
        "api_key": "your-api-key",
        "model": "gpt-4-turbo-preview"
    },
    "embeddings": {
        "api_key": "your-api-key", 
        "model": "text-embedding-3-small"
    }
    "input":{
        "type": "file",
        "file_type": "dataframe",
        "dataframe": documents_df
    }
    # ... more settings
}

# Index the DataFrame with GraphRAG
await build_index(config)
```

## DataFrame Requirements

Your input DataFrame must have the following structure:

### Required Columns

- **Text Column**: Contains the main content of each document
  - Default name: `"text"`
  - Configurable via `text_column` parameter
  - Must contain string data

### Optional Columns

- **Title Column**: Contains document titles/names
  - Default name: `"title"`
  - Configurable via `title_column` parameter
  - If not provided, auto-generated titles will be used

- **Metadata Columns**: Any additional columns to preserve
  - Specified via `metadata_columns` parameter
  - Will be stored as metadata and available in the output

### Auto-Generated Columns

If not present in your DataFrame, these columns will be automatically added:

- **id**: Unique document identifier (hash of content)
- **creation_date**: Timestamp when the document was processed