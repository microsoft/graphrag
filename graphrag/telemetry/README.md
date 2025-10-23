# OpenTelemetry and Zipkin Integration for LazyGraphRAG

This module provides comprehensive observability for LazyGraphRAG using OpenTelemetry with Zipkin as the tracing backend.

## Features

- **Automatic tracing** of API calls, workflows, and storage operations
- **Zipkin integration** for distributed tracing visualization
- **Configurable sampling** and filtering
- **Sensitive data protection** in trace attributes
- **Easy setup** with environment variable configuration
- **Graceful degradation** if telemetry setup fails

## Quick Start

### 1. Install Dependencies

Dependencies are automatically included in the project via `pyproject.toml`:

```toml
dependencies = [
    # ... other dependencies
    "opentelemetry-api>=1.23.0",
    "opentelemetry-sdk>=1.23.0",
    "opentelemetry-exporter-zipkin-json>=1.23.0",
    "opentelemetry-instrumentation>=0.44b0",
    "opentelemetry-instrumentation-httpx>=0.44b0",
    "opentelemetry-instrumentation-aiohttp-client>=0.44b0"
]
```

### 2. Start Zipkin

Run Zipkin using Docker:

```bash
docker run -d -p 9411:9411 openzipkin/zipkin
```

Zipkin UI will be available at: http://localhost:9411/zipkin

### 3. Use LazyGraphRAG (Automatic Setup)

Telemetry is automatically enabled when you import LazyGraphRAG:

```python
from lazy_graphrag.api.index import build_index
from lazy_graphrag.api.query import lazy_search

# Telemetry is automatically set up!
# Your operations will be traced to Zipkin
```

### 4. View Traces

Open http://localhost:9411/zipkin and look for traces with service name `lazy-graphrag`.

## Configuration

### Environment Variables

Configure telemetry using environment variables:

```bash
# Service identification
export OTEL_SERVICE_NAME="my-graphrag-app"
export OTEL_SERVICE_VERSION="1.0.0"
export OTEL_SERVICE_NAMESPACE="my-company"

# Zipkin configuration
export OTEL_EXPORTER_OTLP_TRACES_ENDPOINT="http://localhost:9411/api/v2/spans"

# Tracing configuration
export OTEL_ENABLE_TRACING="true"
export OTEL_ENABLE_METRICS="true"
export OTEL_TRACE_SAMPLE_RATE="1.0"  # Sample 100% of traces

# Environment
export OTEL_DEPLOYMENT_ENVIRONMENT="production"

# Disable telemetry completely (if needed)
export LAZY_GRAPHRAG_DISABLE_TELEMETRY="false"
```

### Programmatic Configuration

```python
from lazy_graphrag.telemetry import TelemetryConfig, setup_telemetry

config = TelemetryConfig(
    service_name="my-graphrag-service",
    service_version="2.0.0",
    obs_endpoint="http://my-zipkin:9411/api/v2/spans",
    trace_sample_rate=0.1,  # Sample 10% of traces
    deployment_environment="production"
)

setup_telemetry(config)
```

## Tracing Coverage

### Automatically Traced Operations

The following operations are automatically traced:

1. **API Operations**
   - `build_index()` - Complete indexing pipeline with `@trace_operation` decorator
   - Query processing operations

2. **Workflow Operations**
   - `create_communities` - Community detection workflow with `@trace_workflow` decorator
   - `load_input_documents` - Document loading workflow with `@trace_workflow` decorator
   - Other workflows can be traced by adding `@trace_workflow("workflow_name")` decorator

3. **Search Operations**
   - `local_search()` - Local search with `@trace_search_operation` decorator
   - `global_search()` - Global search with `@trace_search_operation` decorator
   - `drift_search()` - DRIFT search (can be instrumented)
   - `basic_search()` - Basic search (can be instrumented)

4. **Storage Operations** (via automatic instrumentation)
   - PostgreSQL operations
   - HTTP requests to external services
   - AsyncPG database operations

5. **Vector Store Operations** (via automatic instrumentation)
   - Milvus vector operations
   - HTTP client requests

### Custom Tracing

Add tracing to your own functions:

```python
from graphrag.telemetry.decorators import (
    trace_operation,
    trace_workflow,
    trace_vector_store_operation,
    trace_llm_operation,
    trace_search_operation,
    trace_retrieval_operation
)

@trace_operation("my_custom_function")
async def my_function():
    """This function will be traced."""
    pass

@trace_workflow("data_processing")
async def process_data():
    """Workflow-specific tracing for indexing workflows."""
    pass

@trace_search_operation("custom_search")
async def custom_search():
    """Search operation tracing."""
    pass

@trace_vector_store_operation("search")
async def vector_search():
    """Vector store operation tracing."""
    pass

@trace_llm_operation("gpt-4")
async def call_llm():
    """LLM operation tracing."""
    pass

@trace_retrieval_operation("l1_ranking")
async def retrieval_operation():
    """Retrieval operation tracing."""
    pass
```

### Adding Telemetry to New Workflows

To add telemetry to a new workflow in `graphrag/index/workflows/`:

1. Import the decorator:
   ```python
   from graphrag.telemetry.decorators import trace_workflow
   ```

