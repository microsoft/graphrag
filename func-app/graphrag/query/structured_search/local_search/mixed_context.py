# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
"""Algorithms to build context data for local search prompt."""

import logging
from typing import Any
import ast
import json
import asyncio
import pandas as pd
from common.graph_db_client import GraphDBClient
from graphrag.config.models.graphdb_config import GraphDBConfig
from graphrag.config.models.graph_rag_config import GraphRagConfig
import tiktoken
from graphrag.index.verbs.entities.extraction.strategies.typing import Document
import hashlib
from graphrag.model import (
    CommunityReport,
    Covariate,
    Entity,
    Relationship,
    TextUnit,
)
from graphrag.query.context_builder.community_context import (
    build_community_context,
)
from graphrag.query.context_builder.conversation_history import (
    ConversationHistory,
)
from graphrag.query.context_builder.entity_extraction import (
    EntityVectorStoreKey,
    map_query_to_entities,
)
from graphrag.query.context_builder.local_context import (
    build_covariates_context,
    build_entity_context,
    build_relationship_context,
    get_candidate_context,
)
from graphrag.query.context_builder.source_context import (
    build_text_unit_context,
    count_relationships,
)
from graphrag.query.input.retrieval.community_reports import (
    get_candidate_communities,
)
from graphrag.query.input.retrieval.text_units import get_candidate_text_units
from graphrag.query.llm.base import BaseTextEmbedding
from graphrag.query.llm.text_utils import num_tokens
from graphrag.query.structured_search.base import LocalContextBuilder
from graphrag.vector_stores import BaseVectorStore
from graphrag.vector_stores.kusto import KustoVectorStore
from graphrag.index.verbs.entities.extraction.strategies.graph_intelligence.run_graph_intelligence import run_gi
from graphrag.index.verbs.graph.clustering.cluster_graph import generate_entity_id

log = logging.getLogger(__name__)


