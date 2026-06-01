
import pandas as pd
import tiktoken
from json_repair import loads
from comparison_prompt import eval_system_prompt,eval_user_prompt, RAG_SYSTEM_PROMPT, RESPONSE_TYPE
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from graphrag.query.context_builder.entity_extraction import EntityVectorStoreKey
from graphrag.query.indexer_adapters import (
    read_indexer_covariates,
    read_indexer_entities,
    read_indexer_relationships,
    read_indexer_reports,
    read_indexer_text_units,
)
from graphrag.query.question_gen.local_gen import LocalQuestionGen
from graphrag.query.structured_search.local_search.mixed_context import (
    LocalSearchMixedContext,build_text_unit_context,LocalContextBuilder
)
from graphrag.query.structured_search.local_search.search import LocalSearch
from graphrag.vector_stores.lancedb import LanceDBVectorStore
from graphrag.query.indexer_adapters import (
    read_indexer_communities,
    read_indexer_entities,
    read_indexer_reports,
)
import tiktoken
from graphrag.query.indexer_adapters import read_indexer_entities, read_indexer_reports
#from graphrag.query.llm.oai.chat_openai import ChatOpenAI
#from graphrag.query.llm.oai.typing import OpenaiApiType
from graphrag.query.structured_search.global_search.community_context import (
    GlobalCommunityContext,
)
from graphrag.query.structured_search.global_search.search import GlobalSearch

from graphrag.config.enums import ModelType
from graphrag.config.models.language_model_config import LanguageModelConfig
from graphrag.language_model.manager import ModelManager
from graphrag.config.load_config import load_config
from pathlib import Path


from dataclasses import dataclass,replace

@dataclass
class Answer:
    answer_number: int = 0
    question: str = ""
    answer: str = ""
    comprehensiveness_reason: str = ""
    comprehensiveness_rating: int = 0
    diversity_reason: str = ""
    diversity_rating: int = 0
    empowerment_reason: str = ""
    empowerment_rating: int = 0
    directness_reason: str = ""
    directness_rating: int = 0


@dataclass
class Method:
    rag_search:Answer=None
    local_search:Answer=None
    global_search:Answer=None
    error:str=""
    


