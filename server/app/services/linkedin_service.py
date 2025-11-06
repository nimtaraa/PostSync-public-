import json
import requests
from langchain.tools import tool
from app.utils.logger import get_logger
from app.utils.constants import (
    LINKEDIN_MISSING_CREDENTIALS,
    LINKEDIN_ASSET_REGISTER_FAIL,
    LINKEDIN_ASSET_UPLOAD_FAIL,
    LINKEDIN_POST_SUCCESS,
    LINKEDIN_POST_FAIL,
    LINKEDIN_NETWORK_ERROR,
    REGISTER_UPLOAD_URL,
    LINKEDIN_POST_API_URL,
)
from app.services.Linkedin_credentials import get_credentials

logger = get_logger(__name__)

def upload_media_to_linkedin(file_path: str) -> str | None:
    """
    Upload an image to LinkedIn and return the asset URN.

    Args:
        file_path (str): Local path to the image file.

    Returns:
        str | None: LinkedIn asset URN if successful, else None.
    """
    access_token, person_urn = get_credentials()
    if not access_token or not person_urn:
        logger.error("❌ LinkedIn credentials not set!")
        return None
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }

    payload = {
        "registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "owner": person_urn,
            "serviceProvider": "LBA"
        }
    }

    try:
        # Step 1: Register upload
        reg_response = requests.post(REGISTER_UPLOAD_URL, headers=headers, json=payload)
        reg_response.raise_for_status()
        reg_data = reg_response.json()

        asset_urn = reg_data["value"]["asset"]
        upload_url = reg_data["value"]["uploadMechanism"][
            "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
        ]["uploadUrl"]

        # Step 2: Upload image
        with open(file_path, "rb") as f:
            upload_response = requests.post(upload_url, data=f, headers={
                "Authorization": f"Bearer {access_token}"
            })
            upload_response.raise_for_status()

        logger.info(f"✅ Image uploaded successfully to LinkedIn Asset API. URN: {asset_urn}")
        return asset_urn

    except requests.exceptions.RequestException as e:
        logger.error(LINKEDIN_ASSET_REGISTER_FAIL.format(error=e))
        return None
    except Exception as e:
        logger.error(LINKEDIN_ASSET_UPLOAD_FAIL.format(error=e))
        return None


# === Post to LinkedIn Tool ===
@tool("post_to_linkedin")
def post_to_linkedin(post_content: str, image_asset_urn: str | None = None) -> str:
    """
    💬 Publish a text or image post to LinkedIn.

    Args:
        post_content (str): The text content to publish.
        image_asset_urn (str | None): Optional LinkedIn asset URN for image.

    Returns:
        str: Status message of the operation.
    """
    access_token, person_urn = get_credentials()
    if not access_token or not person_urn:
        return "Missing LinkedIn credentials"       

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }

    payload = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": post_content},
                "shareMediaCategory": "IMAGE" if image_asset_urn else "NONE"
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
    }

    if image_asset_urn:
        payload["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [
            {"status": "READY", "media": image_asset_urn}
        ]

    try:
        response = requests.post(LINKEDIN_POST_API_URL, headers=headers, data=json.dumps(payload))
        if response.status_code == 201:
            logger.info(LINKEDIN_POST_SUCCESS)
            return LINKEDIN_POST_SUCCESS
        else:
            logger.error(LINKEDIN_POST_FAIL.format(status=response.status_code, error=response.text))
            return LINKEDIN_POST_FAIL.format(status=response.status_code, error=response.text)
    except requests.exceptions.RequestException as e:
        logger.error(LINKEDIN_NETWORK_ERROR.format(error=e))
        return LINKEDIN_NETWORK_ERROR.format(error=e)
