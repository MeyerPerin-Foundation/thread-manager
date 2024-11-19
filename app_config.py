import os
from dotenv import load_dotenv

if os.getenv("WEBSITE_HTTPLOGGING_RETENTION_DAYS") is None:
    # running locally
    print("Running locally")
    load_dotenv()
else:
    print("Running in Azure")

AUTHORITY = os.getenv("AUTHORITY") 
AUTHORIZED_USER = os.getenv("AUTHORIZED_USER")

# Application (client) ID of app registration
CLIENT_ID = os.getenv("CLIENT_ID")

# Application's generated client secret: never check this into source control!
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

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

COSMOS_KEY = os.getenv("COSMOS_KEY")
COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_DATABASE = os.getenv("COSMOS_DATABASE")

API_TOKEN = os.getenv("API_TOKEN")  
BSKY_APP_PWD = os.getenv("BSKY_APP_PWD")
BSKY_USER = os.getenv("BSKY_USER")
