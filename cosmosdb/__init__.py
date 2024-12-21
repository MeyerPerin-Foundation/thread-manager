from ._dbutils import _get_container
from .auth import Auth
from .birds import Birds
from .blog import BlogPosts
from .dashboard import Dashboard
from .motd import MessageOfTheDay
from .prompts import Prompts
from .too_far import TooFar
from .ungovernable import Ungovernable
from .visits import Visits
import logging

__all__ = [
    "_get_container",
    "Auth",
    "Birds",
    "BlogPosts",
    "Dashboard",
    "MessageOfTheDay",
    "Prompts",
    "TooFar",
    "Ungovernable",
    "Visits",
]

logger = logging.getLogger("tm-cosmosdb")
