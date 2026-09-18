FROM python:3.11-slim

WORKDIR /app

# Copy GraphRAG code
COPY graphrag ./graphrag
COPY graphrag_api ./graphrag_api
COPY pyproject.toml .

# Install dependencies
RUN pip install --no-cache-dir -e .

# Expose port
EXPOSE 8000

# Run server
CMD ["python", "-m", "graphrag_api.server"]
