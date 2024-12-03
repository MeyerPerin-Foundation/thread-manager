from openai import AzureOpenAI
import app_config
import cosmosdb
import pprint

def _get_client() -> AzureOpenAI:
    return AzureOpenAI(azure_endpoint=app_config.AZURE_OPENAI_ENDPOINT, 
                       api_key=app_config.AZURE_OPENAI_KEY, 
                       api_version=app_config.AZURE_OPENAI_API_VERSION)

def _get_prompt(prompt_name: str, version: int = None) -> str:
    return cosmosdb.get_prompt(prompt_name, version)

def choose_best_bird_image(image_url_list) -> str:

    # Cut the list at 4
    if len(image_url_list) > 4:
        print("Cutting the list of images to 4")
        image_url_list = image_url_list[:4]


    client = _get_client()
    prompt = _get_prompt("choose_best_bird_image")
    
    msg = [
            {"role": "system", "content": "You are a photographer and social media content creator"},
            {"role": "user", "content": [
                {"type": "text", "text": prompt},]}]
    
    for i, image_url in enumerate(image_url_list):
        msg[1]["content"].append({"type": "text", "text": "The next image ID is " + str(i+1)})
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
        print("GPT chose an invalid image number. Returning the first image.")
        return image_url_list[0]

def _test_image_chooser():
    image_url_1 = "https://threadmanager.blob.core.windows.net/bird-buddy/1ff3cb14-d5df-413a-a156-08a58c376ce8.jpg"
    image_url_2 = "https://threadmanager.blob.core.windows.net/bird-buddy/6dd9f4ae-a5fc-4a75-b7fc-fde014fa11ca.jpg"
    image_url_4 = "https://threadmanager.blob.core.windows.net/bird-buddy/1482ef3b-de5c-4753-9f03-bd49387a2b87.jpg"
    image_url_3 = "https://threadmanager.blob.core.windows.net/bird-buddy/9d7ec008-f410-4ea1-94f5-2c65bde9262d.jpg"

    print(choose_best_bird_image([image_url_1, image_url_2, image_url_3]))

def generate_blog_post_summary(title, content, target_site):
    openai_client = AzureOpenAI(azure_endpoint=app_config.AZURE_OPENAI_ENDPOINT, 
                         api_key=app_config.AZURE_OPENAI_KEY, 
                         api_version=app_config.AZURE_OPENAI_API_VERSION)

    if target_site == "LinkedIn":
        prompt = cosmosdb.get_prompt("li_blog_promo")
    elif target_site == "Bluesky":
        prompt = cosmosdb.get_prompt("bt_blog_promo")
    else:
        print(f"Invalid target site {target_site}")
        prompt = cosmosdb.get_prompt("bt_blog_promo")

    prompt = prompt.replace("{title}", title)
    prompt = prompt.replace("{content}", content)

    response = openai_client.chat.completions.create(
        model="gpt-4o", 
        messages=[
            {"role": "system", "content": f"You are business reporter for Wired, posting to {target_site}"},
            {"role": "user", "content": prompt}],
        temperature=0.2,
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    _test_image_chooser()