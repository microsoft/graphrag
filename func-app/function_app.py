import azure.functions as func
import logging
import os
import sys
from graphrag.index.cli import index_cli
from graphrag.query.cli import run_local_search

app = func.FunctionApp()
# Create a handler that writes log messages to stdout
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
logging.getLogger().addHandler(handler)

@app.function_name('csindexer')
@app.route(route="index", auth_level=func.AuthLevel.FUNCTION)
def indexing(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    if executing_correct_func_app(req, "csindexer"):
        return func.HttpResponse(
        "Please trigger csindexer Azure function for indexing",
        status_code=200
        )
    
    input_base_dir=None
    if "input_base_dir" in req.params:
        input_base_dir = req.params['input_base_dir']
    
    output_base_dir=None
    if "output_base_dir" in req.params:
        output_base_dir = req.params['output_base_dir']
    index_cli(
        root = "settings",
        verbose=False,
        resume=False,
        memprofile=False,
        nocache=False,
        config=None,
        emit=None,
        dryrun=False,
        init=False,
        overlay_defaults=False,
        cli=True,
        context_id=None,
        context_operation=None,
        community_level=2,
        use_kusto_community_reports=None,
        optimized_search=None,
        input_base_dir=input_base_dir,
        output_base_dir=output_base_dir
    )
    return func.HttpResponse(
        "Wow this first HTTP Function works!!!!",
        status_code=200
    )


@app.function_name('cscontext')
@app.route(route="context_switch", auth_level=func.AuthLevel.FUNCTION)
def context_switch(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    logging.info("Parameters: "+str(req.params))
    if executing_correct_func_app(req, "csindexer"):
        return func.HttpResponse(
        "Please trigger csindexer Azure function for context swithing",
        status_code=200
        )
    if 'context_id' in req.params:
        context_id=req.params['context_id']
        context_command=req.params['context_operation']
        context_files=req.params['files'].split(',')
        logging.info(f"Got context1 command: {context_id} {context_command} {context_files}")
    else:
        return func.HttpResponse(
        "Must send context id and context operation",
        status_code=200
        )

    index_cli(
        root = "settings",
        verbose=False,
        resume=False,
        memprofile=False,
        nocache=False,
        config=None,
        emit=None,
        dryrun=False,
        init=False,
        overlay_defaults=False,
        cli=True,
        context_id=context_id,
        context_operation=context_command,
        community_level=2,
        use_kusto_community_reports=False,
        optimized_search=False,
        files=context_files
    )
    return func.HttpResponse(
        "Context switching completed",
        status_code=200
    )


@app.function_name('csquery')
@app.route(route="query", auth_level=func.AuthLevel.FUNCTION)
def query(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    logging.info("Parameters1: "+str(req.params))
    if executing_correct_func_app(req, "csquery"):
        return func.HttpResponse(
        "Please trigger csquery Azure function for query",
        status_code=200
        )
    if 'context_id' in req.params:
        context_id=req.params['context_id']
        query=req.params['query']
        path=int(req.params['path'])
    else:
        return func.HttpResponse(
        "Must send context id and context operation",
        status_code=200
        )
    logging.info("Query start")
    output = run_local_search(
                None,
                None,
                "settings",
                community_level=2,
                response_type="",
                context_id=context_id,
                query=query,
                optimized_search=False,
                use_kusto_community_reports=False,
                path=path
            )

    return func.HttpResponse(
        "Query completed: "+ output,
        status_code=200
    )


def executing_correct_func_app(req: func.HttpRequest, route: str):
    return os.getenv("ENVIRONMENT") == "AZURE" and  os.getenv("APP_NAME")!= route
            
