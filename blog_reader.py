import requests
from openai import OpenAI
import app_config
import cosmosdb
from bs4 import BeautifulSoup

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
    openai_client = OpenAI(api_key=app_config.OPENAI_API_KEY)

    prompt = cosmosdb.get_prompt("li_blog_promo")
    prompt = prompt.replace("{title}", title)
    prompt = prompt.replace("{content}", content)

    response = openai_client.chat.completions.create(
        model="gpt-4o", 
        messages=[
            {"role": "system", "content": "You are a social media manager for Wired, posting to LinkedIn"},
            {"role": "user", "content": prompt}],
        temperature=0.2,
    )

    return response.choices[0].message.content

def blog_bt_summary(url):
    title, content = get_mpf_blog_post_content(url)
    openai_client = OpenAI(api_key=app_config.OPENAI_API_KEY)

    prompt = cosmosdb.get_prompt("bt_blog_promo")
    prompt = prompt.replace("{title}", title)
    prompt = prompt.replace("{content}", content)

    response = openai_client.chat.completions.create(
        model="gpt-4o", 
        messages=[
            {"role": "system", "content": "You are a social media manager for Wired Magazine"},
            {"role": "user", "content": prompt}],
        temperature=0.8,
    )

    return response.choices[0].message.content

if __name__ == "__main__":
    url =  "https://meyerperin.org/posts/2024-03-06-luddites.html"
    print(blog_bt_summary(url))
    print("\n\n***************\n\n")
    print(blog_li_summary(url))