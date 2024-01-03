import logging
import logging.handlers
import os
import requests
import time
import pandas as pd

from datetime import datetime
from pytz import timezone
from collections import OrderedDict

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

def request_track_report(endpoint, sessionkey, org_id, filter_cond={"$and":[]}):
    headers = {
        "Authorization": "Bearer " + sessionkey
    }

    params = f"?organization_id={org_id}&filter_condition={filter_cond}"
    request_url = base_url+endpoint+params
    response = requests.get(request_url, headers=headers)

    # Check the response status code
    if response.status_code == 200:
        # Response was successful, print the response content
        logger.info("Request of course report success")
        res_json = response.json()
    else:
        # Response was not successful, print the error message
        logger.error("Error: " + response.reason)
        logger.error("Request failed for some reason.")

    return res_json['download_token']

def get_remote_file(endpoint, sessionkey, download_token):
    headers = {
        "Authorization": "Bearer " + sessionkey
    }

    params = f"?download_token={download_token}"
    request_url = base_url+endpoint+params
    response = requests.get(request_url, headers=headers)

    # Check the response status code
    if response.status_code == 200:
        # Response was successful, print the response content
        res_json = response.json()
    else:
        # Response was not successful, print the error message
        logger.error("Error: " + response.reason)

    return res_json['url']

def cal_track_stats(report_filename):
    student_stat_dict = OrderedDict()

    data_frame = pd.read_excel(report_filename, sheet_name=None, header=0)
    sheet_names = list(data_frame.keys())

    # filter "student" records
    df = data_frame["종합"]
    student_df = df[df['권한'] == 'student'] # 권한만료(nothing)도 필요

    for _, row in student_df.iterrows():
        student_name = row[2]
        if student_name in student_stat_dict:
            student_stat_dict[student_name]['subjects'].append((row[1], row[5]))
        else:
            student_stat_dict.setdefault(student_name, {"email": "", "subjects": []})
            student_stat_dict[student_name]['email'] = row[3]
            student_stat_dict[student_name]['subjects'].append((row[1], row[5]))

    # logger.info(student_stat_dict)

    os.remove(report_filename)
    return student_stat_dict

def get_stats_result(course_report_endpoint, remote_file_endpoint, org_id, api_sessionkey):
    report_download_token = request_track_report(course_report_endpoint, api_sessionkey, org_id)
    logger.info("Download token is: " + report_download_token)
    
    for percent_complete in range(100):
        time.sleep(0.1)
        logger.info(f"Waiting before get remote file... {percent_complete}")
    
    down_report_file_name = f"report_organization_{org_id}_{formatted_now_date}.xlsx"
    report_blob_url = get_remote_file(remote_file_endpoint, api_sessionkey, report_download_token)

    if report_blob_url is not None:
        response = requests.get(report_blob_url)
        if response.status_code == 200:
            with open(down_report_file_name, "wb") as f:
                f.write(response.content)
        else:
            print("Error: " + response.reason)
        
        student_stat_result_dict = cal_track_stats(down_report_file_name)
        lv_one_qualified_email_list = []

        prereq_subjs = {
            "pre_one": ["파이썬 기초 1", "(초급)파이썬 기초 1"],
            "pre_two": ["파이썬 기초 2", "(초급)파이썬 기초 2"],
            "pre_three": ["파이썬 업무자동화 기초편"]
        }

        for student_name in student_stat_result_dict:
            enrolled_courses = student_stat_result_dict[student_name]['subjects']
            found_pre_one, found_pre_two, found_pre_three = False, False, False
            for item in enrolled_courses:
                if item[0] in prereq_subjs['pre_one']:
                    if item[1] == 'O':
                        found_pre_one = True

                if item[0] in prereq_subjs['pre_two']:
                    if item[1] == 'O':
                        found_pre_two = True

                if item[0] in prereq_subjs['pre_three']:
                    if item[1] == 'O':
                        found_pre_three = True

            if found_pre_one and found_pre_two and found_pre_three:
                lv_one_qualified_email_list.append(student_stat_result_dict[student_name]['email'])

        logger.info(lv_one_qualified_email_list)
    else:
        logger.error("에러가 발생했습니다!")

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
    course_report_endpoint = "/global/organization/stats/course/report/request/"
    remote_file_endpoint = "/global/remote_file/temp/get/"
    org_id = 1038 # lginnotek-ai

    now_datetime = datetime.now(timezone('Asia/Seoul'))
    formatted_now_date = now_datetime.strftime("%Y%m%d_%H%M%S")

    auth_post_data = {
        "email": "kwanhong.lee@elicer.com",
        "password": "Younha486!!@@"
    }

    get_auth_token_json = get_auth_token(base_url+auth_login_endpoint, auth_post_data)
    if get_auth_token_json['_result']['status'] == "ok":
        api_sessionkey = get_auth_token_json['sessionkey']
        logger.info("Sessionkey is: " + api_sessionkey)

    get_stats_result(course_report_endpoint, remote_file_endpoint, org_id, api_sessionkey)