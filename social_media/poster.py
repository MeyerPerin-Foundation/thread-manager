from .bluesky import Bluesky
from .linkedin import LinkedIn
from .document import SocialMediaDocument, SocialMediaPostResult
import logging

logger = logging.getLogger("tm-poster")
logger.setLevel(logging.DEBUG)

class SocialMediaPoster:
    def __init__(self):
        pass

    def post_document(self, document: SocialMediaDocument, service: str) -> SocialMediaPostResult:
        
        if service == "Bluesky":
            bluesky = Bluesky()
            return bluesky.post_document(document)
        
        if service == "LinkedIn":
            linkedin = LinkedIn()
            return linkedin.post_document(document)
        
        return SocialMediaPostResult(service=service, success=False, result_message="Service not supported", result_code=500)  