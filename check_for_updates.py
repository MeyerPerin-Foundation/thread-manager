import semantic_kernel as sk
from semantic_kernel import KernelContext
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from dotenv import load_dotenv
import os
import asyncio
import blog_reader
import notifier
import crm
import LinkedInPlugin

def create_kernel() -> sk.Kernel:
    api_key = os.getenv("THREAD_MANAGER_OPENAI_KEY")
    model = os.getenv("OPENAI_DEFAULT_MODEL")
    gpt4 = OpenAIChatCompletion("gpt-4", api_key=api_key)
    kernel = sk.Kernel()
    kernel.add_chat_service("gpt4", gpt4)  
    kernel.import_semantic_plugin_from_directory("plugins", "BlogReader")
    kernel.import_plugin(LinkedInPlugin.LinkedInPlugin(), "LinkedInPlugin")
    return kernel

async def summarize_post(kernel: sk.Kernel, content: str) -> str:
    variables = sk.ContextVariables()
    variables["post_text"] = content
    spf = kernel.plugins["BlogReader"]["SummarizeMPFPost"]
    result = await kernel.run(spf, input_vars=variables)
    blog_post_summary = str(result)
    return blog_post_summary

def send_notification_emails(title, content, url):
    recipients = crm.get_subscribed_contacts()
    notifier.send_email_notification(recipients, 
                                     subject="New blog post by Lucas A. Meyer", 
                                     title=title, 
                                     content=content, 
                                     url=url,
                                     test=True)    

async def generate_linkedin_announcement_text(kernel: sk.Kernel, content: str, url: str) -> str:
    variables = sk.ContextVariables()
    variables["post_text"] = content    
    linkedin_announcement = kernel.plugins["BlogReader"]["CreateLinkedinAnnouncement"]
    result = await kernel.run(linkedin_announcement, input_vars=variables)
    linkedin_announcement_text = str(result)
    return linkedin_announcement_text

async def main():
    kernel = create_kernel()

    url = "https://meyerperin.org/posts/2024-02-01-openai-concurrency.html"
    title, content = blog_reader.get_mpf_blog_post_content(url)

    # blog_post_summary = summarize_post(kernel, content)
    # send_notification_emails(title, blog_post_summary, url)
 
    li_text = await generate_linkedin_announcement_text(kernel, content, url)  

    final_text = f"{li_text}\n\n{url}"

    print(final_text)

    # linkedin_poster = kernel.plugins["LinkedInPlugin"]["CreateTextPost"]
    # result = await kernel.run(linkedin_poster, input_str=li_text)

    # print(result)

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())




