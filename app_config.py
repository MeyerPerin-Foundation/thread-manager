import os
import logging
from dotenv import load_dotenv

RUNNING_LOCALLY = os.getenv("WEBSITE_HTTPLOGGING_RETENTION_DAYS") is None

if RUNNING_LOCALLY:
    print("Running locally")
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("identity.web").setLevel(logging.WARNING)
    logging.getLogger("msal").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("birdbuddy").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("yfinance").setLevel(logging.WARNING)
    logging.getLogger("peewee").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("exifread").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    load_dotenv()
else:
    print("Running in Azure")
    logging.basicConfig(level=logging.INFO)

logging.getLogger("azure").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("matplotlib").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

AUTHORITY = os.getenv("AUTHORITY") 
AUTHORIZED_USER = os.getenv("AUTHORIZED_USER")

# Application (client) ID of app registration
CLIENT_ID = os.getenv("CLIENT_ID")

# Application's generated client secret: never check this into source control!
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

# Security token to prevent unauthorized access to my API
API_TOKEN = os.getenv("API_TOKEN")  

REDIRECT_PATH = "/getAToken"  # Used for forming an absolute URL to your redirect URI.
# The absolute URL must match the redirect URI you set
# in the app's registration in the Azure portal.

# You can find more Microsoft Graph API endpoints from Graph Explorer
# https://developer.microsoft.com/en-us/graph/graph-explorer
ENDPOINT = 'https://graph.microsoft.com/v1.0/users'  # This resource requires no admin consent

# You can find the proper permission names from this document
# https://docs.microsoft.com/en-us/graph/permissions-reference
SCOPE = ["User.ReadBasic.All"]

# Tells the Flask-session extension to store sessions in the filesystem
SESSION_TYPE = "filesystem"
# Using the file system will not work in most production systems,
# it's better to use a database-backed session store instead.

# Cosmos DB
COSMOS_KEY = os.getenv("COSMOS_KEY")
COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")

# Azure Storage
STORAGE_CONNECTION_STRING=os.getenv("STORAGE_CONNECTION_STRING")

# OpenAI
OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT=os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_KEY=os.getenv("AZURE_OPENAI_KEY")
AZURE_OPENAI_API_VERSION=os.getenv("AZURE_OPENAI_API_VERSION")

# BirdBuddy
BIRD_BUDDY_USER=os.getenv("BIRD_BUDDY_USER")
BIRD_BUDDY_PASSWORD=os.getenv("BIRD_BUDDY_PASSWORD")

# Bluesky
BSKY_APP_PWD = os.getenv("BSKY_APP_PWD")
BSKY_USER = os.getenv("BSKY_USER")

# Threads
THREADS_USER_ID = os.getenv("THREADS_USER_ID")
THREADS_TEST_TOKEN = os.getenv("THREADS_TEST_TOKEN")

# LinkedIn
LINKEDIN_PERSON_ID = os.getenv("LINKEDIN_PERSON_ID")
LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")

# Azure Monitor
APPINSIGHTS_CONNECTION_STRING = os.getenv("APPINSIGHTS_CONNECTION_STRING")

# FRED
FRED_API_KEY = os.getenv("FRED_API_KEY")

# Imgflip
IMGFLIP_USERNAME = os.getenv("IMGFLIP_USERNAME")
IMGFLIP_PASSWORD = os.getenv("IMGFLIP_PASSWORD")

# Alpha Vantage
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

# Home
LOCAL_TIME_ZONE = os.getenv("LOCAL_TIME_ZONE")

# Currently only one user
THREAD_MANAGER_SUBSCRIPTION_ID = os.getenv("THREAD_MANAGER_SUBSCRIPTION_ID")