class GraphRagcomparison:

    # Constants defined at class level
    COMMUNITY_REPORT_TABLE = "community_reports"
    ENTITY_TABLE = "entities"
    COMMUNITY_TABLE = "communities"
    RELATIONSHIP_TABLE = "relationships"
    COVARIATE_TABLE = "covariates" 
    TEXT_UNIT_TABLE = "text_units"
    COMMUNITY_LEVEL = 2
    default_entity_description = "default-entity-description"
    default_text_unit_text = "default-text_unit-text"

    def __init__(self, root_dir: str, temperature: float = 0.0):

        print("Initializing GraphRAGSearch...")
        self.root_dir = Path(root_dir)
        self.compare_dir = self.root_dir.joinpath("comparison_results")
        self.compare_dir.mkdir(parents=True, exist_ok=True) 
        self.temperature = temperature
        self.config = None
        self.output_dir = None
        self.lancedb_uri = None

        # Models & Encoder
        self.rag_model = None
        self.local_model = None
        self.global_model = None
        self.compare_model = None
        self.text_embedder = None
        self.token_encoder = None
        

        # Data
        self.entities = None
        self.communities = None
        self.relationships = None
        self.reports = None
        self.text_units = None

        # Vector Store
        self.description_embedding_store = None
        self.text_unit_embedding_store = None

        # Context Builders
        self.local_context_builder = None
        self.global_context_builder = None

        # Search Objects
        self.localsearch = None
        self.globalsearch = None

        # Run setup methods
        self._load_config()
        self._setup_paths()
        self._setup_models_and_encoder()
        self._load_data()
        self.description_embedding_store=self._setup_vector_store(vector_store_collection_name=self.default_entity_description)
        self.text_unit_embedding_store=self._setup_vector_store(vector_store_collection_name=self.default_text_unit_text)
        self._setup_context_builders()
        self._setup_search_engines()
        print("Initialization complete.")


    def run_rag_search(self,question):
        
        rag_results = self.text_unit_embedding_store.similarity_search_by_text(question,k=5,text_embedder=self.text_embedder.embed,)
        context_text=""
            
        for r in rag_results:
            text = r.document.text
            id = r.document.id
            context_text += f"[Data: Source unit_text {id}]\n{text}\n"
            
        
        system_prompt = RAG_SYSTEM_PROMPT.format(
    
            context_data=context_text, response_type=RESPONSE_TYPE
        )
        prompt = system_prompt.strip() + "\nQuestion: " + question.strip()    

        llm_result = self.rag_model.chat(prompt).output.content
        print(f"--- Running Normal RAG: {llm_result[:50]} ---")
        
        return llm_result

    def _load_config(self):
        """Loads configuration from the root directory."""
        print("Loading configuration...")
        self.config = load_config(self.root_dir)
        if not self.config:
            raise ValueError(f"Could not load configuration from {self.root_dir}")
        print("Configuration loaded.")

    def _setup_paths(self):
        """Sets up output directory and LanceDB URI paths."""
        self.output_dir = self.config.output.base_dir
        self.lancedb_uri = f"{self.output_dir}/lancedb"
        print(f"Output directory set to: {self.output_dir}")
        print(f"LanceDB URI set to: {self.lancedb_uri}")

    def _setup_models_and_encoder(self):
        """Initializes LLM chat models, embedding model, and token encoder."""
        print("Setting up models and token encoder...")
        model_manager = ModelManager()

        chat_config = self.config.models['default_chat_model']
        print(f"Using chat model config: {chat_config}")
        self.rag_model = model_manager.get_or_create_chat_model(
            name = "rag_search", 
            model_type=ModelType.OpenAIChat,
            config=chat_config,
        )
        self.local_model = model_manager.get_or_create_chat_model(
            name = "local_search",
            model_type=ModelType.OpenAIChat,
            config=chat_config,
        )

        self.global_model = model_manager.get_or_create_chat_model(
            name="global_search_chat",
            model_type=ModelType.OpenAIChat,
            config=chat_config, # Using the same config
        )

        self.compare_model = model_manager.get_or_create_chat_model(
            name="compare",
            model_type=ModelType.OpenAIChat,
            config=chat_config, # Using the same config
        )

        # Token Encoder
        try:
            self.token_encoder = tiktoken.get_encoding("cl100k_base")
        except Exception:
            print("cl100k_base encoding not found, trying model name...")
            self.token_encoder = tiktoken.encoding_for_model("gpt-4-turbo-preview")
        print(f"Token Encoder created based on: {'cl100k_base' if 'cl100k_base' in str(self.token_encoder) else llm_model_name}")

        # Embedding Model
        embedding_config = self.config.models['default_embedding_model']
        self.text_embedder = model_manager.get_or_create_embedding_model(
            name="local_search_embedding",
            model_type=ModelType.OpenAIEmbedding,
            config=embedding_config,
        )
        print("Models and encoder setup complete.")

    def _load_data(self):
        """Loads data from parquet files."""
        print("Loading data from parquet files...")
        try:
            entity_df = pd.read_parquet(f"{self.output_dir}/{self.ENTITY_TABLE}.parquet")
            community_df = pd.read_parquet(f"{self.output_dir}/{self.COMMUNITY_TABLE}.parquet")
            report_df = pd.read_parquet(f"{self.output_dir}/{self.COMMUNITY_REPORT_TABLE}.parquet")
            relationship_df = pd.read_parquet(f"{self.output_dir}/{self.RELATIONSHIP_TABLE}.parquet")
            text_unit_df = pd.read_parquet(f"{self.output_dir}/{self.TEXT_UNIT_TABLE}.parquet")

            # Process data using indexer readers
            self.entities = read_indexer_entities(entity_df, community_df, self.COMMUNITY_LEVEL)
            self.communities = read_indexer_communities(community_df, report_df) # Assuming this signature is correct

            # Handle potential NaNs in relationship degrees
            relationship_df.fillna({'combined_degree': 0.0}, inplace=True) # More specific fillna
            self.relationships = read_indexer_relationships(relationship_df)

            self.reports = read_indexer_reports(report_df, community_df, self.COMMUNITY_LEVEL)
            self.text_units = read_indexer_text_units(text_unit_df)

            print(f"Loaded {len(self.entities)} entities, {len(self.communities)} communities, "
                  f"{len(self.relationships)} relationships, {len(self.reports)} reports, "
                  f"{len(self.text_units)} text units.")
        except FileNotFoundError as e:
            print(f"ERROR: Parquet file not found: {e}. Ensure indexing pipeline has run successfully.")
            raise
        except Exception as e:
            print(f"ERROR loading or processing data: {e}")
            raise
        print("Data loading complete.")


    def _setup_vector_store(self,vector_store_collection_name):
        """Sets up the LanceDB vector store for entity descriptions."""
        print("Setting up vector store...")
        vector_store = LanceDBVectorStore(
            collection_name=vector_store_collection_name,
        )
        try:
            vector_store.connect(db_uri=self.lancedb_uri)
            # Test connection (optional but good practice)
            test_search = vector_store.similarity_search_by_text(
                "test query", k=1, text_embedder=self.text_embedder.embed
                )
            print(f"Vector store connected successfully to {self.lancedb_uri} "
                  f"(collection: {self.default_entity_description}). Test search returned {len(test_search)} result(s).")
            return vector_store
        except Exception as e:
            print(f"ERROR connecting to or querying vector store at {self.lancedb_uri}: {e}")
            print("Please ensure LanceDB is running and the collection exists.")
        
        
        
    
    def _setup_context_builders(self):
        """Creates the context builders for local and global search."""
        print("Setting up context builders...")
        # Local Context Builder
        self.local_context_builder = LocalSearchMixedContext(
            community_reports=self.reports,
            text_units=self.text_units,
            entities=self.entities,
            relationships=self.relationships,
            covariates=None, # Explicitly None as per original code comment
            entity_text_embeddings=self.description_embedding_store,
            embedding_vectorstore_key=EntityVectorStoreKey.ID, # Defaulting to ID
            text_embedder=self.text_embedder,
            token_encoder=self.token_encoder,
        )
        print("LocalSearchMixedContext created.")

        # Global Context Builder
        self.global_context_builder = GlobalCommunityContext(
            community_reports=self.reports,
            communities=self.communities,
            entities=self.entities, 
            token_encoder=self.token_encoder,
        )
        print("GlobalCommunityContext created.")
        print("Context builders setup complete.")

    def _setup_search_engines(self):
        """Configures and initializes the LocalSearch and GlobalSearch objects."""
        print("Setting up search engines...")

        # Local Search Configuration
        local_context_params = {
            "text_unit_prop": 0.5,
            "community_prop": 0.1,
            "conversation_history_max_turns": 5,
            "conversation_history_user_turns_only": True,
            "top_k_mapped_entities": 10,
            "top_k_relationships": 10,
            "include_entity_rank": True,
            "include_relationship_weight": True,
            "include_community_rank": False,
            "return_candidate_context": False,
            "embedding_vectorstore_key": EntityVectorStoreKey.ID,
            "max_tokens": 12_000,
        }
        local_llm_params = {
            "max_tokens": 2_000,
            "temperature": self.temperature,
        }
        self.localsearch = LocalSearch(
            model=self.local_model, # Use the primary chat model
            context_builder=self.local_context_builder,
            token_encoder=self.token_encoder,
            model_params=local_llm_params,
            context_builder_params=local_context_params,
            response_type="multiple paragraphs",
        )
        print("LocalSearch engine configured.")

        # Global Search Configuration
        global_context_builder_params = {
            "use_community_summary": False,
            "shuffle_data": True,
            "include_community_rank": True,
            "min_community_rank": 0,
            "community_rank_name": "rank",
            "include_community_weight": True,
            "community_weight_name": "occurrence weight",
            "normalize_community_weight": True,
            "max_tokens": 12_000,
            "context_name": "Reports",
        }
        map_llm_params = {
            "max_tokens": 1000,
            "temperature": self.temperature,
            "response_format": {"type": "json_object"},
        }
        reduce_llm_params = {
            "max_tokens": 2000,
            "temperature": self.temperature,
        }
        self.globalsearch = GlobalSearch(
            model=self.global_model,
            context_builder=self.global_context_builder,
            token_encoder=self.token_encoder,
            max_data_tokens=12_000,
            map_llm_params=map_llm_params,
            reduce_llm_params=reduce_llm_params,
            allow_general_knowledge=False,
            json_mode=True,
            context_builder_params=global_context_builder_params,
            concurrent_coroutines=1,
            response_type="multiple paragraphs",
        )
        print("GlobalSearch engine configured.")
        print("Search engines setup complete.")

    async def run_local_search(self, question: str) -> str:
        """Runs a local search query."""
        if not self.localsearch:
            raise RuntimeError("LocalSearch engine not initialized.")
        
        result = await self.localsearch.search(question)
        print(f"--- Running GraphRAG Local Search: {result.response[:50]} ---")
        return result.response

    async def run_global_search(self, question: str) -> str:
        """Runs a global search query."""
        if not self.globalsearch:
            raise RuntimeError("GlobalSearch engine not initialized.")
        result = await self.globalsearch.search(question)
        print(f"--- Running GraphRAG Global Search: {result.response[:50]} ---")
        
        return result.response

    async def answer_questions(self, questions: list[str], sleep_interval: int = 5):
        
        results = []
        print(f"\n--- Starting Evaluation of {len(questions)} Questions ---")
        for i, question in enumerate(questions):
            print(f"\nProcessing Question {i+1}/{len(questions)}: '{question}'")
            method = Method()
            
            try:
                # Standard RAG
                method.rag_search = Answer(question=question, answer = self.run_rag_search(question))

                # GraphRAG Local Search
                method.local_search= Answer(question=question, answer = await self.run_local_search(question))

                # GraphRAG Global Search
                method.global_search = Answer(question=question, answer = await self.run_global_search(question))

            except Exception as e:
                print(f"ERROR processing question '{question}': {e}")
                method.error = str(e)

            results.append(method)

        
        return results
    
    
    def compare_answers(self,
        methods: list[Method],
        
    ) -> dict[str, pd.DataFrame]:
     
        for i, method in enumerate(methods):
            method : Method
            #print(method)
            question = method.rag_search.question
            answers = {
                'answer_1': method.rag_search.answer,
                'answer_2': method.local_search.answer,
                'answer_3': method.global_search.answer
            }
            print(f"\nEvaluating Row {i}: {question[:80]}...")

            #try:
            user_prompt = eval_user_prompt.format(question=question, **answers)
            prompt = eval_system_prompt + user_prompt
            prompt = prompt.lower()
            print("length of prompt: ", len(prompt))
            llm_outputs = self.compare_model.chat(prompt)
            llm_outputs = loads(llm_outputs.output.content)
            print(f"LLM Output Snippet: {str(llm_outputs)[:100]}...") 

            for idx, output_rating in enumerate(llm_outputs):
                match output_rating["answer_number"]:
                    case '1':
                        method.rag_search = replace( method.rag_search, **output_rating)
                    case '2':
                        method.local_search = replace( method.local_search, **output_rating)
                    case '3':
                        method.global_search = replace( method.global_search, **output_rating)
                

        rag_answers = [method.rag_search for method in methods]
        local_answers = [method.local_search for method in methods]
        global_answers = [method.global_search for method in methods]

        # Create a DataFrame for each rating list
        df_rag = pd.DataFrame(rag_answers)
        df_local = pd.DataFrame(local_answers)
        df_global = pd.DataFrame(global_answers)

        df_rag.to_parquet(self.compare_dir.joinpath(f"rag_ratings.parquet")) 
        df_local.to_parquet(self.compare_dir.joinpath(f"local_ratings.parquet")) 
        df_global.to_parquet(self.compare_dir.joinpath(f"global_ratings.parquet")) 
        
        df_compare = pd.DataFrame({
            'Question': df_rag["question"],
            'RAG': df_rag["answer"],
            'Graph RAG (Local)': df_local["answer"],
            'Graph RAG (Global)': df_global["answer"]
        })
        df_compare.to_parquet(self.compare_dir.joinpath(f"compare_result.parquet"))
        
        print("--- Evaluation Complete ---")
        return methods # Return the dataframes
    
    def plot_comparison_results(self,):


        filenames = [
            'rag_ratings',
            'local_ratings',
            'global_ratings'
        ]

        ratings_columns = ['comprehensiveness_rating', 'diversity_rating', 'empowerment_rating', 'directness_rating']

        bar_width = 0.25

        n_categories = len(ratings_columns)

        x = np.arange(n_categories)

        plt.figure(figsize=(10, 6))

        sum_per_questions = []
        for i, fn in enumerate(filenames):
            # Load the data
            rag_ratings = pd.read_parquet(self.compare_dir.joinpath( fn + '.parquet'))
            data = rag_ratings[ratings_columns].astype(int)
            
            bars = data.sum() / data.count()
            sum_per_questions.append( data.sum(1) )
            
            plt.bar(x + i * bar_width, bars.values, width=bar_width, label=fn)

        sum_per_questions = pd.DataFrame(sum_per_questions)
        winners = sum_per_questions.idxmax(0)
        w = winners.value_counts()
        
        # Set x-tick positions and labels
        plt.xticks(x + bar_width * (len(filenames) - 1) / 2, ratings_columns, rotation=45)
        plt.xlabel('Rating Categories', fontsize=12)
        plt.ylabel('Average Ratings', fontsize=12)
        plt.title('Average Ratings by Category', fontsize=16)
        plt.legend(title='Keys')

        #plt.show()
        plt.gcf().savefig(self.compare_dir.joinpath('comparison_plot.png'), bbox_inches='tight')
        
        
    def print_comparison_results(self,):
        from IPython.display import display
        for fn in ['compare_result','rag_ratings', 'local_ratings', 'global_ratings']:
            print(f"\n--- {fn} ---")
            display(pd.read_parquet(self.compare_dir.joinpath(fn + '.parquet')))
 
        img = plt.imread(self.compare_dir.joinpath('comparison_plot.png'))
        plt.imshow(img)
        plt.axis('off') 
        plt.show()
        
        


