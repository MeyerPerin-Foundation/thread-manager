from bsky_bridge import BskySession, post_text
import os


def post_to_bsky():
    session = BskySession("lucasmeyer.bsky.social", os.getenv("BSKY_APP_PWD"))
    response = post_text(session, "This is an automated post from the bsky_bridge module.")
    print(response)