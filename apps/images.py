import os

from dotenv import load_dotenv
from imagekitio import ImageKit

load_dotenv()

private_key = os.getenv("PRIVATE_KEY")
public_key = os.getenv("PUBLIC_KEY")
url_endpoint = os.getenv("URL_ENDPOINT")

if private_key and public_key and url_endpoint:
    imagekit = ImageKit(
        private_key=private_key,
        public_key=public_key,
        url_endpoint=url_endpoint,
    )
else:
    imagekit = None


def get_imagekit():
    if imagekit is None:
        raise RuntimeError(
            "ImageKit is not configured. Add PRIVATE_KEY, PUBLIC_KEY, and URL_ENDPOINT to your .env file."
        )
    return imagekit
