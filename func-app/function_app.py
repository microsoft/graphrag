import azure.functions as func
import logging
from graphrag.index.cli import index_cli
from graphrag.query.cli import run_local_search

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


@app.function_name('QUERYFunc')
@app.route(route="query", auth_level=func.AuthLevel.ANONYMOUS)
def query(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    logging.info("Parameters: "+str(req.params))

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
    run_local_search(
                None,
                None,
                '.\\exe',
                community_level=2,
                response_type="",
                context_id=context_id,
                query=query,
                optimized_search=False,
                use_kusto_community_reports=False,
                path=path
            )

    return func.HttpResponse(
        "Query completed",
        status_code=200
    )


@app.function_name('CNTXSwitch')
@app.route(route="context_switch", auth_level=func.AuthLevel.ANONYMOUS)
def context_switch(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    logging.info("Parameters: "+str(req.params))

    if 'context_id' in req.params:
        context_id=req.params['context_id']
        context_command=req.params['context_operation']
        logging.info(f"Got context command: {context_id} {context_command}")
    else:
        return func.HttpResponse(
        "Must send context id and context operation",
        status_code=200
        )

    index_cli(
        root = "exe",
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
        optimized_search=False
    )
    return func.HttpResponse(
        "Context switching completed",
        status_code=200
    )