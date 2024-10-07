from graphrag.index.utils import gen_md5_hash,gen_sha256_hash
from graphrag.common.storage.blob_pipeline_storage import BlobPipelineStorage
from typing import Dict, Any
import os
import re
import json
import logging

log = logging.getLogger(__name__)

class ContextManager:
    """The Blob-Storage implementation."""
    _context_name: str
    _context_id: str
    _store : BlobPipelineStorage
    def __init__(
        self,
        context_name: str | None):

        self._context_name = context_name
        self._context_id = self.__generate_context_id(context_name)
        self._store = self.__intialize_store()

    
    def __generate_context_id(self, content_name):
        keys = { "key" : content_name }

        hash_Id = gen_md5_hash(keys, keys.keys())

        return hash_Id

    def __intialize_store(self) -> BlobPipelineStorage:
        context_store_url = os.environ.get("CONTEXT_STORE_URL", default="https://inputdatasetsa.blob.core.windows.net")
        context_store_contaier_name = os.environ.get("CONTEXT_STORE_CONTAINER_NAME", default="context")

        return BlobPipelineStorage(connection_string=None, container_name=context_store_contaier_name, storage_account_blob_url= context_store_url)
    
    def __generate_init_file_key(self) -> str:
        init_file_name = f"{self._context_id}/{self._context_id}_init.json"
        return init_file_name
    
    def __generate_file_key(self, file_name:str) -> str:
        init_file_name = f"{self._context_id}/contents/{file_name}"
        return init_file_name

    def initialize(self, files: list[str]) -> bool:
        init_file_name = self.__generate_init_file_key()
        
        result = self._store.check_if_exists(init_file_name)
        if result == True:
            return False
        
        values: Dict[str, Any] = dict()

        values['context_name'] = self._context_name
        values['context_id'] = self._context_id
        values['state'] = 'cold'
        values['files'] = files

        value = json.dumps(values)

        self._store.set_sync(key=init_file_name, value=value)

        return True
    
    def __push_to_queue(self, files: list[str]):
        if len(files) <= 0:
            log.info(f"No files to push to the queue for {self._context_name}")
            return

        for file in files:
            file_name = self.__generate_file_key(file)

            self._store.set_sync(file_name, "")

    def switch_context_state(self):
        init_file_name = self.__generate_init_file_key()

        value = self._store.get_sync(key=init_file_name)

        values = json.loads(value)

        if values['state'] == 'hot':
            values['state'] = 'cold'
        else:
            values['state'] = 'hot'
            self.__push_to_queue(values['files'])
        
        value = json.dumps(values)

        self._store.set_sync(key=init_file_name, value=value)
    
    def update(self, files: list[str]):
        init_file_name = self.__generate_init_file_key()

        value = self._store.get_sync(key=init_file_name)

        values = json.loads(value)

        existing_files = values['files']

        new_files = list(set(files) - set(existing_files))

        if len(new_files) <= 0:
            log.info(f"No updates are required for the context {self._context_name}")
            return
        
        files = list(set(existing_files + new_files))
        values['files'] = files

        if values['state'] == 'hot':
            self.__push_to_queue(new_files)
        
        value = json.dumps(values)

        self._store.set_sync(key=init_file_name, value=value)








