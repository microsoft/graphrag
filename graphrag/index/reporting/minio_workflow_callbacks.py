"""A reporter that writes to a MinIO storage."""

import io
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from datashaper import NoopWorkflowCallbacks
from minio import Minio
from minio.error import S3Error


class MinioWorkflowCallbacks(NoopWorkflowCallbacks):
    """A reporter that writes to a MinIO storage."""

    _minio_client: Minio
    _bucket_name: str
    _max_block_count: int = 25000  # 25k blocks per object

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        base_dir: str
    ):  # type: ignore
        """Create a new instance of the MinIOStorageReporter class."""
        if bucket_name is None:
            msg = "No bucket name provided for MinIO storage."
            raise ValueError(msg)
        
        if not endpoint or not access_key or not secret_key:
            msg = "Endpoint, Access Key, and Secret Key must be provided for MinIO storage."
            raise ValueError(msg)

        self._bucket_name = bucket_name

        self._minio_client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=False
        )
        self._bucket_name = bucket_name
        self.access_key = access_key
        self.endpoint = endpoint
        self.secret_key = secret_key
        self.base_dir = base_dir
        if bucket_name == "":
            object_name = f"report/{datetime.now(tz=timezone.utc).strftime('%Y-%m-%d-%H:%M:%S:%f')}.logs.json"
            self._object_name = str(Path(base_dir or "") / object_name)
        
        # Ensure the bucket exists
        if not self._minio_client.bucket_exists(self._bucket_name):
            self._minio_client.make_bucket(self._bucket_name)

        self._num_blocks = 0  # refresh block counter

    def _write_log(self, log: dict[str, Any]):
        # create a new file when block count hits close to 25k
        if self._num_blocks >= self._max_block_count:
            self.__init__(
                self.endpoint,
                self.access_key,
                self.secret_key,
                self._bucket_name,
                self.base_dir
            )

        log_data = json.dumps(log) + "\n"
        try:
            time = f"{datetime.now(tz=timezone.utc).strftime('%Y-%m-%d-%H:%M:%S:%f')}"
            self.base_dir = self.base_dir.replace("${timestamp}",time)
            object_name = f"{self.base_dir}.logs.json"
            self._object_name = str(Path(self.base_dir or "") / object_name)
            current_data = self._minio_client.get_object(self._bucket_name, self._object_name).read().decode("utf-8")
            updated_data = current_data + log_data
        except S3Error as e:
            if e.code == "NoSuchKey":
                updated_data = log_data
            else:
                raise
     
        # 创建一个 BinaryIO 对象
        binary_io_data = io.BytesIO(updated_data.encode("utf-8"))
        self._minio_client.put_object(
            self._bucket_name,
            self._object_name,
            data=binary_io_data,
            length=len(updated_data),
            content_type="application/json"
        )
        # update the log's block count
        self._num_blocks += 1

    def on_error(
        self,
        message: str,
        cause: BaseException | None = None,
        stack: str | None = None,
        details: dict | None = None,
    ):
        """Report an error."""
        self._write_log({
            "type": "error",
            "data": message,
            "cause": str(cause),
            "stack": stack,
            "details": details,
        })

    def on_warning(self, message: str, details: dict | None = None):
        """Report a warning."""
        self._write_log({"type": "warning", "data": message, "details": details})

    def on_log(self, message: str, details: dict | None = None):
        """Report a generic log message."""
        self._write_log({"type": "log", "data": message, "details": details})