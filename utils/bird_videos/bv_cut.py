from mpfutils.azstorage import AzsContainerClient
from mpfutils.cosmosdb import CosmosDBContainer
from dotenv import load_dotenv
import os

load_dotenv()

cdb = CosmosDBContainer("content", "bird_buddy")

v = cdb.run_query("SELECT * FROM c WHERE NOT IS_DEFINED(c.video_processed) and c.media_type = 'MediaVideo'")

for item in v:
    print(item)

