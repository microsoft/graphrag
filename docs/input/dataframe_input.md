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
from graphrag.api import index_dataframe

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

# Index the DataFrame with GraphRAG
await index_dataframe(
    input_dataframe=documents_df,
    output_dir="./output",
    text_column="text",
    title_column="title",
    metadata_columns=["source", "category"]
)
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

## API Reference

### `index_dataframe`

```python
async def index_dataframe(
    input_dataframe: pd.DataFrame,
    output_dir: str | Path,
    config_path: str | Path | None = None,
    config_data: dict[str, Any] | None = None,
    text_column: str = "text",
    title_column: str | None = "title", 
    metadata_columns: list[str] | None = None,
    method: IndexingMethod | str = IndexingMethod.Standard,
    progress_logger: ProgressLogger | None = None,
) -> None
```

#### Parameters

- **`input_dataframe`**: The pandas DataFrame containing documents to index
- **`output_dir`**: Directory where indexing outputs will be saved
- **`config_path`**: Optional path to GraphRAG configuration file
- **`config_data`**: Optional configuration data as dictionary
- **`text_column`**: Name of column containing document text (default: "text")
- **`title_column`**: Name of column containing document titles (default: "title")
- **`metadata_columns`**: List of column names to preserve as metadata
- **`method`**: Indexing method to use (Standard, Fast, etc.)
- **`progress_logger`**: Optional progress logger instance

## Configuration

You can provide GraphRAG configuration in two ways:

### 1. Configuration File

```python
await index_dataframe(
    input_dataframe=df,
    output_dir="./output",
    config_path="./settings.yaml"  # Your existing GraphRAG config
)
```

### 2. Configuration Dictionary

```python
config = {
    "llm": {
        "api_key": "your-api-key",
        "model": "gpt-4-turbo-preview"
    },
    "embeddings": {
        "api_key": "your-api-key", 
        "model": "text-embedding-3-small"
    }
}

await index_dataframe(
    input_dataframe=df,
    output_dir="./output",
    config_data=config
)
```

## Custom File Loader Example

Here's an example of how you might implement a custom file loader:

```python
import pandas as pd
from pathlib import Path
import PyPDF2
from bs4 import BeautifulSoup
import markdown

class CustomFileLoader:
    def __init__(self):
        self.loaders = {
            '.pdf': self.load_pdf,
            '.html': self.load_html,
            '.htm': self.load_html,
            '.xml': self.load_xml,
            '.md': self.load_markdown,
            '.txt': self.load_text
        }
    
    def load_pdf(self, file_path: Path) -> dict:
        """Extract text from PDF file."""
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        
        return {
            "text": text,
            "title": file_path.stem,
            "source": str(file_path),
            "file_type": "pdf"
        }
    
    def load_html(self, file_path: Path) -> dict:
        """Extract text from HTML file."""
        with open(file_path, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file.read(), 'html.parser')
            text = soup.get_text()
        
        return {
            "text": text,
            "title": soup.title.string if soup.title else file_path.stem,
            "source": str(file_path),
            "file_type": "html"
        }
    
    def load_markdown(self, file_path: Path) -> dict:
        """Convert Markdown to text."""
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            # Convert to HTML then extract text
            html = markdown.markdown(content)
            soup = BeautifulSoup(html, 'html.parser')
            text = soup.get_text()
        
        return {
            "text": text,
            "title": file_path.stem,
            "source": str(file_path),
            "file_type": "markdown"
        }
    
    def load_directory(self, directory: Path) -> pd.DataFrame:
        """Load all supported files from a directory."""
        documents = []
        
        for file_path in directory.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in self.loaders:
                try:
                    loader = self.loaders[file_path.suffix.lower()]
                    doc = loader(file_path)
                    doc["creation_date"] = file_path.stat().st_mtime
                    documents.append(doc)
                except Exception as e:
                    print(f"Error loading {file_path}: {e}")
        
        return pd.DataFrame(documents)

# Usage
loader = CustomFileLoader()
df = loader.load_directory(Path("./documents"))

# Index with GraphRAG
await index_dataframe(
    input_dataframe=df,
    output_dir="./output",
    metadata_columns=["source", "file_type", "creation_date"]
)
```

## Best Practices

### Data Preparation

1. **Clean Text**: Ensure your text content is clean and properly formatted
2. **Chunking**: For very large documents, consider splitting them into smaller chunks
3. **Encoding**: Ensure proper text encoding to avoid character issues
4. **Deduplication**: Remove duplicate documents if necessary

### Column Configuration

1. **Text Column**: Should contain the main content you want to index
2. **Title Column**: Should be descriptive and unique per document
3. **Metadata**: Include relevant metadata that might be useful for querying

### Performance Considerations

1. **Memory Usage**: Large DataFrames may consume significant memory
2. **Batch Processing**: For very large datasets, consider processing in batches
3. **Parallel Processing**: Use multiple workers if your file loader supports it

## Error Handling

The DataFrame input system will validate your data and provide helpful error messages:

```python
# Missing required column
ValueError: Text column 'content' not found in input dataframe

# Empty dataframe
ValueError: Input dataframe is empty

# Invalid configuration
ValueError: No 'text' column found in input dataframe and no text_column configured
```

## Integration with Existing Workflows

The DataFrame input feature is fully compatible with existing GraphRAG workflows:

- Use the same configuration files and settings
- All output formats remain the same
- Query APIs work identically with DataFrame-indexed data
- Compatible with all indexing methods (Standard, Fast, etc.)

## Complete Example

See `examples/dataframe_input_example.py` for a complete working example that demonstrates:

- Creating a sample DataFrame from various file types
- Configuring the indexing process
- Error handling and validation
- Custom file loader implementation patterns 