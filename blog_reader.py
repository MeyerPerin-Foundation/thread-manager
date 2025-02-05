import requests
from bs4 import BeautifulSoup
import ai

import logging
logger = logging.getLogger("tm-blog-reader")

def get_mpf_blog_post_content(url: str):
    # Fetch the content of the URL
    response = requests.get(url)
    response.raise_for_status()  # Ensure the request was successful

    # Parse the HTML content
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract and return the text of the blog post
    # Adjust the selector as needed to match the structure of the webpage
    article_text = soup.find('article').get_text(separator="\n", strip=True)
    article_title = soup.find('h1').get_text()
    return article_title, article_text

def blog_li_full_text(url):
    title, content = get_mpf_blog_post_content(url)
    return f"{title}\n\n{content}"


def blog_li_summary(url):
    title, content = get_mpf_blog_post_content(url)
    generated_post = ai.generate_blog_post_summary(title, content, "LinkedIn")
    logger.info(f"Generated post for LinkedIn:\n {generated_post}")
    return generated_post

def blog_bt_summary(url):
    title, content = get_mpf_blog_post_content(url)
    generated_post = ai.generate_blog_post_summary(title, content, "Bluesky")
    logger.info(f"Generated post for Bluesky:\n {generated_post}")
    return generated_post

if __name__ == "__main__":
    url =  "https://meyerperin.org/posts/2024-12-02-blog-comments.html"
    logger.info(blog_li_summary(url))