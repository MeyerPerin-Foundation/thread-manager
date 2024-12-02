from openai import AzureOpenAI
import app_config
import pprint

def choose_best_bird_image(image_url_list) -> str:

    # Cut the list at 4
    if len(image_url_list) > 4:
        print("Cutting the list of images to 4")
        image_url_list = image_url_list[:4]


    client = AzureOpenAI(azure_endpoint=app_config.AZURE_OPENAI_ENDPOINT, 
                         api_key=app_config.AZURE_OPENAI_KEY, 
                         api_version=app_config.AZURE_OPENAI_API_VERSION)
    # prompt = app_config.get_prompt("choose_best_bird_image")
    prompt="I will present you with up to four images. These are images of birds that will be posted to social media. My objective is to show birds in funny poses, or in pictures shot with good composition, in order to get more likes for my posts. Of the images presented, which one should I use? Respond only with the number of the image, like '1'."

    
    msg = [
            {"role": "system", "content": "You are a photographer and social media content creator"},
            {"role": "user", "content": [
                {"type": "text", "text": prompt},]}]
    
    for i, image_url in enumerate(image_url_list):
        msg[1]["content"].append({"type": "text", "text": "The next image ID is " + str(i+1)})
        msg[1]["content"].append({"type": "image_url", "image_url": {"url": image_url}})

    pprint.pprint(msg)
    
    response = client.chat.completions.create(
        model="gpt-4o", 
        messages=msg,                
    )

    chosen_image = response.choices[0].message.content

    print(f"GPT chose image {chosen_image}")

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


if __name__ == "__main__":
    # Test images
    image_url_1 = "https://threadmanager.blob.core.windows.net/bird-buddy/1ff3cb14-d5df-413a-a156-08a58c376ce8.jpg"
    image_url_2 = "https://threadmanager.blob.core.windows.net/bird-buddy/6dd9f4ae-a5fc-4a75-b7fc-fde014fa11ca.jpg"
    image_url_4 = "https://threadmanager.blob.core.windows.net/bird-buddy/1482ef3b-de5c-4753-9f03-bd49387a2b87.jpg"
    image_url_3 = "https://threadmanager.blob.core.windows.net/bird-buddy/9d7ec008-f410-4ea1-94f5-2c65bde9262d.jpg"

    print(choose_best_bird_image([image_url_1, image_url_2, image_url_3]))
