import azure.functions as func
import logging
from graphrag.index.cli import index_cli

app = func.FunctionApp()

@app.function_name('csindexer')
@app.route(route="index", auth_level=func.AuthLevel.FUNCTION)
def indexing(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    
    index_cli(
        root = "",
        verbose=False,
        resume=False,
        memprofile=False,
        nocache=False,
        config=None,
        emit=None,
        dryrun=False,
        init=True,
        overlay_defaults=False,
        cli=True,
        context_id=None,
        context_operation=None,
        community_level=None,
        use_kusto_community_reports=None,
        optimized_search=None
    )
    return func.HttpResponse(
        "Wow this first HTTP Function works!!!!",
        status_code=200
    )
