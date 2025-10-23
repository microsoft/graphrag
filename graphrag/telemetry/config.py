"""Telemetry configuration for OpenTelemetry."""

import os
from dataclasses import dataclass
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file if present
OTEL_EXPORTER_OTLP_TRACES_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "http://localhost:9411/api/v2/spans")
@dataclass
class TelemetryConfig:
    """Configuration for OpenTelemetry telemetry."""
    
    # Telemetry control
    telemetry_disabled: bool = False
    
    # Service information
    service_name: str = "graphrag"
    service_version: str = "1.0.0"
    service_namespace: str = "microsoft.research"

    # observability configuration
    obs_endpoint: str = OTEL_EXPORTER_OTLP_TRACES_ENDPOINT
    
    # Tracing configuration
    enable_tracing: bool = True
    enable_metrics: bool = True
    enable_logging: bool = True
    
    # Sampling configuration
    trace_sample_rate: float = 1.0  # Sample 100% of traces by default
    
    # Resource attributes
    deployment_environment: str = "development"
    
    @classmethod
    def from_env(cls) -> "TelemetryConfig":
        """Create configuration from environment variables."""
        return cls(
            service_name=os.getenv("OTEL_SERVICE_NAME", "graphrag"),
            service_version=os.getenv("OTEL_SERVICE_VERSION", "1.0.0"),
            service_namespace=os.getenv("OTEL_SERVICE_NAMESPACE", "microsoft.research"),
            obs_endpoint=os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "http://localhost:9411/api/v2/spans"),
            enable_tracing=os.getenv("OTEL_ENABLE_TRACING", "true").lower() == "true",
            enable_metrics=os.getenv("OTEL_ENABLE_METRICS", "true").lower() == "true",
            enable_logging=os.getenv("OTEL_ENABLE_LOGGING", "true").lower() == "true",
            trace_sample_rate=float(os.getenv("OTEL_TRACE_SAMPLE_RATE", "1.0")),
            deployment_environment=os.getenv("OTEL_DEPLOYMENT_ENVIRONMENT", "development"),
        )


def is_telemetry_disabled() -> bool:
    """Check if telemetry is disabled via environment variable."""
    return os.getenv("GRAPHRAG_DISABLE_TELEMETRY", "true").lower() == "true"