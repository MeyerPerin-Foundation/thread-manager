from azure.storage.blob import BlobServiceClient
import app_config

class AzureStorageClient:
    def __init__(self):
        self.blob_service_client = BlobServiceClient.from_connection_string(app_config.STORAGE_CONNECTION_STRING)

    def upload_blob(self, container_name, blob_name, data):
        blob_client = self.blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        blob_client.upload_blob(data, overwrite=True)
        return blob_client.url

