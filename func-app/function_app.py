import azure.functions as func
import logging
import os
import sys
from graphrag.index.cli import index_cli
from graphrag.common.storage.queue_storage import QueueStorageClient
from graphrag.common.storage.blob_pipeline_storage import BlobPipelineStorage
from graphrag.query.cli import run_local_search
from utility import find_next_target_blob
from utility import water_mark_target

app = func.FunctionApp()
# Create a handler that writes log messages to stdout
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
logging.getLogger().addHandler(handler)

def initialize_incoming_msg_queue() -> QueueStorageClient:
    # queue_url = 'https://inputdatasetsa.queue.core.windows.net' 
    # queue_name='inputdataetqu'
    # client_id = '500051c4-c242-4018-9ae4-fb983cfebefd'
    
    max_messages = int(os.environ.get("MAX_QUEUE_MESSAGE_COUNT", default="1"))
    queue_url = os.environ.get("AZURE_QUEUE_URL")
    queue_name = os.environ.get("AZURE_QUEUE_NAME")
    client_id = os.environ.get("AZURE_CLIENT_ID")

    queue_storage_client = QueueStorageClient(account_url=queue_url, queue_name=queue_name, client_id=client_id, max_message=max_messages)

    return queue_storage_client

def initialize_watermark_client() -> BlobPipelineStorage:
    # blob_account_url = 'https://inputdatasetsa.blob.core.windows.net'
    # watermark_container_name='watermark'

    blob_account_url = os.environ.get("AZURE_WATERMARK_ACCOUNT_URL")
    watermark_container_name = os.environ.get("WATERMARK_CONTAINER_NAME")
    client_id = os.environ.get("AZURE_CLIENT_ID")

    watermark_storage_account = BlobPipelineStorage(connection_string=None, container_name=watermark_container_name, storage_account_blob_url=blob_account_url)

    return watermark_storage_account
    

@app.function_name('csindexer')
@app.timer_trigger(schedule="0 */10 * * * *", arg_name="mytimer", run_on_startup=True) 
def indexing(mytimer: func.TimerRequest) -> None:
    logging.info('Python HTTP trigger function processed a request.')
    if executing_correct_func_app(req, "csindexer"):
        return func.HttpResponse(
        "Please trigger csindexer Azure function for indexing",
        status_code=200
        )
    
    input_base_dir=None
    # if "input_base_dir" in req.params:
    #     input_base_dir = req.params['input_base_dir']
    
    output_base_dir=None
    # if "output_base_dir" in req.params:
    #     output_base_dir = req.params['output_base_dir']
    
    queue_client = initialize_incoming_msg_queue()
    watermark_client = initialize_watermark_client()
    
    targets = find_next_target_blob(queue_storage_client=queue_client, watermark_client=watermark_client)

    file_target = []
    for target in targets:
        file_target.append(target[0])
    
    try:
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
            output_base_dir=output_base_dir,
            files=file_target
        )

        water_mark_target(targets=targets, queue_storage_client=queue_client, watermark_client=watermark_client)
        
    except:
        logging.error("Error executing the function")
        raise


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
            
