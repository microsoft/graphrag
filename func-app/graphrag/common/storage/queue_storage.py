from azure.storage.queue import QueueServiceClient, QueueClient, QueueMessage, BinaryBase64DecodePolicy, BinaryBase64EncodePolicy
from azure.identity import DefaultAzureCredential, InteractiveBrowserCredential
import os

class QueueStorageClient:
    """The Blob-Storage implementation."""
    _account_url: str
    _queue_name: str
    _max_messages: int
    _queue_client: QueueClient

    def __init__(
        self,
        account_url: str | None,
        queue_name: str,
        client_id: str,
        max_message: int = 1
    ):
        self._account_url = account_url
        self._queue_name = queue_name
        self._max_messages = max_message
        self._queue_client = QueueClient(account_url=account_url, queue_name=queue_name, credential=DefaultAzureCredential(managed_identity_client_id=client_id))
    
    def  poll_messages(self):
        messages = self._queue_client.receive_messages(max_messages=self._max_messages)

        return messages
    
    def delete_message(self, message: QueueMessage):
        self._queue_client.delete_message(message=message, pop_receipt=message.pop_receipt)