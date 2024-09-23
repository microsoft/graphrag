from graphrag.config import (
    GraphRagConfig,
)

def get_files_by_contextid(config: GraphRagConfig, context_id: str):
    """Utility function to get files by context id"""
    # General: eventually this will be comming from cosmos db or any other storage
    filesInContext = config.query_context.files
    return filesInContext