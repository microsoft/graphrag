# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from __future__ import annotations

import os
import pathlib
import typing

import pandas as pd
import tiktoken
import typing_extensions

from . import _base, _defaults, _utils
from .. import _builders
from ... import _llm
from .... import _utils as _common_utils


class LocalContextLoader(_base.BaseContextLoader):
    """
    LocalContextLoader is responsible for loading various components (such as
    nodes, entities, community reports, text units, relationships, and
    covariates) from data files, typically in Parquet format, and preparing them
    for use in constructing a LocalContextBuilder. It serves as an interface
    between data sources and the context builder for local search in the
    GraphRAG framework.

    Attributes:
        _nodes: A DataFrame containing the graph nodes.
        _entities:
            A DataFrame containing the graph entities (nodes with specific
            properties).
        _community_reports:
            A DataFrame containing community reports from the graph index.
        _text_units:
            A DataFrame containing text units related to the entities and
            reports.
        _relationships:
            A DataFrame containing relationships (edges) between entities in
            the graph.
        _covariates:
            An optional DataFrame containing covariates (claims) associated with
            entities.
    """
    _nodes: pd.DataFrame
    _entities: pd.DataFrame
    _community_reports: pd.DataFrame
    _text_units: pd.DataFrame
    _relationships: pd.DataFrame
    _covariates: typing.Optional[pd.DataFrame] = None

    @property
    def nodes(self) -> pd.DataFrame:
        return self._nodes

    @property
    def entities(self) -> pd.DataFrame:
        return self._entities

    @property
    def community_reports(self) -> pd.DataFrame:
        return self._community_reports

    @property
    def text_units(self) -> pd.DataFrame:
        return self._text_units

    @property
    def relationships(self) -> pd.DataFrame:
        return self._relationships

    @property
    def covariates(self) -> typing.Optional[pd.DataFrame]:
        return self._covariates

    @classmethod
    @typing_extensions.override
    def from_parquet_directory(
        cls,
        directory: typing.Union[str, os.PathLike[str], pathlib.Path],
        nodes_file: typing.Optional[str] = None,
        entities_file: typing.Optional[str] = None,
        community_reports_file: typing.Optional[str] = None,
        text_units_file: typing.Optional[str] = None,
        relationships_file: typing.Optional[str] = None,
        covariates_file: typing.Optional[str] = None,
        **kwargs: typing.Any
    ) -> typing.Self:
        """
        Loads context data from a directory containing Parquet files.

        This method reads various data components from the specified directory
        and creates a LocalContextLoader instance. Each file can either be
        provided explicitly or default filenames will be used.

        Args:
            directory: The path to the directory containing the Parquet files.
            nodes_file:
                Optional filename for the nodes' data. If not provided, the
                default filename is used.
            entities_file:
                Optional filename for the entities' data. If not provided, the
                default filename is used.
            community_reports_file:
                Optional filename for the community reports data. If not
                provided, the default filename is used.
            text_units_file:
                Optional filename for the text units data. If not provided, the
                default filename is used.
            relationships_file:
                Optional filename for the relationships' data. If not provided,
                the default filename is used.
            covariates_file:
                Optional filename for the covariates data. If not provided, the
                default filename is used.
            **kwargs: Additional arguments for future extensibility.

        Returns:
            A LocalContextLoader instance with the loaded data.
        """
        if not directory:
            raise ValueError("Directory not provided")
        directory = pathlib.Path(directory)
        if not directory.exists() or not directory.is_dir():
            raise FileNotFoundError(f"Directory not found: {directory}")

        nodes = pd.read_parquet(directory / (nodes_file or _defaults.PARQUET_FILE_NAME__NODES))
        entities = pd.read_parquet(directory / (entities_file or _defaults.PARQUET_FILE_NAME__ENTITIES))
        community_reports = pd.read_parquet(
            directory / (community_reports_file or _defaults.PARQUET_FILE_NAME__COMMUNITY_REPORTS)
        )

        text_units = pd.read_parquet(directory / (text_units_file or _defaults.PARQUET_FILE_NAME__TEXT_UNITS))
        relationships = pd.read_parquet(
            directory / (relationships_file or _defaults.PARQUET_FILE_NAME__RELATIONSHIPS)
        )
        covariates_path = directory / (covariates_file or _defaults.PARQUET_FILE_NAME__COVARIATES)
        covariates = pd.read_parquet(covariates_path) if covariates_path.exists() else None
        return cls(
            nodes=nodes,
            entities=entities,
            community_reports=community_reports,
            text_units=text_units,
            relationships=relationships,
            covariates=covariates,
        )

    def __init__(
        self,
        *,
        nodes: pd.DataFrame,
        entities: pd.DataFrame,
        community_reports: pd.DataFrame,
        text_units: pd.DataFrame,
        relationships: pd.DataFrame,
        covariates: typing.Optional[pd.DataFrame],
    ) -> None:
        self._nodes = nodes
        self._entities = entities
        self._community_reports = community_reports
        self._text_units = text_units
        self._relationships = relationships
        self._covariates = covariates

    @typing_extensions.override
    def to_context_builder(
        self,
        community_level: int,
        embedder: _llm.BaseEmbedding,
        store_coll_name: str,
        store_uri: str,
        encoding_model: str,
        **kwargs: typing.Any
    ) -> _builders.LocalContextBuilder:
        """
        Converts the loaded data into a LocalContextBuilder for constructing
        search contexts.

        This method processes the loaded nodes, entities, community reports,
        text units, relationships, and covariates, then creates a
        LocalContextBuilder instance, which can be used to build context for
        local search in the GraphRAG framework.

        Args:
            community_level: The level of community data to include.
            embedder: The text embedding model to use for embedding the entities.
            store_coll_name:
                The name of the collection in the vector store where entity
                embeddings are stored.
            store_uri: The URI for connecting to the vector store.
            encoding_model: The model used for token encoding.
            **kwargs:
                Additional keyword arguments, can be prefixed with 'entities__'
                for `_utils.get_entities`, 'community_reports__' for
                `_utils.get_community_reports`, 'text_units__' for
                `_utils.get_text_units`, 'relationships__' for
                `_utils.get_relationships`, and 'covariates__' for
                `_utils.get_covariates`. See details in the specific method
                documentation and source code.

        Returns:
            A LocalContextBuilder instance ready for building local search
            contexts.
        """
        entities_list = _utils.get_entities(
            nodes=self._nodes,
            entities=self._entities,
            community_level=community_level,
            **_common_utils.filter_kwargs(_utils.get_entities, kwargs, prefix="entities__")
        )
        community_reports_list = _utils.get_community_reports(
            community_reports=self._community_reports,
            nodes=self._nodes,
            community_level=community_level,
            **_common_utils.filter_kwargs(_utils.get_community_reports, kwargs, prefix="community_reports__")
        )
        text_units_list = _utils.get_text_units(
            text_units=self._text_units,
            **_common_utils.filter_kwargs(_utils.get_text_units, kwargs, prefix="text_units__")
        )
        relationships_list = _utils.get_relationships(
            relationships=self._relationships,
            **_common_utils.filter_kwargs(_utils.get_relationships, kwargs, prefix="relationships__")
        )
        covariates_dict = {
            "claims": _utils.get_covariates(
                self._covariates,
                **_common_utils.filter_kwargs(_utils.get_covariates, kwargs, prefix="covariates__")
            ) if self._covariates is not None else []
        }
        store = _utils.get_store(entities_list, coll_name=store_coll_name, uri=store_uri)
        return _builders.LocalContextBuilder(
            entities=entities_list,
            entity_text_embeddings=store,
            community_reports=community_reports_list,
            text_units=text_units_list,
            relationships=relationships_list,
            covariates=covariates_dict,
            text_embedder=embedder,
            token_encoder=tiktoken.get_encoding(encoding_model),
        )

    @typing_extensions.override
    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}(\n"
            f"\tnum_nodes={len(self._nodes)}, \n"
            f"\tnum_entities={len(self._entities)}, \n"
            f"\tnum_community_reports={len(self._community_reports)}, \n"
            f"\tnum_text_units={len(self._text_units)}, \n"
            f"\tnum_relationships={len(self._relationships)}, \n"
            f"\tnum_covariates={self._covariates and len(self._covariates) or 0}\n"
            f")"
        )

    @typing_extensions.override
    def __repr__(self) -> str:
        return self.__str__()


