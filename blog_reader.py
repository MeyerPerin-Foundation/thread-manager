import requests
from openai import AzureOpenAI
import app_config
import cosmosdb
from bs4 import BeautifulSoup
import ai

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

def blog_li_summary(url):
    title, content = get_mpf_blog_post_content(url)
    return ai.generate_blog_post_summary(title, content, "LinkedIn")

def blog_bt_summary(url):
    title, content = get_mpf_blog_post_content(url)
    return ai.generate_blog_post_summary(title, content, "Bluesky")

if __name__ == "__main__":
    url =  "https://meyerperin.org/posts/2024-12-02-blog-comments.html"
    print(blog_li_summary(url))