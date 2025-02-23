from social_media import SocialMediaPoster
import time

class TestPoster:
    def test_document_creation(self):
        p = SocialMediaPoster()
        id = p.generate_and_queue_document(
            text="This document was added to the queue",
            image_urls=["https://meyerperin.org/images/bird.jpg"],
            urls=["https://meyerperin.org"],
            url_titles=["MeyerPerin Foundation"],
            hashtags=["Test1", "ATProto"],
        )
        # p.post_with_id(id)
        print(id)

    def test_document_posting_by_id(self):
        p = SocialMediaPoster()
        time.sleep(1)
        id = p.generate_and_queue_document(
            text=["This document has been posted by id"],
            urls=["https://meyerperin.org"],
            url_titles=["MeyerPerin Foundation"],
            hashtags=["Test2", "ATProto"],
        )
        p.post_with_id(id)
        assert True

    def test_document_posting_from_queue(self):
        p = SocialMediaPoster()
        time.sleep(1)
        p.post_next_document()
        assert True

        