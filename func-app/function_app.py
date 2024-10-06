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
@app.timer_trigger(schedule="0 */5 * * * *", arg_name="mytimer", run_on_startup=True) 
def indexing(mytimer: func.TimerRequest) -> None:
    logging.info('Python HTTP trigger function processed a request.')
    
    input_base_dir=None
    # if "input_base_dir" in req.params:
    #     input_base_dir = req.params['input_base_dir']
    
    output_base_dir=None
    # if "output_base_dir" in req.params:
    #     output_base_dir = req.params['output_base_dir']
    
    queue_client = initialize_incoming_msg_queue()
    watermark_client = initialize_watermark_client()
    
    targets = find_next_target_blob(queue_storage_client=queue_client, watermark_client=watermark_client)
    if len(targets) <= 0:
        logging.info("No target to index. Silently skipping the iteration")
        return
    
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


def executing_correct_func_app(req: func.HttpRequest, route: str):
    return os.getenv("ENVIRONMENT") == "AZURE" and  os.getenv("APP_NAME")!= route
            