if __name__ == "__main__":
    import asyncio


    ROOT_DIR = "/home/cip/ce/ix05ogym/Majid/LLM/GraphRag/v2/" # UPDATE THIS PATH
    TEMPERATURE_SETTING = 0.2 # Example temperature

    questions_to_evaluate = [
        "What are letter codes in the context of BS 4584?",
        "How does soldering potentially contribute to peaceful pursuits?",
        "How does soldering contribute to the development of intelligent machines?",
        "How does LEAD contribute to the depletion of the ozone layer?",
        "What is the main advantage of using automatic insertion for component placement?",
        'What are some of the key areas where Cookson Electronics is involved?',
        'What are the primary functions of actions like bonding and flow in relation to the SI-GC-CU-13 laminate?',
        'What is the significance of the conductivity property of the SI-GC-CU-13 laminate?',
        'Explain the impact of LEAD on the environment, specifically its relationship with the ozone layer?',
        'What specific requirements are defined by standards in soldering?',
        'What is the significance of the "degree of 6" mentioned in relation to printed wiring boards?',
        'Is there any information about the specific types of components that are typically joined using soldering processes?',
        "What concepts are connected to wave soldering?",
        'What are the potential dangers associated with wavesoldering systems?',
        'What is the purpose of TABLE 1.2 in relation to letter codes?',
        'How does the time allowed for cooling after soldering impact the joint?',
        "what are top 5 important topics in soldering? write it with a number from 1 to 5",
        "what are 5 least important topics in soldering? write it with a number from 1 to 5",
        "what cause soldification quality decrease?",
        "if I have a poor solder can I still reach a high quality soldering? How?",
        "give me a comperhensive summary of solidification",
        "what is relationship between address and alloy?"
    ][:10]

    async def main():
            graph_rag_comparison = GraphRagcomparison(root_dir=ROOT_DIR, temperature=TEMPERATURE_SETTING)

            evaluation_results = await graph_rag_comparison.answer_questions(
                questions=questions_to_evaluate,
                sleep_interval=5 
            )
            print(evaluation_results)
            graph_rag_comparison.compare_answers(evaluation_results,
                                                         )
            print(f"Evaluation results saved to {graph_rag_comparison.compare_dir}.")
            
            graph_rag_comparison.plot_comparison_results()
            
            print("\n--- Final Evaluation Results ---")
           
            
    asyncio.run(main())