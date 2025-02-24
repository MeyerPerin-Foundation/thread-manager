import requests
from bs4 import BeautifulSoup
import utils.ai.ai as ai

import logging
logger = logging.getLogger("tm-blog-reader")

def get_mpf_blog_post_content(url: str):
    # Fetch the content of the URL
    response = requests.get(url)
    response.raise_for_status()  # Ensure the request was successful

    # Parse the HTML content
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the first h1 element for the title
    article_title = soup.find('h1').get_text(strip=True)

    # Extract the main image from the meta tag (og:image)
    meta_image = soup.find("meta", property="og:image")
    main_image = meta_image["content"] if meta_image and meta_image.has_attr("content") else None
    image_url = main_image

    # Extract and return the text of the blog post
    # Adjust the selector as needed to match the structure of the webpage
    article_html = soup.find('article').decode_contents()

    return article_title, image_url, article_html

def html_to_text(html):
    soup = BeautifulSoup(html, 'html.parser')
    return soup.get_text(strip=True, separator="\n")

def blog_li_full_text(url):
    title, image_url, article_html = get_mpf_blog_post_content(url)
    article_html = BeautifulSoup(article_html, 'html.parser')

    # remove subheaders and links
    for subheader in article_html.find_all(['h2', 'h3', 'h4']):
        subheader.decompose()

    # replace bullet points with "-"
    for ul in article_html.find_all('ul'):
        for li in ul.find_all('li'):
            li.insert(0, "- ")
            li.unwrap()
    for ol in article_html.find_all('ol'):
        for li in ol.find_all('li'):
            li.insert(0, "- ")
            li.unwrap()
            
    # remove all links
    for link in article_html.find_all('a'):
        link.unwrap()

    # Replace images with "[Image in blog post, link below]"
    for img in article_html.find_all('img'):
        img.replace_with("[Image in blog post]")

    # Replace tables with "[Table in blog post, link below]"
    for table in article_html.find_all('table'):
        table.replace_with("[Table in blog post]")

    # replace code blocks with "[Code block in blog post, link below]"
    for code in article_html.find_all('pre'):
        code.replace_with("[Code block in blog post]")

    article_text = article_html.get_text(strip=True, separator=" ")
    generated_post = ai.fix_blog_post(title, article_text, "LinkedIn")
    logger.info(f"Generated post content for LinkedIn:\n {generated_post}")    

    return title, image_url, generated_post

def blog_li_summary(url):
    title, image_url, content = get_mpf_blog_post_content(url)
    generated_post = ai.generate_blog_post_summary(title, html_to_text(content), "LinkedIn")
    logger.info(f"Generated post content for LinkedIn:\n {generated_post}")
    return title, image_url, generated_post

def blog_bt_summary(url):
    title, image_url, content = get_mpf_blog_post_content(url)
    generated_post = ai.generate_blog_post_summary(title, html_to_text(content), "Bluesky")
    logger.info(f"Generated post content for Bluesky:\n {generated_post}")
    return title, image_url, generated_post
