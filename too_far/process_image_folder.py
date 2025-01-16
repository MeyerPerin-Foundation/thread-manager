from PIL import Image

def download_images_from_azure_storage():
    pass

def download_image_list_from_cosmos_db():
    pass

def create_new_image_list():
    # for each image in the folder
    # check if the image is new
    # if new, add to new image list
    pass

def create_duplicate_image_list():
    # use the <tbd> lib to generate a list of duplicate images
    # for each duplicate image, if it's new, delete it from the new image list
    pass

def process_new_images():
    # for each remaining image in the new image list
    # convert to jpg
    # rename to a guid
    # upload to azure storage
    # add to cosmos db
    pass
    


def main():
    download_image_list_from_cosmos_db()
    download_images_from_azure_storage()

if __name__ == '__main__':
    main()