class LocalSearchMixedContext(LocalContextBuilder):
    """Build data context for local search prompt combining community reports and entity/relationship/covariate tables."""

    def __init__(
        self,
        entities: list[Entity],
        entity_text_embeddings: BaseVectorStore,
        text_embedder: BaseTextEmbedding,
        text_units: list[TextUnit] | None = None,
        community_reports: list[CommunityReport] | None = None,
        relationships: list[Relationship] | None = None,
        covariates: dict[str, list[Covariate]] | None = None,
        token_encoder: tiktoken.Encoding | None = None,
        embedding_vectorstore_key: str = EntityVectorStoreKey.ID,
        is_optimized_search: bool = False,
        use_kusto_community_reports: bool = False,
        config: GraphRagConfig | None = None,
        context_id:str = None,
    ):
        if community_reports is None:
            community_reports = []
        if relationships is None:
            relationships = []
        if covariates is None:
            covariates = {}
        if text_units is None:
            text_units = []
        self.entities = {entity.id: entity for entity in entities}
        self.community_reports = {
            community.id: community for community in community_reports
        }
        self.text_units = {unit.id: unit for unit in text_units}
        self.relationships = {
            relationship.id: relationship for relationship in relationships
        }
        self.covariates = covariates
        self.entity_text_embeddings = entity_text_embeddings
        self.text_embedder = text_embedder
        self.token_encoder = token_encoder
        self.embedding_vectorstore_key = embedding_vectorstore_key
        self.is_optimized_search = is_optimized_search
        self.use_kusto_community_reports = use_kusto_community_reports
        self.config = config
        self.context_id = context_id

    def filter_by_entity_keys(self, entity_keys: list[int] | list[str]):
        """Filter entity text embeddings by entity keys."""
        self.entity_text_embeddings.filter_by_id(entity_keys)

    def build_context(
        self,
        query: str,
        conversation_history: ConversationHistory | None = None,
        path=0,
        include_entity_names: list[str] | None = None,
        exclude_entity_names: list[str] | None = None,
        conversation_history_max_turns: int | None = 5,
        conversation_history_user_turns_only: bool = True,
        max_tokens: int = 8000,
        text_unit_prop: float = 0.5,
        community_prop: float = 0.25,
        top_k_mapped_entities: int = 10,
        top_k_relationships: int = 10,
        include_community_rank: bool = False,
        include_entity_rank: bool = False,
        rank_description: str = "number of relationships",
        include_relationship_weight: bool = False,
        relationship_ranking_attribute: str = "rank",
        return_candidate_context: bool = False,
        use_community_summary: bool = False,
        min_community_rank: int = 0,
        community_context_name: str = "Reports",
        column_delimiter: str = "|",
        is_optimized_search: bool = False,
        **kwargs: dict[str, Any],
    ) -> tuple[str | list[str], dict[str, pd.DataFrame]]:
        """
        Build data context for local search prompt.

        Build a context by combining community reports and entity/relationship/covariate tables, and text units using a predefined ratio set by summary_prop.
        """
        if include_entity_names is None:
            include_entity_names = []
        if exclude_entity_names is None:
            exclude_entity_names = []
        if community_prop + text_unit_prop > 1:
            value_error = (
                "The sum of community_prop and text_unit_prop should not exceed 1."
            )
            raise ValueError(value_error)

        # map user query to entities
        # if there is conversation history, attached the previous user questions to the current query
        if conversation_history:
            pre_user_questions = "\n".join(
                conversation_history.get_user_turns(conversation_history_max_turns)
            )
            query = f"{query}\n{pre_user_questions}"


        preselected_entities, selected_entities, entity_to_related_entities = [], [], []

        #path = 4 #1: base, 2,3: paths 4:graphdb simulation

        if path in (2,3):
            args = {}
            args['type'] = self.config.llm.type
            args['model'] = self.config.llm.model
            args['model_supports_json'] = self.config.llm.model_supports_json
            args['api_base'] = self.config.llm.api_base
            args['api_version'] = self.config.llm.api_version
            args['deployment_name'] = self.config.llm.deployment_name
            llm_conf = {}
            llm_conf['llm'] = args

            q_entities = asyncio.run(run_gi(
                docs=[Document(text=query, id='0')],
                entity_types=self.config.entity_extraction.entity_types,
                reporter = None,
                pipeline_cache=None,
                args=llm_conf,
            ))

            q_entities=q_entities.entities

            preselected_entities=[generate_entity_id(entity['name']) for entity in q_entities]

            names = [entity['name'] for entity in q_entities]

            print("Entities: ", names)

            if path == 3:
                #graph search: get relationships

                graphdb_client=GraphDBClient(self.config.graphdb,self.context_id)# if (self.config.graphdb and self.config.graphdb.enabled) else None
                if graphdb_client:
                    # Call graphdb making a list of dictionary of entity_id to related entities mapping
                    entity_to_related_entities = {preselected_entity: graphdb_client.get_top_related_unique_edges(preselected_entity, top_k_relationships) for preselected_entity in preselected_entities}
                    print("Related entities: ", entity_to_related_entities)
                else:
                    print("No graphdb, cannot add relationship context")


        selected_entities = map_query_to_entities(
            query=query,
            text_embedding_vectorstore=self.entity_text_embeddings,
            text_embedder=self.text_embedder,
            all_entities=list(self.entities.values()),
            embedding_vectorstore_key=self.embedding_vectorstore_key,
            include_entity_names=include_entity_names,
            exclude_entity_names=exclude_entity_names,
            k=top_k_mapped_entities,
            oversample_scaler=2,
            preselected_entities=preselected_entities
        )

        print("Selected entities titles: ", [entity.title for entity in selected_entities])


        # build context
        final_context = list[str]()
        final_context_data = dict[str, pd.DataFrame]()

        if conversation_history:
            # build conversation history context
            (
                conversation_history_context,
                conversation_history_context_data,
            ) = conversation_history.build_context(
                include_user_turns_only=conversation_history_user_turns_only,
                max_qa_turns=conversation_history_max_turns,
                column_delimiter=column_delimiter,
                max_tokens=max_tokens,
                recency_bias=False,
            )
            if conversation_history_context.strip() != "":
                final_context.append(conversation_history_context)
                final_context_data = conversation_history_context_data
                max_tokens = max_tokens - num_tokens(
                    conversation_history_context, self.token_encoder
                )

        if not is_optimized_search:
            community_tokens = max(int(max_tokens * community_prop), 0)
            community_context, community_context_data = self._build_community_context(
                selected_entities=selected_entities,
                max_tokens=community_tokens,
                use_community_summary=use_community_summary,
                column_delimiter=column_delimiter,
                include_community_rank=include_community_rank,
                min_community_rank=min_community_rank,
                return_candidate_context=return_candidate_context,
                context_name=community_context_name,
                is_optimized_search=is_optimized_search
            )
            if community_context.strip() != "":
                final_context.append(community_context)
                final_context_data = {**final_context_data, **community_context_data}

        # build local (i.e. entity-relationship-covariate) context
        local_prop = 1 - community_prop - text_unit_prop
        local_tokens = max(int(max_tokens * local_prop), 0)
        local_context, local_context_data = self._build_local_context( #RELATIONSHIPS HERE
            selected_entities=selected_entities,
            max_tokens=local_tokens,
            include_entity_rank=include_entity_rank,
            rank_description=rank_description,
            include_relationship_weight=include_relationship_weight,
            top_k_relationships=top_k_relationships,
            relationship_ranking_attribute=relationship_ranking_attribute,
            return_candidate_context=return_candidate_context,
            column_delimiter=column_delimiter,
            is_optimized_search=is_optimized_search
        )
        if local_context.strip() != "":
            final_context.append(str(local_context))
            final_context_data = {**final_context_data, **local_context_data}
        if not self.is_optimized_search:
            # build text unit context
            text_unit_tokens = max(int(max_tokens * text_unit_prop), 0)


            if isinstance(self.entity_text_embeddings,KustoVectorStore):
                text_unit_context, text_unit_context_data = self._build_text_unit_context_kusto(
                    selected_entities=selected_entities,
                    max_tokens=text_unit_tokens,
                    return_candidate_context=return_candidate_context,
                    vector_store=self.entity_text_embeddings,
                    entity_to_related_entities=entity_to_related_entities
                )
            else: #legacy
                text_unit_context, text_unit_context_data = self._build_text_unit_context(
                    selected_entities=selected_entities,
                    max_tokens=text_unit_tokens,
                    return_candidate_context=return_candidate_context,
                )

            if text_unit_context.strip() != "":
                final_context.append(text_unit_context)
                final_context_data = {**final_context_data, **text_unit_context_data}

        ############### get doc ids
        entity_to_units={}
        for e in selected_entities:
            text_units=[]
            if e.text_unit_ids!='' and e.text_unit_ids!=None:
                text_units.extend(ast.literal_eval(e.text_unit_ids))
            if e.title not in entity_to_units:
                #TODO: change title to id later
                entity_to_units[e.title]=[]
            entity_to_units[e.title].extend(text_units)


        for title in entity_to_units:
            for unit in entity_to_units[title]:
                docs=self.text_units_kusto[unit]
                ## Documents IDs per TextUnit per Entity:
                print(f"> {title}: {unit}: {docs}")

        return ("\n\n".join(final_context), final_context_data)

    def _build_community_context(
        self,
        selected_entities: list[Entity],
        max_tokens: int = 4000,
        use_community_summary: bool = False,
        column_delimiter: str = "|",
        include_community_rank: bool = False,
        min_community_rank: int = 0,
        return_candidate_context: bool = False,
        context_name: str = "Reports",
        is_optimized_search: bool = False,
    ) -> tuple[str, dict[str, pd.DataFrame]]:
        """Add community data to the context window until it hits the max_tokens limit."""
        if len(selected_entities) == 0 or (len(self.community_reports) == 0 and not self.use_kusto_community_reports):
            return ("", {context_name.lower(): pd.DataFrame()})

        community_matches = {}
        for entity in selected_entities:
            # increase count of the community that this entity belongs to
            if entity.community_ids:
                for community_id in entity.community_ids:
                    community_matches[community_id] = (
                        community_matches.get(community_id, 0) + 1
                    )

        selected_communities = []
        if self.use_kusto_community_reports:
            selected_communities = self.entity_text_embeddings.get_extracted_reports(
                community_ids=list(community_matches.keys())
            )
        else:
            selected_communities = [
                self.community_reports[community_id]
                for community_id in community_matches
                if community_id in self.community_reports
            ]

        # sort communities by number of matched entities and rank
        for community in selected_communities:
            if community.attributes is None:
                community.attributes = {}
            community.attributes["matches"] = community_matches[community.id]
        selected_communities.sort(
            key=lambda x: (x.attributes["matches"], x.rank),  # type: ignore
            reverse=True,  # type: ignore
        )
        for community in selected_communities:
            del community.attributes["matches"]  # type: ignore
        context_data = {}
        context_data["reports"] =  selected_communities
        context_text = ""
        if not is_optimized_search:
            context_text, context_data = build_community_context(
                community_reports=selected_communities,
                token_encoder=self.token_encoder,
                use_community_summary=use_community_summary,
                column_delimiter=column_delimiter,
                shuffle_data=False,
                include_community_rank=include_community_rank,
                min_community_rank=min_community_rank,
                max_tokens=max_tokens,
                single_batch=True,
                context_name=context_name,
            )
            if isinstance(context_text, list) and len(context_text) > 0:
                context_text = "\n\n".join(context_text)

            if return_candidate_context:
                candidate_context_data = get_candidate_communities(
                    selected_entities=selected_entities,
                    community_reports=list(self.community_reports.values()),
                    use_community_summary=use_community_summary,
                    include_community_rank=include_community_rank,
                )
                context_key = context_name.lower()
                if context_key not in context_data:
                    context_data[context_key] = candidate_context_data
                    context_data[context_key]["in_context"] = False
                else:
                    if (
                        "id" in candidate_context_data.columns
                        and "id" in context_data[context_key].columns
                    ):
                        candidate_context_data["in_context"] = candidate_context_data[
                            "id"
                        ].isin(  # cspell:disable-line
                            context_data[context_key]["id"]
                        )
                        context_data[context_key] = candidate_context_data
                    else:
                        context_data[context_key]["in_context"] = True
        return (str(context_text), context_data)

    def _build_text_unit_context_kusto(
        self,
        selected_entities: list[Entity],
        max_tokens: int = 8000,
        return_candidate_context: bool = False,
        column_delimiter: str = "|",
        context_name: str = "Sources",
        vector_store: BaseVectorStore = None,
        entity_to_related_entities: [dict[str, str]] = [],
    ) -> tuple[str, dict[str, pd.DataFrame]]:

        selected_text_units=vector_store.retrieve_text_units(selected_entities)

        # if path 3, we have related text units to add to the context
        for related_groups in entity_to_related_entities.values() if entity_to_related_entities else []:
            for related in related_groups:
                selected_text_units += vector_store.retrieve_text_units_by_id(ast.literal_eval(related['text_unit_ids']))

        hmap={}
        text_units_kusto={}
        for unit in selected_text_units:
            if unit.id not in hmap:
                hmap[unit.id]=unit
                text_units_kusto[unit.id]=unit.document_ids

        selected_text_units=[]
        for id in hmap:
            selected_text_units.append(hmap[id])


        self.text_units_kusto=text_units_kusto

        #ignore sorting selected_text_usnits based on relationship count

        def str_to_list(unit,column):
            cvar = getattr(unit,column)
            if cvar == '' or cvar==None:
                setattr(unit,column,[])
                return
            setattr(unit,column,ast.literal_eval(cvar))

        for unit in selected_text_units:
            str_to_list(unit,'entity_ids')
            str_to_list(unit,'relationship_ids')
            str_to_list(unit,'document_ids')

            ### EMAIL DATASET
            txt=unit.text
            loc = txt.find("\"body\"")
            if loc > -1:
                unit.text = txt[loc+9:]

            logging.info("Adding source: "+unit.text)


        context_text, context_data = build_text_unit_context(
            text_units=selected_text_units,
            token_encoder=self.token_encoder,
            max_tokens=max_tokens,
            shuffle_data=False,
            context_name=context_name,
            column_delimiter=column_delimiter,
        )

        if return_candidate_context:
            candidate_context_data = get_candidate_text_units(
                selected_entities=selected_entities,
                text_units=list(self.text_units.values()),
            )
            context_key = context_name.lower()
            if context_key not in context_data:
                context_data[context_key] = candidate_context_data
                context_data[context_key]["in_context"] = False
            else:
                if (
                    "id" in candidate_context_data.columns
                    and "id" in context_data[context_key].columns
                ):
                    candidate_context_data["in_context"] = candidate_context_data[
                        "id"
                    ].isin(  # cspell:disable-line
                        context_data[context_key]["id"]
                    )
                    context_data[context_key] = candidate_context_data
                else:
                    context_data[context_key]["in_context"] = True
        return (str(context_text), context_data)


    def _build_text_unit_context(
        self,
        selected_entities: list[Entity],
        max_tokens: int = 8000,
        return_candidate_context: bool = False,
        column_delimiter: str = "|",
        context_name: str = "Sources",
    ) -> tuple[str, dict[str, pd.DataFrame]]:
        """Rank matching text units and add them to the context window until it hits the max_tokens limit."""
        if len(selected_entities) == 0 or len(self.text_units) == 0:
            return ("", {context_name.lower(): pd.DataFrame()})

        selected_text_units = list[TextUnit]()
        # for each matching text unit, rank first by the order of the entities that match it, then by the number of matching relationships
        # that the text unit has with the matching entities
        for index, entity in enumerate(selected_entities):
            if entity.text_unit_ids:
                for text_id in entity.text_unit_ids:
                    if (
                        text_id not in [unit.id for unit in selected_text_units]
                        and text_id in self.text_units
                    ):
                        selected_unit = self.text_units[text_id]
                        num_relationships = count_relationships(
                            selected_unit, entity, self.relationships
                        )
                        if selected_unit.attributes is None:
                            selected_unit.attributes = {}
                        selected_unit.attributes["entity_order"] = index
                        selected_unit.attributes["num_relationships"] = (
                            num_relationships
                        )
                        selected_text_units.append(selected_unit)

        # sort selected text units by ascending order of entity order and descending order of number of relationships
        selected_text_units.sort(
            key=lambda x: (
                x.attributes["entity_order"],  # type: ignore
                -x.attributes["num_relationships"],  # type: ignore
            )
        )

        for unit in selected_text_units:
            del unit.attributes["entity_order"]  # type: ignore
            del unit.attributes["num_relationships"]  # type: ignore

        context_text, context_data = build_text_unit_context(
            text_units=selected_text_units,
            token_encoder=self.token_encoder,
            max_tokens=max_tokens,
            shuffle_data=False,
            context_name=context_name,
            column_delimiter=column_delimiter,
        )

        if return_candidate_context:
            candidate_context_data = get_candidate_text_units(
                selected_entities=selected_entities,
                text_units=list(self.text_units.values()),
            )
            context_key = context_name.lower()
            if context_key not in context_data:
                context_data[context_key] = candidate_context_data
                context_data[context_key]["in_context"] = False
            else:
                if (
                    "id" in candidate_context_data.columns
                    and "id" in context_data[context_key].columns
                ):
                    candidate_context_data["in_context"] = candidate_context_data[
                        "id"
                    ].isin(  # cspell:disable-line
                        context_data[context_key]["id"]
                    )
                    context_data[context_key] = candidate_context_data
                else:
                    context_data[context_key]["in_context"] = True
        return (str(context_text), context_data)

    def _build_local_context(
        self,
        selected_entities: list[Entity],
        max_tokens: int = 8000,
        include_entity_rank: bool = False,
        rank_description: str = "relationship count",
        include_relationship_weight: bool = False,
        top_k_relationships: int = 10,
        relationship_ranking_attribute: str = "rank",
        return_candidate_context: bool = False,
        column_delimiter: str = "|",
        is_optimized_search: bool = False
    ) -> tuple[str, dict[str, pd.DataFrame]]:
        """Build data context for local search prompt combining entity/relationship/covariate tables."""
        # build entity context
        entity_context, entity_context_data = build_entity_context(
            selected_entities=selected_entities,
            token_encoder=self.token_encoder,
            max_tokens=max_tokens,
            column_delimiter=column_delimiter,
            include_entity_rank=include_entity_rank,
            rank_description=rank_description,
            context_name="Entities",
            is_optimized_search=is_optimized_search,
        )
        entity_tokens = num_tokens(entity_context, self.token_encoder)

        # build relationship-covariate context
        added_entities = []
        final_context = []
        final_context_data = {}

        # gradually add entities and associated metadata to the context until we reach limit
        graphdb_client=GraphDBClient(self.config.graphdb,self.context_id) if (self.config.graphdb and self.config.graphdb.enabled) else None
        for entity in selected_entities:
            current_context = []
            current_context_data = {}
            added_entities.append(entity)

            # build relationship context
            (
                relationship_context,
                relationship_context_data,
            ) = build_relationship_context(
                selected_entities=added_entities,
                relationships=list(self.relationships.values()),
                token_encoder=self.token_encoder,
                max_tokens=max_tokens,
                column_delimiter=column_delimiter,
                top_k_relationships=top_k_relationships,
                include_relationship_weight=include_relationship_weight,
                relationship_ranking_attribute=relationship_ranking_attribute,
                context_name="Relationships",
                is_optimized_search=is_optimized_search,
                graphdb_client=graphdb_client,
            )
            current_context.append(relationship_context)
            current_context_data["relationships"] = relationship_context_data
            total_tokens = entity_tokens + num_tokens(
                relationship_context, self.token_encoder
            )


            # build covariate context
            for covariate in self.covariates:
                covariate_context, covariate_context_data = build_covariates_context(
                    selected_entities=added_entities,
                    covariates=self.covariates[covariate],
                    token_encoder=self.token_encoder,
                    max_tokens=max_tokens,
                    column_delimiter=column_delimiter,
                    context_name=covariate,
                    is_optimized_search=is_optimized_search
                )
                total_tokens += num_tokens(covariate_context, self.token_encoder)
                current_context.append(covariate_context)
                current_context_data[covariate.lower()] = covariate_context_data

            if total_tokens > max_tokens:
                log.info("Reached token limit - reverting to previous context state")
                break

            final_context = current_context
            final_context_data = current_context_data

        # attach entity context to final context
        if graphdb_client:
            graphdb_client._client.close()
        final_context_text = entity_context + "\n\n" + "\n\n".join(final_context)
        final_context_data["entities"] = entity_context_data

        if return_candidate_context:
            # we return all the candidate entities/relationships/covariates (not only those that were fitted into the context window)
            # and add a tag to indicate which records were included in the context window
            candidate_context_data = get_candidate_context(
                selected_entities=selected_entities,
                entities=list(self.entities.values()),
                relationships=list(self.relationships.values()),
                covariates=self.covariates,
                include_entity_rank=include_entity_rank,
                entity_rank_description=rank_description,
                include_relationship_weight=include_relationship_weight,
            )
            for key in candidate_context_data:
                candidate_df = candidate_context_data[key]
                if key not in final_context_data:
                    final_context_data[key] = candidate_df
                    final_context_data[key]["in_context"] = False
                else:
                    in_context_df = final_context_data[key]

                    if "id" in in_context_df.columns and "id" in candidate_df.columns:
                        candidate_df["in_context"] = candidate_df[
                            "id"
                        ].isin(  # cspell:disable-line
                            in_context_df["id"]
                        )
                        final_context_data[key] = candidate_df
                    else:
                        final_context_data[key]["in_context"] = True

        else:
            for key in final_context_data:
                final_context_data[key]["in_context"] = True
        return (final_context_text, final_context_data)
