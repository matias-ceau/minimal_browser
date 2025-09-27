from __future__ import annotations

from typing import Any, Dict, Optional

try:
    import boto3  # type: ignore[import-untyped]
except ImportError as exc:  # pragma: no cover - optional dependency guard
    raise ImportError(
        "boto3 is required for ObjectStorage and KVStorage; install minimal-browser with the 'storage' extras."
    ) from exc

try:
    import chromadb  # type: ignore[import-untyped]
except ImportError as exc:  # pragma: no cover - optional dependency guard
    raise ImportError(
        "chromadb is required for VectorStorage; install minimal-browser with the 'storage' extras."
    ) from exc


class ObjectStorage:
    def __init__(self, bucket_name: str):
        self.s3 = boto3.client("s3")
        self.bucket_name = bucket_name

    def upload(self, key: str, data: bytes) -> None:
        self.s3.put_object(Bucket=self.bucket_name, Key=key, Body=data)

    def download(self, key: str) -> bytes:
        response = self.s3.get_object(Bucket=self.bucket_name, Key=key)
        return response["Body"].read()


class KVStorage:
    def __init__(self, table_name: str):
        self.client = boto3.client("dynamodb")
        self.table_name = table_name

    def put_item(self, item: Dict[str, Any]) -> None:
        self.client.put_item(TableName=self.table_name, Item=item)

    def get_item(self, key: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        response = self.client.get_item(TableName=self.table_name, Key=key)
        return response.get("Item")


class VectorStorage:
    def __init__(self, collection_name: str):
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def add_vector(self, vector: str, metadata: Dict[str, Any]) -> None:
        self.collection.add(documents=[vector], metadatas=[metadata])

    def query(self, vector: str, n_results: int = 5) -> Dict[str, Any]:
        return self.collection.query(queries=[vector], n_results=n_results)
