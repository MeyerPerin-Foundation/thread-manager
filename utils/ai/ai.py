from openai import AzureOpenAI, BadRequestError
import app_config
from .prompts_db import PromptsDB
import datetime
import pytz
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


logger = logging.getLogger("tm-ai")
logger.setLevel(logging.INFO)

def _get_client() -> AzureOpenAI:
    return AzureOpenAI(
        azure_endpoint=app_config.AZURE_OPENAI_ENDPOINT,
        api_key=app_config.AZURE_OPENAI_KEY,
        api_version=app_config.AZURE_OPENAI_API_VERSION,
    )


def _get_prompt(prompt_name: str, version: int = None) -> str:
    prompts = PromptsDB()
    return prompts.get_prompt(prompt_name, version)


def _test_image_chooser():
    image_url_1 = "https://threadmanager.blob.core.windows.net/bird-buddy/1ff3cb14-d5df-413a-a156-08a58c376ce8.jpg"
    image_url_2 = "https://threadmanager.blob.core.windows.net/bird-buddy/6dd9f4ae-a5fc-4a75-b7fc-fde014fa11ca.jpg"
    image_url_3 = "https://threadmanager.blob.core.windows.net/bird-buddy/9d7ec008-f410-4ea1-94f5-2c65bde9262d.jpg"
    # image_url_4 = "https://threadmanager.blob.core.windows.net/bird-buddy/1482ef3b-de5c-4753-9f03-bd49387a2b87.jpg"

    logger.info(choose_best_bird_image([image_url_1, image_url_2, image_url_3]))

def handle_excess_retries(retry_state):
    logger.error(f"Exceeded retries: {retry_state}")
    return False

def choose_best_bird_image(image_url_list) -> str:
    # Cut the list at 4
    if len(image_url_list) > 4:
        logger.info(
            f"The list has {len(image_url_list)} images. Cutting the list of images to 4."
        )
        image_url_list = image_url_list[:4]

    client = _get_client()
    prompt = _get_prompt("choose_best_bird_image")

    msg = [
        {
            "role": "system",
            "content": "You are a photographer and social media content creator",
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
            ],
        },
    ]

    for i, image_url in enumerate(image_url_list):
        msg[1]["content"].append({
            "type": "text",
            "text": "The next image ID is " + str(i + 1),
        })
        msg[1]["content"].append({"type": "image_url", "image_url": {"url": image_url}})

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=msg,
    )

    chosen_image = response.choices[0].message.content

    if chosen_image == "1":
        return image_url_list[0]
    elif chosen_image == "2":
        return image_url_list[1]
    elif chosen_image == "3":
        return image_url_list[2]
    elif chosen_image == "4":
        return image_url_list[3]
    else:
        logger.warning("GPT chose an invalid image number. Returning the first image.")
        return image_url_list[0]

@retry(
    retry=retry_if_exception_type((BadRequestError)),  
    stop=stop_after_attempt(3),  
    wait=wait_exponential(multiplier=1, min=1, max=10),  
    retry_error_callback=handle_excess_retries
)
def good_birb(image_url):
    prompts = PromptsDB()

    prompt = prompts.get_prompt("good_birb")
    openai_client = _get_client()

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a photography critic and social media content creator",
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                },
            ],
        )
        return "yes" in response.choices[0].message.content.lower()
    except Exception as e:
        logger.error(f"Exception processing image {image_url} and prompt {prompt}")
        if isinstance(e, BadRequestError):
            logger.error(f"Handling {e} with tenacity")
            raise e
        else:
            logger.error(f"Handling {e} without tenacity")
            return False

def generate_blog_post_summary(title, content, target_site):
    openai_client = AzureOpenAI(
        azure_endpoint=app_config.AZURE_OPENAI_ENDPOINT,
        api_key=app_config.AZURE_OPENAI_KEY,
        api_version=app_config.AZURE_OPENAI_API_VERSION,
    )

    prompts = PromptsDB()

    if target_site == "LinkedIn":
        prompt = prompts.get_prompt("li_blog_promo")
    elif target_site == "Bluesky" or target_site == "Threads":
        prompt = prompts.get_prompt("bt_blog_promo")
    else:
        logger.warning(f"Invalid target site {target_site}")
        prompt = prompts.get_prompt("bt_blog_promo")

    prompt = prompt.replace("{title}", title)
    prompt = prompt.replace("{content}", content)


    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": f"You are business reporter for Wired, posting to {target_site}",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content


def generate_caption_for_bird_picture(
    image_url, species=None, created_at=None, location=None, voice=None
):
    client = AzureOpenAI(
        azure_endpoint=app_config.AZURE_OPENAI_ENDPOINT,
        api_key=app_config.AZURE_OPENAI_KEY,
        api_version=app_config.AZURE_OPENAI_API_VERSION,
    )

    if species:
        sp = f" of a {species} "
    else:
        sp = ""

    if created_at:
        # Convert the created_at iso formatted string to a datetime object
        utc_time = datetime.datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        # Define the Central Time timezone
        central_tz = pytz.timezone("US/Central")

        # Convert UTC time to Central Time
        central_time = utc_time.astimezone(central_tz)

        # Format the date and time
        picture_time = central_time.strftime("%B %d, %Y at %I:%M %p")

        pt = f" on {picture_time} "
    else:
        pt = ""

    if location:
        loc = f" in {location}"
    else:
        loc = ""

    if not voice:
        voice = "Sir David Attenborough"

    prompts = PromptsDB()
    prompt = prompts.get_prompt("bird_caption")
    prompt = prompt.replace("{sp}", sp)
    prompt = prompt.replace("{pt}", pt)
    prompt = prompt.replace("{loc}", loc)
    prompt = prompt.replace("{voice}", voice)
    prompt = prompt.replace("{len}, ", str(300 - 45 - len(voice)))

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are a photographer and social media content creator",
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            },
        ],
        temperature=0.8,
    )

    return response.choices[0].message.content

def fix_blog_post(title, content, target_site):
    openai_client = AzureOpenAI(
        azure_endpoint=app_config.AZURE_OPENAI_ENDPOINT,
        api_key=app_config.AZURE_OPENAI_KEY,
        api_version=app_config.AZURE_OPENAI_API_VERSION,
    )

    prompt = "The blog post below needs to be reviewed for grammar, spelling, formatting and punctuation." 
    prompt += "Don't add any additional content, don't change the meaning, just fix grammar, spelling, formatting and punctuation."
    prompt += "Add appropriate line breaks and paragraph breaks."
    prompt += "Don't return the title, just the blog post content."
    prompt += "Return the fixed blog post only in plain text, no other text. "
    prompt += f"\n\nTitle: {title}\n\n"
    prompt += f"{content}"

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": f"You are a reviewer for Wired Magazine",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    pass
