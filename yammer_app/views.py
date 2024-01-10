from django.conf import settings
import urllib.parse
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import render
from rest_framework import status
import requests
from sanvad_project.settings import r
import json
from dotenv import load_dotenv
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
import os
import io

import requests
from requests.auth import HTTPBasicAuth

from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload


# Yammer Data
@api_view(["GET"])
def get_api(request):
    try:
        ##r = redis.Redis(host="localhost", port=6379, decode_responses=True)
        return Response({"data": json.loads(r.get("yammer_data"))})
    except e:
        print("error", e)
        return Response({"error": e})


class GoogleDriveService:
    def __init__(self):
        self._SCOPES = ["https://www.googleapis.com/auth/drive"]

        _base_path = os.path.dirname(__file__)
        _credential_path = "healthy-mender-378707-54fc2eb13e3f.json"

        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = _credential_path

    def build(self):
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            os.getenv("GOOGLE_APPLICATION_CREDENTIALS"), self._SCOPES
        )
        service = build("drive", "v3", credentials=creds)
        return service


# GET IMAGES FROM GDRIVE AND SAVE TO LOCALHOST
@api_view(["GET"])
def getFileListFromGDrive(request):
    try:
        selected_fields = "files(id,name,webViewLink)"
        g_drive_service = GoogleDriveService().build()
        list_file = g_drive_service.files().list(fields=selected_fields).execute()
        for _file in list_file.get("files"):
            download_file(_file["id"], _file["name"])
        return Response({"files": list_file.get("files")})
    except Exception as e:
        return Response({"e": e, "status": 400})


def download_file(file_id, file_name):
    try:
        g_drive_service = GoogleDriveService().build()
        request = g_drive_service.files().get_media(fileId=file_id)
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            # print(f"Download {int(status.progress() * 100)}.")

    except HttpError as error:
        print(f"An error occurred: {error}")
        file = None

    try:
        if file.getvalue():
            media_root = settings.MEDIA_ROOT
            yammer_folder = os.path.join(media_root, "yammer")

            # Create the "yammer" folder if it doesn't exist
            if not os.path.exists(yammer_folder):
                os.makedirs(yammer_folder)

            full_path = os.path.join(yammer_folder, file_name)
            with open(full_path, "wb") as f:
                f.write(file.getvalue())
                print("File downloaded successfully")
    except Exception as e:
        print("Error:", e)


# DONE 👍
def download_sharpoint_file():
    # Replace these with your actual values
    load_dotenv()
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    tenant_id = os.getenv("TENANT_ID")

    # Get an access token using client credentials flow
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    token_data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://graph.microsoft.com/.default",
    }
    token_response = requests.post(token_url, data=token_data).json()
    access_token = token_response["access_token"]

    # Make a request to get file information
    file_url = f"https://graph.microsoft.com/v1.0/sites/adorians.sharepoint.com,a5150817-1f02-4c6f-9bbb-c65e5ededcb6,3bafd510-ca90-4a38-a7f5-d72ed5c325a0/drive/root:/Apps/Viva%20Engage/Ador_Pune_Final_10 MB.mp4"
    file_response = requests.get(
        file_url, headers={"Authorization": "Bearer " + access_token}
    ).json()

    # Get the download URL
    download_url = file_response["@microsoft.graph.downloadUrl"]

    # Download the file
    response = requests.get(
        download_url, headers={"Authorization": "Bearer " + access_token}
    )

    media_root = settings.MEDIA_ROOT
    yammer_folder = os.path.join(media_root, "yammer")

    # Create the "yammer" folder if it doesn't exist
    if not os.path.exists(yammer_folder):
        os.makedirs(yammer_folder)

    full_path = os.path.join(yammer_folder, "Ador_Pune_Final_10 MB.mp4")
    with open(full_path, "wb") as f:
        f.write(response.content)
        print("File downloaded successfully")
