import os
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient


class BlobStorageClient:
    """The Blob-Storage implementation."""

    _connection_string: str | None
    _container_name: str
    _path_prefix: str
    _encoding: str
    _storage_account_blob_url: str | None

    def __init__(
        self,
        connection_string: str | None,
        container_name: str,
        encoding: str | None = None,
        path_prefix: str | None = None,
        storage_account_blob_url: str | None = None,
    ):
        """Create a new BlobStorage instance."""
        if connection_string:
            self._blob_service_client = BlobServiceClient.from_connection_string(
                connection_string
            )
        else:
            if storage_account_blob_url is None:
                msg = "Either connection_string or storage_account_blob_url must be provided."
                raise ValueError(msg)

            self._blob_service_client = BlobServiceClient(
                account_url=storage_account_blob_url,
                credential=DefaultAzureCredential(managed_identity_client_id=os.getenv('AZURE_CLIENT_ID'), exclude_interactive_browser_credential = False),
            )
        self._encoding = encoding or "utf-8"
        self._container_name = container_name
        self._connection_string = connection_string
        self._path_prefix = path_prefix or ""
        self._storage_account_blob_url = storage_account_blob_url
        self._storage_account_name = (
            storage_account_blob_url.split("//")[1].split(".")[0]
            if storage_account_blob_url
            else None
        )
        #log.info(
        #    "creating blob storage at container=%s, path=%s",
        #    self._container_name,
        #    self._path_prefix,
        #)

    def get_blob_service_client(self):
        """Get the BlobServiceClient instance."""
        return self._blob_service_client
    
    def get_container_client(self):
        """Get the container client instance."""
        return self._blob_service_client.get_container_client(self._container_name)