2. Add the decorator to the `run_workflow` function:
   ```python
   @trace_workflow("workflow_name")
   async def run_workflow(config: GraphRagConfig, context: PipelineRunContext) -> WorkflowFunctionOutput:
       # Your workflow code here
       pass
   ```

### Adding Telemetry to New Search Operations

To add telemetry to a new search operation in `graphrag/query/structured_search/`:

1. Import the decorator:
   ```python
   from graphrag.telemetry.decorators import trace_search_operation
   ```

2. Add the decorator to the `search` method:
   ```python
   @trace_search_operation("search_type_name")
   async def search(self, query: str, **kwargs) -> SearchResult:
       # Your search code here
       pass
   ```

## Trace Attributes

Traces include rich metadata:

### Automatic Attributes

- `service.name` - Service name
- `service.version` - Service version  
- `service.namespace` - Service namespace
- `deployment.environment` - Environment (dev/staging/prod)
- `function.name` - Function being traced
- `function.module` - Module containing the function
- `component` - Component type (api, workflow, storage, etc.)

### Function Arguments

Function arguments are automatically captured as attributes:

- **Simple types** (str, int, float, bool) - Full value
- **Collections** (list, tuple, dict) - Length/count only
- **Sensitive data** - Automatically redacted (passwords, tokens, keys, etc.)

### Custom Attributes

Add custom attributes to traces:

```python
from lazy_graphrag.telemetry.setup import get_tracer
from opentelemetry import trace

tracer = get_tracer(__name__)

with tracer.start_as_current_span("my_operation") as span:
    span.set_attribute("custom.attribute", "value")
    span.set_attribute("document.count", 150)
    # Your code here
```

## Security and Privacy

### Automatic Data Protection

The telemetry system automatically protects sensitive data:

- **Redacted parameters**: Any parameter containing `password`, `token`, `key`, `secret`, `auth`, or `credential`
- **Redacted values**: Replaced with `[REDACTED]` in traces
- **Collection sizes only**: Lists/dicts show count, not contents

### Disabling Telemetry

Completely disable telemetry:

```bash
export LAZY_GRAPHRAG_DISABLE_TELEMETRY="true"
```

Or disable specific features:

```bash
export OTEL_ENABLE_TRACING="false"
export OTEL_ENABLE_METRICS="false"
```

## Troubleshooting

### Common Issues

1. **No traces in Zipkin**
   - Check Zipkin is running: `curl http://localhost:9411/api/v2/services`
   - Verify endpoint: `echo $OTEL_EXPORTER_OTLP_TRACES_ENDPOINT`
   - Check sampling rate: `echo $OTEL_TRACE_SAMPLE_RATE`

2. **Telemetry setup failures**
   - Check logs for warning messages
   - Telemetry failures don't stop LazyGraphRAG execution
   - Verify OpenTelemetry dependencies are installed

3. **High overhead**
   - Reduce sampling rate: `export OTEL_TRACE_SAMPLE_RATE="0.1"`
   - Disable if not needed: `export LAZY_GRAPHRAG_DISABLE_TELEMETRY="true"`

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger("lazy_graphrag.telemetry").setLevel(logging.DEBUG)
```

### Health Check

Verify telemetry setup:

```python
from lazy_graphrag.telemetry.setup import get_tracer

tracer = get_tracer("test")
with tracer.start_as_current_span("health_check") as span:
    span.set_attribute("test", "working")
    print("Telemetry is working!")
```

## Architecture

### Components

- **`config.py`** - Configuration management
- **`setup.py`** - OpenTelemetry initialization and providers
- **`decorators.py`** - Tracing decorators and utilities
- **`__init__.py`** - Public API and auto-setup

### Flow

1. **Import** → Auto-setup telemetry (unless disabled)
2. **Function Call** → Decorator creates span
3. **Execution** → Attributes added, exceptions recorded
4. **Completion** → Span exported to Zipkin
5. **Visualization** → View in Zipkin UI

## Example: Complete Workflow

```python
import asyncio
from lazy_graphrag.api.index import build_index
from lazy_graphrag.config.load_config import load_config

async def main():
    # Load config
    config = load_config("config.yaml", ".")
    
    # Build index (automatically traced)
    results = await build_index(config=config)
    
    print("Check Zipkin for traces: http://localhost:9411/zipkin")

if __name__ == "__main__":
    asyncio.run(main())
```

## Advanced Usage

### Custom Exporter

Use a different exporter:

```python
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# In your setup code
jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=6831,
)
span_processor = BatchSpanProcessor(jaeger_exporter)
```

### Metrics Integration

Add custom metrics:

```python
from lazy_graphrag.telemetry.setup import get_meter

meter = get_meter(__name__)
counter = meter.create_counter("custom_operations")

counter.add(1, {"operation": "data_load"})
```

### Sampling Strategies

Implement custom sampling:

```python
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased, ParentBased

# Custom sampler
sampler = ParentBased(root=TraceIdRatioBased(0.1))  # 10% sampling
```

For more information, see the [OpenTelemetry Python documentation](https://opentelemetry.io/docs/instrumentation/python/).
