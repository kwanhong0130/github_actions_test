import logging
import logging.handlers
import os

import requests

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger_file_handler = logging.handlers.RotatingFileHandler(
    "status.log",
    maxBytes=1024 * 1024,
    backupCount=1,
    encoding="utf8",
)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger_file_handler.setFormatter(formatter)
logger.addHandler(logger_file_handler)

def get_auth_token(auth_url, post_data):
    response = requests.post(auth_url, data=post_data)
    res_json = response.json()
    # Check the response status code
    if response.status_code == 200:
        # Response was successful, print the response content
        logger.info("Get auth token success")
    else:
        # Response was not successful, print the error message
        logger.error("Error: " + response.reason)
        logger.error("Auth Failed for some reason.")
    return res_json

if __name__ == "__main__":

    base_url = "https://api-rest.elice.io"
    auth_login_endpoint = "/global/auth/login/"

    auth_post_data = {
        "email": "kwanhong.lee@elicer.com",
        "password": "Younha486!!@@"
    }

    get_auth_token_json = get_auth_token(base_url+auth_login_endpoint, auth_post_data)
    if get_auth_token_json['_result']['status'] == "ok":
        api_sessionkey = get_auth_token_json['sessionkey']
        logger.info("Sessionkey is: " + api_sessionkey)