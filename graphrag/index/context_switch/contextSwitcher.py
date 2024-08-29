from graphrag.index.progress import ProgressReporter
from graphrag.config import GraphRagConfig
from azure.cosmos import CosmosClient, PartitionKey

class ContextSwitcher:
    """ContextSwitcher class definition."""

    def __init__(self):
        #initialize Gremline and Cosmos Db client here.
        pass
    def activate(self, config: GraphRagConfig | str, contextId: str | None, reporter: ProgressReporter):
        """Activate the context."""
        
        #1. read the context id to fileId mapping.
        #2. read the file from storage using common/blob_storage_client.py
        #3. GraphDB: use cosmos db client to load data into Cosmos DB.
        #4. KustoDB: use Kusto client to load embedding data into Kusto.
        if config.graphdb.enabled:
            cosmos_client = CosmosClient(
                f"https://{config.graphdb.account_name}.documents.azure.com:443/",
                f"{config.graphdb.account_key}",
            )
            database_name = config.graphdb.username.split("/")[2]
            database = cosmos_client.get_database_client(database_name)
            graph_name=config.graphdb.username.split("/")[-1]+"-contextid-"+contextId
            graph = database.create_container_if_not_exists(
                id=graph_name,
                partition_key=PartitionKey(path='/category'),
                offer_throughput=400
            )
        return 0

    def deactivate(self, config: GraphRagConfig | str, contextId: str | None, reporter: ProgressReporter):
        """DeActivate the context."""
        #1. Delete all the data for a given context id.
        return 0