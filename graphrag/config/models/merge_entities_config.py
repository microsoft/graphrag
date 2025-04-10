"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

from graphrag.config.defaults import graphrag_config_defaults


class MergeEntitiesConfig(BaseModel):
    """The default configuration section for Node2Vec."""

    enabled: bool = Field(
        description="A flag indicating whether to enable merge entities workflow.",
        default=graphrag_config_defaults.merge_entities.enabled,
    )
    eps: float = Field(
        description="eps for DBSCAN clustering algorithm.",
        default=graphrag_config_defaults.merge_entities.eps,
    )
    min_samples: int = Field(
        description="min_samples for DBSCAN clustering algorithm.",
        default=graphrag_config_defaults.merge_entities.min_samples,
    )