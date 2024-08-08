from pathlib import Path
from typing import Tuple, Dict

import pandas as pd
import tiktoken

from graphrag.query.cli import __get_embedding_description_store, _configure_paths_and_settings
from graphrag.query.factories import get_llm, get_text_embedder
from graphrag.query.indexer_adapters import read_indexer_entities, read_indexer_relationships, read_indexer_covariates, read_indexer_reports, \
    read_indexer_text_units
from graphrag.query.input.loaders.dfs import store_entity_semantic_embeddings
from graphrag.query.llm.base import BaseLLM
from graphrag.query.structured_search.base import BaseSearch
from graphrag.query.structured_search.local_search.mixed_context import LocalSearchMixedContext
from graphrag.vector_stores import VectorStoreType
from plugins.webserver import consts
from plugins.webserver.config.create_final_config import create_final_config
from plugins.webserver.config.merge_config import merge_config
from plugins.webserver.config.final_config import FinalConfig
from plugins.webserver.types import ContextBuilder

from plugins.webserver.types.enums import DomainEnum, SearchModeEnum
from plugins.webserver.service.graphrag.local import build_local_search_engine


def load_universal_obj(config: FinalConfig):
    """
    Load the universal objects for search engine.
    """
    llm = get_llm(config)
    text_embedder = get_text_embedder(config)
    token_encoder = tiktoken.get_encoding(config.encoding_model)

    return llm, text_embedder, token_encoder


def load_data_files(data_dir, config: FinalConfig):
    """
    load data from data files in specified domain dir.
    """
    datas = dict()

    # load entity
    entity_df = pd.read_parquet(f"{data_dir}/{consts.ENTITY_TABLE}.parquet")
    entity_embedding_df = pd.read_parquet(f"{data_dir}/{consts.ENTITY_EMBEDDING_TABLE}.parquet")
    entities = read_indexer_entities(entity_df, entity_embedding_df, config.query.community_level)
    datas['entities'] = entities

    # load entity description embedding
    vector_store_args = (
        config.embeddings.vector_store if config.embeddings.vector_store else {}
    )
    vector_store_type = vector_store_args.get("type", VectorStoreType.LanceDB)
    description_embedding_store = __get_embedding_description_store(
        vector_store_type=vector_store_type,
        config_args=vector_store_args,
    )
    store_entity_semantic_embeddings(
        entities=entities, vectorstore=description_embedding_store
    )
    datas['entity_text_embeddings'] = description_embedding_store

    # load relationship
    relationship_df = pd.read_parquet(f"{data_dir}/{consts.RELATIONSHIP_TABLE}.parquet")
    relationships = read_indexer_relationships(relationship_df)
    datas['relationships'] = relationships

    # load covariate
    covariate_file = Path(f"{data_dir}/{consts.COVARIATE_TABLE}.parquet")
    if covariate_file.exists():
        covariate_df = pd.read_parquet(covariate_file)
        claims = read_indexer_covariates(covariate_df)
        covariates = {"claims": claims}
    else:
        covariates = None
    datas['covariates'] = covariates

    # load report
    report_df = pd.read_parquet(f"{data_dir}/{consts.COMMUNITY_REPORT_TABLE}.parquet")
    reports = read_indexer_reports(report_df, entity_df, config.query.community_level)
    datas['community_reports'] = reports

    # load text unit
    text_unit_df = pd.read_parquet(f"{data_dir}/{consts.TEXT_UNIT_TABLE}.parquet")
    text_units = read_indexer_text_units(text_unit_df)
    datas['text_units'] = text_units

    # load document
    documents_file = Path(f"{data_dir}/{consts.DOCUMENT_TABLE}.parquet")
    if documents_file.exists():
        documents_df = pd.read_parquet(documents_file)
    else:
        documents_df = None
    datas['documents'] = documents_df

    return datas


def build_search_engine(mode: SearchModeEnum, llm: BaseLLM, config: FinalConfig, token_encoder: tiktoken.Encoding, context_builder=None) -> BaseSearch:
    match mode:
        case SearchModeEnum.local:
            return build_local_search_engine(llm, config, token_encoder, context_builder)
        case SearchModeEnum.global_:
            ...


def load_context(mode: SearchModeEnum, text_embedder, token_encoder, **kwargs) -> ContextBuilder:
    match mode:
        case SearchModeEnum.local:
            return LocalSearchMixedContext(text_embedder=text_embedder, token_encoder=token_encoder, **kwargs)
        case SearchModeEnum.global_:
            ...
            # return await build_global_context_builder(text_embedder, token_encoder, **kwargs)


def load_search_engine_by_domain_dir(domain_dir) -> Dict[SearchModeEnum, BaseSearch]:
    domain_instance: Dict[SearchModeEnum, BaseSearch] = {}
    data_dir, config = load_domain_setting(domain_dir)
    # load universal object
    llm, text_embedder, token_encoder = load_universal_obj(config)
    # load data files
    datas = load_data_files(data_dir, config)
    # load tow mode of search_engine engine
    for mode in SearchModeEnum.__members__.values():
        context_builder: ContextBuilder = load_context(mode, text_embedder, token_encoder, **datas)
        search_engine: BaseSearch = build_search_engine(mode, llm, config, token_encoder, context_builder)
        domain_instance[SearchModeEnum(mode)] = search_engine
    return domain_instance


def load_domain_setting(domain_dir) -> Tuple[str, FinalConfig]:
    """
    load setting. The global setting will overwrite the domain setting

    Args:
        domain_dir: domain dir

    Returns:
        str: data dir
        Dict: config
    """
    # load setting from domain dir
    data_dir, _, config = _configure_paths_and_settings(None, domain_dir)

    # todo:load setting from global setting
    # get current file path
    plugin_path = Path(__file__).parent.parent.parent
    global_setting_yaml_path = plugin_path / 'settings.yaml'
    yaml_config = load_yaml_setting(global_setting_yaml_path)
    final_config = create_final_config(yaml_config, str(plugin_path), config)
    # merge config
    final_config = merge_config(domain_config=config, final_config=final_config)

    return data_dir, final_config


def load_yaml_setting(yaml_path: Path) -> Dict:
    if yaml_path.exists():
        with yaml_path.open("rb") as file:
            import yaml
            data = yaml.safe_load(file.read().decode(encoding="utf-8", errors="strict"))
            return data


def load_all_search_engine(all_index_dir: str) -> Dict[DomainEnum, Dict[SearchModeEnum, BaseSearch]]:
    all_search_engine: Dict[DomainEnum, Dict[SearchModeEnum, BaseSearch]] = {}
    all_index_dir = Path(all_index_dir)
    if all_index_dir.exists():
        for domain_dir in all_index_dir.iterdir():
            if domain_dir.name in DomainEnum.__members__:
                domain = domain_dir.name
                all_search_engine[DomainEnum(domain)] = load_search_engine_by_domain_dir(str(domain_dir))
    return all_search_engine


def init_env() -> Dict[DomainEnum, Dict[SearchModeEnum, BaseSearch]]:
    # get current file path
    plugin_path = Path(__file__).parent.parent.parent
    global_setting_yaml_path = plugin_path / 'settings.yaml'
    config = load_yaml_setting(global_setting_yaml_path)
    all_index_dir = config.get('all_index_dir', './context')
    return load_all_search_engine(all_index_dir)
