from atproto import Client, IdResolver
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os

load_dotenv()


# Initialize client and login
client = Client()
client.login(os.getenv('BSKY_USER'), os.getenv('BSKY_APP_PWD'))

# Time threshold
cutoff = datetime.now(timezone.utc) - timedelta(days=3)

resolver = IdResolver()
did = resolver.handle.resolve("lucas.meyerperin.org")

# get posts by an author
posts = client.get_author_feed(did, filter="posts_no_replies")

to_delete = []

for record in posts.feed:
    print(record)
    print("Likes:", record.record.like_count)
    print("Reposts:", record.repost_count)
    print("Replies:", record.reply_count)
    print("Quotes:", record.quote_count)
    print("Created at:", record.created_at)
    break
    created_at = datetime.fromisoformat(record.value['createdAt'].replace('Z', '+00:00'))
    if created_at < cutoff:
        to_delete.append((record.uri, record.cid))

print(f"Found {len(to_delete)} posts to delete...")

# Deleting posts
for uri, cid in to_delete:
    # if uri contains 3lf5xz64h6s2g, 3lf5xz6mwjs2g, 3lf5xz72yq22g, 3lf5xz7ms2s2g, 3lf5xzaaa522g
    print("Skipping deletion for uri:", uri)
    if any(x in uri for x in ['3lf5xz64h6s2g', '3lf5xz6mwjs2g', '3lf5xz72yq22g', '3lf5xz7ms2s2g', '3lf5xzaaa522g']):
        print(f"Skipping {uri}")
        continue

    print(f"Deleting {uri}")
    # client.com.atproto.repo.delete_record(
    #     repo=did,
    #     collection='app.bsky.feed.post',
    #     rkey=uri.split('/')[-1]
    # )

print("Done.")