class GlobalContextLoader(_base.BaseContextLoader):
    """
    GlobalContextLoader is responsible for loading nodes, entities, and
    community reports from data files (typically in Parquet format) and
    preparing them for use in constructing a GlobalContextBuilder. It serves as
    an interface between data sources and the context builder for global search
    in the GraphRAG framework.

    Attributes:
        _nodes: A DataFrame containing the graph nodes.
        _entities:
            A DataFrame containing the graph entities (nodes with specific
            properties).
        _community_reports:
            A DataFrame containing community reports from the graph index.
    """
    _nodes: pd.DataFrame
    _entities: pd.DataFrame
    _community_reports: pd.DataFrame

    @property
    def nodes(self) -> pd.DataFrame:
        return self._nodes

    @property
    def entities(self) -> pd.DataFrame:
        return self._entities

    @property
    def community_reports(self) -> pd.DataFrame:
        return self._community_reports

    @classmethod
    @typing_extensions.override
    def from_parquet_directory(
        cls,
        directory: typing.Union[str, os.PathLike[str], pathlib.Path],
        nodes_file: typing.Optional[str] = None,
        entities_file: typing.Optional[str] = None,
        community_reports_file: typing.Optional[str] = None,
        **kwargs: str
    ) -> typing.Self:
        """
        Loads global context data from a directory containing Parquet files.

        This method reads nodes, entities, and community reports from the
        specified directory and creates a GlobalContextLoader instance. If
        filenames are not provided, default filenames are used.

        Args:
            directory: The path to the directory containing the Parquet files.
            nodes_file:
                Optional filename for the nodes' data. If not provided, the
                default filename is used.
            entities_file:
                Optional filename for the entities' data. If not provided, the
                default filename is used.
            community_reports_file:
                Optional filename for the community reports data. If not
                provided, the default filename is used.
            **kwargs: Additional arguments for future extensibility.

        Returns:
            A GlobalContextLoader instance with the loaded data.
        """
        directory = pathlib.Path(directory)
        if not directory.exists() or not directory.is_dir():
            raise FileNotFoundError(f"Directory not found: {directory}")

        nodes = pd.read_parquet(
            directory / (nodes_file or _defaults.PARQUET_FILE_NAME__NODES)
        )
        entities = pd.read_parquet(
            directory / (entities_file or _defaults.PARQUET_FILE_NAME__ENTITIES)
        )
        community_reports = pd.read_parquet(
            directory / (community_reports_file or _defaults.PARQUET_FILE_NAME__COMMUNITY_REPORTS)
        )

        return cls(
            nodes=nodes,
            entities=entities,
            community_reports=community_reports,
        )

    @classmethod
    def from_local_context_loader(
        cls,
        local_context_loader: LocalContextLoader,
    ) -> GlobalContextLoader:
        """
        Creates a GlobalContextLoader from an existing LocalContextLoader.

        This method reuses the data loaded in a LocalContextLoader to initialize
        a GlobalContextLoader, avoiding the need to load data again.

        Args:
            local_context_loader:
                The LocalContextLoader instance whose data will be reused to
                initialize the GlobalContextLoader.

        Returns:
            A new instance initialized with the local context loader's data.
        """
        return cls(
            nodes=local_context_loader.nodes,
            entities=local_context_loader.entities,
            community_reports=local_context_loader.community_reports,
        )

    def __init__(
        self,
        *,
        nodes: pd.DataFrame,
        entities: pd.DataFrame,
        community_reports: pd.DataFrame,
    ) -> None:
        self._nodes = nodes
        self._entities = entities
        self._community_reports = community_reports

    @typing_extensions.override
    def to_context_builder(
        self,
        community_level: int,
        encoding_model: str,
        **kwargs: typing.Any
    ) -> _builders.GlobalContextBuilder:
        """
        Converts the loaded data into a GlobalContextBuilder for constructing
        global search contexts.

        This method processes the loaded nodes, entities, and community reports,
        then creates a GlobalContextBuilder instance, which can be used to build
        context for global search in the GraphRAG framework.

        Args:
            community_level: The level of community data to include.
            encoding_model: The model used for token encoding.
            **kwargs:
                Additional keyword arguments, can be prefixed with
                'entities__' for `_utils.get_entities` and 'community_reports__'
                for `_utils.get_community_reports`. See details in the specific
                method documentation and source code.

        Returns:
            A GlobalContextBuilder instance ready for building global search contexts.
        """
        community_reports_list = _utils.get_community_reports(
            community_reports=self._community_reports,
            nodes=self._nodes,
            community_level=community_level,
            **_common_utils.filter_kwargs(_utils.get_community_reports, kwargs, prefix="community_reports__")
        )
        entities_list = _utils.get_entities(
            nodes=self._nodes,
            entities=self._entities,
            community_level=community_level,
            **_common_utils.filter_kwargs(_utils.get_entities, kwargs, prefix="entities__")
        )
        return _builders.GlobalContextBuilder(
            community_reports=community_reports_list,
            entities=entities_list,
            token_encoder=tiktoken.get_encoding(encoding_model),
        )

    @typing_extensions.override
    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}(\n"
            f"\tnum_nodes={len(self._nodes)}, \n"
            f"\tnum_entities={len(self._entities)}, \n"
            f"\tnum_community_reports={len(self._community_reports)}\n"
            f")"
        )

    @typing_extensions.override
    def __repr__(self) -> str:
        return self.__str__()
