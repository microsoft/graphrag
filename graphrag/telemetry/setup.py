"""OpenTelemetry setup and configuration."""

import logging
from typing import Optional

from opentelemetry import trace, metrics
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
try:
    from opentelemetry.exporter.zipkin.json import ZipkinExporter
    ZIPKIN_AVAILABLE = True
except ImportError:
    ZIPKIN_AVAILABLE = False
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file if present
import os, grpc
USE_ZIPKIN = os.getenv("USE_ZIPKIN", "false")

from .config import TelemetryConfig

logger = logging.getLogger(__name__)

_telemetry_initialized = False
_tracer_provider: Optional[TracerProvider] = None
_meter_provider: Optional[MeterProvider] = None


def setup_telemetry(config: Optional[TelemetryConfig] = None) -> None:
    """Set up OpenTelemetry tracing and metrics."""
    global _telemetry_initialized, _tracer_provider, _meter_provider
    
    if _telemetry_initialized:
        logger.warning("Telemetry already initialized, skipping setup")
        return
    
    if config is None:
        config = TelemetryConfig.from_env()
    
    logger.info(f"Setting up telemetry for service: {config.service_name}")
    
    # Create resource with service information
    resource = Resource.create({
        "microsoft.resourceId": config.microsoft_resource_id,
        "service.name": config.service_name,
        "service.version": config.service_version,
        "service.namespace": config.service_namespace,
        "deployment.environment": config.deployment_environment,
    })
    
    # Set up tracing
    if config.enable_tracing:
        _setup_tracing(config, resource)
    
    # Set up metrics
    if config.enable_metrics:
        _setup_metrics(config, resource)
    
    # Set up automatic instrumentation
    _setup_instrumentation()
    
    _telemetry_initialized = True
    logger.info("Telemetry setup completed successfully")

def _get_credentials():
    """Get credentials for OpenTelemetry exporter."""
    # Check if deployment is aldo, set no auth mode
    if USE_ZIPKIN.lower() == "true":
        isInSecure = True
        credentials = None
        return credentials, isInSecure

    # Load the root certificate for TLS
    try:
        with open('./certs/root-certs.pem', 'rb') as cert_file:
            root_cert = cert_file.read()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        root_cert = None

    # Create TLS credentials if certificate is found, otherwise print error
    if root_cert:
        credentials = grpc.ssl_channel_credentials(root_cert)
        isInSecure = False
    else:
        logger.error("Root certificate not found. Continuing without Observability")
        credentials = None
        isInSecure = True
        # raise RuntimeError("Root certificate not found.")
    return credentials, isInSecure

def _setup_tracing(config: TelemetryConfig, resource: Resource) -> None:
    """Set up OpenTelemetry tracing."""
    global _tracer_provider
    
    # Create tracer provider with sampling
    sampler = TraceIdRatioBased(config.trace_sample_rate)
    _tracer_provider = TracerProvider(resource=resource, sampler=sampler)

    # Choose exporter based on USE_ZIPKIN setting
    if USE_ZIPKIN.lower() == "true":
        # Use Zipkin exporter for local development/testing
        if ZIPKIN_AVAILABLE:
            exporter = ZipkinExporter(endpoint=config.obs_endpoint)
            logger.info(f"Tracing configured with Zipkin endpoint: {config.obs_endpoint}")
        else:
            logger.warning("Zipkin exporter not available. Install with: pip install opentelemetry-exporter-zipkin-json")
            logger.info("Falling back to OTLP exporter")
            credentials, isInSecure = _get_credentials()
            exporter = OTLPSpanExporter(
                endpoint=config.obs_endpoint,
                credentials=credentials,
                insecure=isInSecure
            )
    else:
        # Use OTLP exporter for production
        credentials, isInSecure = _get_credentials()
        exporter = OTLPSpanExporter(
            endpoint=config.obs_endpoint,
            credentials=credentials,
            insecure=isInSecure
        )
        logger.info(f"Tracing configured with OTLP endpoint: {config.obs_endpoint}")
    
    # Create span processor with the chosen exporter
    span_processor = BatchSpanProcessor(exporter)
    _tracer_provider.add_span_processor(span_processor)
    
    # Set the global tracer provider
    trace.set_tracer_provider(_tracer_provider)


def _setup_metrics(config: TelemetryConfig, resource: Resource) -> None:
    """Set up OpenTelemetry metrics."""
    global _meter_provider
    
    # Create meter provider
    _meter_provider = MeterProvider(resource=resource)
    
    # Set the global meter provider
    metrics.set_meter_provider(_meter_provider)
    
    logger.info("Metrics configured")


def _setup_instrumentation() -> None:
    """Set up automatic instrumentation for common libraries."""
    try:
        # Instrument HTTP clients
        HTTPXClientInstrumentor().instrument()
        AioHttpClientInstrumentor().instrument()
        
        logger.info("Automatic instrumentation configured")
    except Exception as e:
        logger.warning(f"Failed to set up some instrumentation: {e}")


def shutdown_telemetry() -> None:
    """Shutdown telemetry providers and flush any remaining data."""
    global _telemetry_initialized, _tracer_provider, _meter_provider
    
    if not _telemetry_initialized:
        return
    
    logger.info("Shutting down telemetry")
    
    # Shutdown tracer provider
    if _tracer_provider:
        _tracer_provider.shutdown()
        _tracer_provider = None
    
    # Shutdown meter provider
    if _meter_provider:
        _meter_provider.shutdown()
        _meter_provider = None
    
    _telemetry_initialized = False
    logger.info("Telemetry shutdown completed")


def get_tracer(name: str) -> trace.Tracer:
    """Get a tracer instance."""
    return trace.get_tracer(name)


def get_meter(name: str) -> metrics.Meter:
    """Get a meter instance."""
    return metrics.get_meter(name)
