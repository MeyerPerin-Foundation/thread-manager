from mpfutils.cosmosdb import CosmosDBContainer
from mpfutils.azsclient import AzsContainerClient

class FolderContent:
    def __init__(self):
        self.storage: AzsContainerClient("posts", "folder_content")
        self.db: CosmosDBContainer("posts", "folder_content")


