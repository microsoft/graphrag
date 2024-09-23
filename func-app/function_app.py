import azure.functions as func
import datetime
import json
import logging
import csv
import codecs
from graphrag.index.cli import index_cli

app = func.FunctionApp()

@app.function_name('IndexingPipelineFunc')
@app.route(route="index", auth_level=func.AuthLevel.ANONYMOUS)
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
