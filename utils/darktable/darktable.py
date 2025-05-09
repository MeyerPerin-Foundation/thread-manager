import os
import exifread 
from pathlib import Path
from typing import Tuple
from PIL import Image, ImageOps
import io
import uuid
from mpfutils.azstorage import AzsContainerClient
from mpfutils.cosmosdb import CosmosDBContainer
from mpfutils.ai import OpenAIClient
import app_config
from datetime import datetime, timezone, timedelta
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("tm-darktable")

class DarkTable:

    def __init__(self, root_dir: str | Path = None):
        self.root_dir = root_dir
        self.azs_client = AzsContainerClient(container_name="users")
        self.oai_client = OpenAIClient(azure=True)
        self.db = CosmosDBContainer("content", "themed_folders")

    def generate_thumbnail(self, src_path: str) -> bytes:
        """
        Generates a thumbnail for the image at src_path
        """
        with Image.open(src_path) as img:
            width = img.width
            # generate a thumbnail with a witdth of 300px and a height that keeps the aspect ratio
            img.thumbnail((300, int((img.height / img.width) * 300)))
            img = ImageOps.exif_transpose(img)
            img = img.convert("RGB")
            img_bytes = io.BytesIO()
            img.save(img_bytes, format="JPEG", quality=85)
            img_bytes.seek(0)
            return img_bytes.read()

    def upload_originals(self):
        """
        Uploads the original exported images to Azure Blob Storage
        """

        subscription_id = app_config.THREAD_MANAGER_SUBSCRIPTION_ID

        for root, dirs, files in os.walk(self.root_dir):
            if "darktable_exported" in root:
                for filename in files:
                    if filename.endswith(".jpg") or filename.endswith(".jpeg"):
                        filepath = os.path.join(root, filename)
                        parent_dir = os.path.basename(os.path.dirname(filepath))

                        # get the parent directory of parent_dir
                        parent_dir = os.path.basename(os.path.dirname(os.path.dirname(filepath)))
                        
                        # replace spaces with - in the parent_dir
                        parent_dir = parent_dir.replace(" ", "-")

                        idpath = os.path.basename(filepath)

                        logger.debug("Processing %s", idpath)

                        id = str(uuid.uuid5(uuid.NAMESPACE_DNS, idpath))
                        idfilename = f"{id}.jpg"
                        blob_path = f"{subscription_id}/themed_folders/photography/{parent_dir}/{idfilename}"
                        thumbnail_blob_path = f"{subscription_id}/themed_folders/photography/{parent_dir}/{id}_thumb.jpg"

                        # check if the blob already exists
                        d = self.db.get_item(id, partition_key=subscription_id)


                        if d and self.azs_client.blob_exists(blob_path):
                            logger.debug("Skipping %s, already exists", blob_path)
                            continue

                        # generate the thumbnail
                        thumbnail = self.generate_thumbnail(filepath)
                        # upload the thumbnail to Azure Blob Storage
                        thumbnail_url = self.azs_client.upload_blob(thumbnail_blob_path, thumbnail, content_type="image/jpeg")

                        # read the image data
                        with open(filepath, 'rb') as f:
                            data = f.read()

                        url = self.azs_client.upload_blob(blob_path, data, content_type="image/jpeg")
                        bird = self.check_for_bird(url)

                        description = self.caption_photo(url)
                        j = self.generate_dict(id, filepath, url, description, bird=bird)
                        j["thumbnail_blob_url"] = thumbnail_url                        
                        j["subscription_id"] = subscription_id
                        j["last_modified"] = datetime.now(timezone.utc).isoformat()
                        self.db.upsert_item(j)

    def caption_photo(self, blob_url: str) -> str:
        """
        Generates a caption for the photo using the OpenAI API
        """
        prompt = "Generate a caption for this photo in 150 characters or less. " 
        response = self.oai_client.run_vision_prompt(prompt, [blob_url])
        if response:
            return response
        else:
            return ""

    def check_for_bird(self, blob_url: str) -> bool:
        """
        Checks if the image contains a bird using the OpenAI API
        """
        prompt = "Does this picture contain a bird? Respond with 'yes' or 'no'."
        response = self.oai_client.run_vision_prompt(prompt, [blob_url])
        if response and "y" in response.lower():
            return True
        else:
            return False
                    
    def generate_dict(self, id: str, src_path: str, blob_url: str, description: str, bird: bool = False) -> dict:
        """
        Generates a dictionary from the file data, including the EXIF data
        """
        j = {}
        j["id"] = id
        if bird:
            j["hashtags"] = ["birds", "photography"]
        else:
            j["hashtags"] = ["photography"]

        j["folder_name"] = "photography"
        j["file_name"] = id + ".jpg"
        j["blob_url"] = blob_url

        with open(src_path, 'rb') as f:
            tags = exifread.process_file(f)
            exif_d = {}
            for tag in tags.keys():
                if tag in ["Image Model", "EXIF DateTimeOriginal",
                            "EXIF ExposureTime", "EXIF FNumber", "EXIF ISOSpeedRatings",
                            "EXIF LensModel", "EXIF FocalLength"]:
                    exif_d[tag] = tags[tag].printable.strip()
        
        if exif_d["Image Model"] == "OM-1MarkII":
            exif_d["Camera"] = "OM-1 MkII"
        else:
            exif_d["Camera"] = exif_d["Image Model"]
        del exif_d["Image Model"]

        if "EXIF LensModel" in exif_d:
            if exif_d["EXIF LensModel"] == "M.Zuiko Digital ED 12-40mm F2.8 PRO":
                exif_d["Lens"] = "OM 12-40mm F2.8"
            elif exif_d["EXIF LensModel"] == "M.Zuiko Digital ED 300mm F4.0 IS PRO":
                exif_d["Lens"] = "OM 300mm F4.0"
            elif exif_d["EXIF LensModel"] == "M.Zuiko Digital ED 100-400mm F5.0-6.3 IS":
                exif_d["Lens"] = "OM 100-400mm F5.0-6.3"
            else:
                exif_d["Lens"] = exif_d["EXIF LensModel"]
            del exif_d["EXIF LensModel"]

        exif_d["Lens"] = exif_d["Lens"].replace("M.Zuiko Digital ED ", "M.Zuiko ")

        if "EXIF DateTimeOriginal" in exif_d:
            date = exif_d["EXIF DateTimeOriginal"].split(" ")[0]
            date = date.split(":")
            date = date[0] + "-" + date[1] + "-" + date[2]

            time = exif_d["EXIF DateTimeOriginal"].split(" ")[1]
            time = time.split(":")
            time = time[0] + ":" + time[1]
            exif_d["date"] = f"{date}@{time}"

            del exif_d["EXIF DateTimeOriginal"]
        
        if "EXIF ExposureTime" in exif_d:
            exif_d["Exposure"] = f"{exif_d["EXIF ExposureTime"]}s"
            del exif_d["EXIF ExposureTime"]
        
        if "EXIF FNumber" in exif_d:
            # Convert the FNumber to a float
            num_dem = exif_d["EXIF FNumber"].split("/")

            if len(num_dem) == 1:
                # If there is no denominator, set it to 1
                num_dem.append("1") 

            exif_d["FNumber"] = f"{float(num_dem[0]) / float(num_dem[1])}"
            # Convert to a string with 2 decimal places
            exif_d["FNumber"] = f"{float(exif_d['FNumber']):.1f}"
            del exif_d["EXIF FNumber"]
        
        if "EXIF ISOSpeedRatings" in exif_d:
            exif_d["ISO"] = exif_d["EXIF ISOSpeedRatings"]
            del exif_d["EXIF ISOSpeedRatings"]

        if "EXIF FocalLength" in exif_d:
            exif_d["Focal Length"] = f"{exif_d['EXIF FocalLength']}mm"
            del exif_d["EXIF FocalLength"]

        j["text"] = f"{description}\n📷:{exif_d['Camera']}\n🔍:{exif_d['Lens']}@{exif_d['Focal Length']}\nf:{exif_d['FNumber']} • {exif_d['ISO']} ISO • {exif_d['Exposure']}\n{exif_d['date']}"

        return j

if __name__ == "__main__":
    root_dir = "C:\\Users\\lucasmeyer\\OneDrive\\Pictures\\darktable"

    darktable = DarkTable(root_dir)
    darktable.upload_originals()
