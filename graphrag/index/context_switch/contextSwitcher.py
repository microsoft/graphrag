from graphrag.index.progress import ProgressReporter
from graphrag.index import PipelineConfig

class ContextSwitcher:
    """ContextSwitcher class definition."""

    def __init__(self):
        #initialize Gremline and Cosmos Db client here.
        pass
    def activate(self, config: PipelineConfig | str, contextId: str | None, reporter: ProgressReporter):
        """Activate the context."""
        #1. read the context id to fileId mapping.
        #2. read the file from storage.
        #3. LanceDB: use cosmos db client to load data into Cosmos DB.
        #4. KustoDB: use Kusto client to load embedding data into Kusto.

        return 0

    def deactivate(self, config: PipelineConfig | str, contextId: str | None, reporter: ProgressReporter):
        """DeActivate the context."""
        #1. Delete all the data for a given context id.
        return 0