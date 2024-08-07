import inspect

from graphrag.config import defaults
from graphrag.config.models import (
    CacheConfig,
    ChunkingConfig,
    ClaimExtractionConfig,
    ClusterGraphConfig,
    CommunityReportsConfig,
    EmbedGraphConfig,
    EntityExtractionConfig,
    GlobalSearchConfig,
    InputConfig,
    LLMParameters,
    LocalSearchConfig,
    ParallelizationParameters,
    ReportingConfig,
    SnapshotsConfig,
    StorageConfig,
    SummarizeDescriptionsConfig,
    TextEmbeddingConfig,
    UmapConfig,
)

config_list = [
    CacheConfig,
    ChunkingConfig,
    ClaimExtractionConfig,
    ClusterGraphConfig,
    CommunityReportsConfig,
    EmbedGraphConfig,
    EntityExtractionConfig,
    GlobalSearchConfig,
    InputConfig,
    LLMParameters,
    LocalSearchConfig,
    ParallelizationParameters,
    ReportingConfig,
    SnapshotsConfig,
    StorageConfig,
    SummarizeDescriptionsConfig,
    TextEmbeddingConfig,
    UmapConfig
]

class_cfg_mapping = {
    "CacheConfig": "cache",
    "ChunkingConfig": "chunk",
    "ClaimExtractionConfig": "claim_extraction",
    "ClusterGraphConfig": "cluster_graph",
    "CommunityReportsConfig": "community_report",
    "EmbedGraphConfig": "NODE2VEC",
    "EntityExtractionConfig": "entity_extraction",
    "GlobalSearchConfig": "global_search",
    "InputConfig": "input",
    "LLMParameters": "llm",
    "LocalSearchConfig": "local_search",
    "ParallelizationParameters": "parallelization",
    "ReportingConfig": "reporting",
    "SnapshotsConfig": "snapshots",
    "StorageConfig": "storage",
    "SummarizeDescriptionsConfig": "summarize_descriptions",
    "TextEmbeddingConfig": "embeddings",
    "UmapConfig": "umap"
}


def merge_config(domain_config, final_config):
    """
    Merge the domain config with the final config.

    Args:
        domain_config: The domain config.
        final_config: The final config.

    Returns:
        The merged config.
    """

    for key, value in dict(final_config).items():
        if type(value) in config_list:
            final_item = value
            domain_item = getattr(domain_config, key, None)
            if domain_item:
                modify_item = merge_config(domain_item, final_item)
                setattr(final_config, key, modify_item)
        else:
            final_value = value
            domain_value = getattr(domain_config, key, None)
            # judge final_value whether equals to default
            if key in ['max_cluster_size']:  # special case
                default_attr_name = key.upper()
            else:
                class_cfg_name = class_cfg_mapping.get(type(final_config).__name__) or ''
                default_attr_name = f"{class_cfg_name.upper()}_{key.upper()}"
            default_value = getattr(defaults, default_attr_name, None)

            if final_value == default_value:
                setattr(final_config, key, domain_value)

    return final_config
