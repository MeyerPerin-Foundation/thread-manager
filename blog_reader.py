import requests
from bs4 import BeautifulSoup

def get_mpf_blog_post_content(url: str) -> (str, str):
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

def main():
    # Example usage
    url = "https://meyerperin.org/posts/2024-02-01-openai-concurrency.html"
    title, content = get_mpf_blog_post_content(url)
    print(f"Title: {title}\nContent: {content}")

if __name__ == "__main__":
    main()