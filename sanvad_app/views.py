from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import render
from sanvad_app.models import UserManagement
from sanvad_app.serializers import userManagementSerializer
from rest_framework import status
import requests


# GET ALL DATA.
@api_view(["GET"])
def all_data(request):
    obj = UserManagement.objects.all()
    serializers = userManagementSerializer(obj, many=True)
    return Response(serializers.data)


@api_view(["GET", "PUT", "DELETE"])
def data_by_id(request, id):
    match request.method:
        case "GET":
            obj = UserManagement.objects.get(pk=id)
            serializers = userManagementSerializer(obj)
            return Response(
                {"data": serializers.data, "status_code": status.HTTP_200_OK}
            )

        case "PUT":
            obj = UserManagement.objects.get(pk=id)
            serializers = userManagementSerializer(obj, data=request.data)
            if serializers.is_valid():
                serializers.save()
                return Response(
                    {"data": serializers.data, "status_code": status.HTTP_200_OK}
                )
            return Response(
                {
                    "error": serializers.errors,
                    "status_code": status.HTTP_400_BAD_REQUEST,
                }
            )
        case "DELETE":
            obj = UserManagement.objects.get(pk=id)
            obj.delete()
            return Response(
                {"mess": f"Deleted {id}".format(id), "status_code": status.HTTP_200_OK}
            )


# CREATE
@api_view(["POST"])
def create(request):
    serializers = userManagementSerializer(data=request.data)
    if serializers.is_valid():
        print("is valid")
        serializers.save()
        return Response({"mess": "Created", "status": 200})
    print("notvalid")
    return Response({"mess": "Not", "status": 400, "err": serializers.errors})


yammer_data = [
    {
        "created_at": "2023/07/13 06:01:22 +0000",
        "web_url": "https://www.yammer.com/adorians.com/messages/2353123363758080",
        "message": "Prevention of Sexual Harassment ( POSH) Training Conducted for off roll employee's at Chinchwad Plant.",
        "image": [
            {
                "id": 1752184004608,
                "network_id": 5043320,
                "url": "https://www.yammer.com/api/v1/uploaded_files/1752184004608",
                "web_url": "https://www.yammer.com/adorians.com/uploaded_files/1752184004608",
                "type": "image",
                "name": "Posh Training .jpeg",
                "original_name": "Posh Training .jpeg",
                "full_name": "Posh Training ",
                "description": "",
                "content_type": "image/jpeg",
                "content_class": "Image",
                "created_at": "2023/07/13 05:55:37 +0000",
                "owner_id": 974848434176,
                "official": False,
                "storage_type": "SHAREPOINT",
                "target_type": "GROUP",
                "storage_state": False,
                "sharepoint_id": "01XSUWBKFIYSECF3VPDNAZOFERWF57Q7LM",
                "sharepoint_web_url": "https://adorians.sharepoint.com/sites/allcompany/Shared%20Documents/Apps/Viva%20Engage/Posh%20Training%20.jpeg",
                "small_icon_url": "https://s0-azure.assets-yammer.com/assets/images/file_icons/types/picture_orange_39x50_icon.png",
                "large_icon_url": "https://s0-azure.assets-yammer.com/assets/images/file_icons/types/picture_orange_79x102_icon.png",
                "download_url": "https://www.yammer.com/api/v1/uploaded_files/1752184004608/download",
                "thumbnail_url": "https://www.yammer.com/api/v1/uploaded_files/1752184004608/version/1775132737536/thumbnail",
                "preview_url": "https://www.yammer.com/api/v1/uploaded_files/1752184004608/preview/",
                "large_preview_url": "https://www.yammer.com/api/v1/uploaded_files/1752184004608/version/1775132737536/large_preview/",
                "size": 90201,
                "owner_type": "user",
                "last_uploaded_at": "2023/07/13 05:55:37 +0000",
                "last_uploaded_by_id": 974848434176,
                "last_uploaded_by_type": "user",
                "uuid": False,
                "transcoded": False,
                "streaming_url": False,
                "path": "5043320/1752184004608/Posh Training .jpeg",
                "y_id": 1752184004608,
                "overlay_url": "https://www.yammer.com/api/v1/uploaded_files/1752184004608/version/1775132737536/preview/",
                "privacy": "public",
                "group_id": 45776887808,
                "height": 720,
                "width": 1280,
                "scaled_url": "https://www.yammer.com/api/v1/uploaded_files/1752184004608/version/1775132737536/scaled/{{width}}x{{height}}",
                "image": {
                    "url": "https://www.yammer.com/api/v1/uploaded_files/1752184004608/preview/",
                    "size": 90201,
                    "thumbnail_url": "https://www.yammer.com/api/v1/uploaded_files/1752184004608/version/1775132737536/thumbnail",
                },
                "latest_version_id": 1775132737536,
                "status": "not_ams",
                "real_type": "uploaded_file",
            },
            {
                "id": 1752183996416,
                "network_id": 5043320,
                "url": "https://www.yammer.com/api/v1/uploaded_files/1752183996416",
                "web_url": "https://www.yammer.com/adorians.com/uploaded_files/1752183996416",
                "type": "image",
                "name": "Posh Training 1.jpeg",
                "original_name": "Posh Training 1.jpeg",
                "full_name": "Posh Training 1",
                "description": "",
                "content_type": "image/jpeg",
                "content_class": "Image",
                "created_at": "2023/07/13 05:55:37 +0000",
                "owner_id": 974848434176,
                "official": False,
                "storage_type": "SHAREPOINT",
                "target_type": "GROUP",
                "storage_state": False,
                "sharepoint_id": "01XSUWBKGJV6DAJWANW5DKO2BOTAER72WD",
                "sharepoint_web_url": "https://adorians.sharepoint.com/sites/allcompany/Shared%20Documents/Apps/Viva%20Engage/Posh%20Training%201.jpeg",
                "small_icon_url": "https://s0-azure.assets-yammer.com/assets/images/file_icons/types/picture_orange_39x50_icon.png",
                "large_icon_url": "https://s0-azure.assets-yammer.com/assets/images/file_icons/types/picture_orange_79x102_icon.png",
                "download_url": "https://www.yammer.com/api/v1/uploaded_files/1752183996416/download",
                "thumbnail_url": "https://www.yammer.com/api/v1/uploaded_files/1752183996416/version/1775132729344/thumbnail",
                "preview_url": "https://www.yammer.com/api/v1/uploaded_files/1752183996416/preview/",
                "large_preview_url": "https://www.yammer.com/api/v1/uploaded_files/1752183996416/version/1775132729344/large_preview/",
                "size": 79569,
                "owner_type": "user",
                "last_uploaded_at": "2023/07/13 05:55:37 +0000",
                "last_uploaded_by_id": 974848434176,
                "last_uploaded_by_type": "user",
                "uuid": False,
                "transcoded": False,
                "streaming_url": False,
                "path": "5043320/1752183996416/Posh Training 1.jpeg",
                "y_id": 1752183996416,
                "overlay_url": "https://www.yammer.com/api/v1/uploaded_files/1752183996416/version/1775132729344/preview/",
                "privacy": "public",
                "group_id": 45776887808,
                "height": 780,
                "width": 1040,
                "scaled_url": "https://www.yammer.com/api/v1/uploaded_files/1752183996416/version/1775132729344/scaled/{{width}}x{{height}}",
                "image": {
                    "url": "https://www.yammer.com/api/v1/uploaded_files/1752183996416/preview/",
                    "size": 79569,
                    "thumbnail_url": "https://www.yammer.com/api/v1/uploaded_files/1752183996416/version/1775132729344/thumbnail",
                },
                "latest_version_id": 1775132729344,
                "status": "not_ams",
                "real_type": "uploaded_file",
            },
            {
                "id": 1752183988224,
                "network_id": 5043320,
                "url": "https://www.yammer.com/api/v1/uploaded_files/1752183988224",
                "web_url": "https://www.yammer.com/adorians.com/uploaded_files/1752183988224",
                "type": "image",
                "name": "WhatsApp Image 2023-07-13 at 11.21.20 AM (1).jpeg",
                "original_name": "WhatsApp Image 2023-07-13 at 11.21.20 AM (1).jpeg",
                "full_name": "WhatsApp Image 2023-07-13 at 11.21.20 AM (1)",
                "description": "",
                "content_type": "image/jpeg",
                "content_class": "Image",
                "created_at": "2023/07/13 05:55:37 +0000",
                "owner_id": 974848434176,
                "official": False,
                "storage_type": "SHAREPOINT",
                "target_type": "GROUP",
                "storage_state": False,
                "sharepoint_id": "01XSUWBKEMGSOTARRX3FGIQZRCDRNOZ6GN",
                "sharepoint_web_url": "https://adorians.sharepoint.com/sites/allcompany/Shared%20Documents/Apps/Viva%20Engage/WhatsApp%20Image%202023-07-13%20at%2011.21.20%20AM%20(1).jpeg",
                "small_icon_url": "https://s0-azure.assets-yammer.com/assets/images/file_icons/types/picture_orange_39x50_icon.png",
                "large_icon_url": "https://s0-azure.assets-yammer.com/assets/images/file_icons/types/picture_orange_79x102_icon.png",
                "download_url": "https://www.yammer.com/api/v1/uploaded_files/1752183988224/download",
                "thumbnail_url": "https://www.yammer.com/api/v1/uploaded_files/1752183988224/version/1775132721152/thumbnail",
                "preview_url": "https://www.yammer.com/api/v1/uploaded_files/1752183988224/preview/",
                "large_preview_url": "https://www.yammer.com/api/v1/uploaded_files/1752183988224/version/1775132721152/large_preview/",
                "size": 78577,
                "owner_type": "user",
                "last_uploaded_at": "2023/07/13 05:55:37 +0000",
                "last_uploaded_by_id": 974848434176,
                "last_uploaded_by_type": "user",
                "uuid": False,
                "transcoded": False,
                "streaming_url": False,
                "path": "5043320/1752183988224/WhatsApp Image 2023-07-13 at 11.21.20 AM (1).jpeg",
                "y_id": 1752183988224,
                "overlay_url": "https://www.yammer.com/api/v1/uploaded_files/1752183988224/version/1775132721152/preview/",
                "privacy": "public",
                "group_id": 45776887808,
                "height": 780,
                "width": 1040,
                "scaled_url": "https://www.yammer.com/api/v1/uploaded_files/1752183988224/version/1775132721152/scaled/{{width}}x{{height}}",
                "image": {
                    "url": "https://www.yammer.com/api/v1/uploaded_files/1752183988224/preview/",
                    "size": 78577,
                    "thumbnail_url": "https://www.yammer.com/api/v1/uploaded_files/1752183988224/version/1775132721152/thumbnail",
                },
                "latest_version_id": 1775132721152,
                "status": "not_ams",
                "real_type": "uploaded_file",
            },
            {
                "id": 1752185880576,
                "network_id": 5043320,
                "url": "https://www.yammer.com/api/v1/uploaded_files/1752185880576",
                "web_url": "https://www.yammer.com/adorians.com/uploaded_files/1752185880576",
                "type": "image",
                "name": "Posh Training 2.jpeg",
                "original_name": "Posh Training 2.jpeg",
                "full_name": "Posh Training 2",
                "description": "",
                "content_type": "image/jpeg",
                "content_class": "Image",
                "created_at": "2023/07/13 05:58:26 +0000",
                "owner_id": 974848434176,
                "official": False,
                "storage_type": "SHAREPOINT",
                "target_type": "GROUP",
                "storage_state": False,
                "sharepoint_id": "01XSUWBKCA7FRTVCTAVVBK6J3LOOUPN27D",
                "sharepoint_web_url": "https://adorians.sharepoint.com/sites/allcompany/Shared%20Documents/Apps/Viva%20Engage/Posh%20Training%202.jpeg",
                "small_icon_url": "https://s0-azure.assets-yammer.com/assets/images/file_icons/types/picture_orange_39x50_icon.png",
                "large_icon_url": "https://s0-azure.assets-yammer.com/assets/images/file_icons/types/picture_orange_79x102_icon.png",
                "download_url": "https://www.yammer.com/api/v1/uploaded_files/1752185880576/download",
                "thumbnail_url": "https://www.yammer.com/api/v1/uploaded_files/1752185880576/version/1775134613504/thumbnail",
                "preview_url": "https://www.yammer.com/api/v1/uploaded_files/1752185880576/preview/",
                "large_preview_url": "https://www.yammer.com/api/v1/uploaded_files/1752185880576/version/1775134613504/large_preview/",
                "size": 82874,
                "owner_type": "user",
                "last_uploaded_at": "2023/07/13 05:58:26 +0000",
                "last_uploaded_by_id": 974848434176,
                "last_uploaded_by_type": "user",
                "uuid": False,
                "transcoded": False,
                "streaming_url": False,
                "path": "5043320/1752185880576/Posh Training 2.jpeg",
                "y_id": 1752185880576,
                "overlay_url": "https://www.yammer.com/api/v1/uploaded_files/1752185880576/version/1775134613504/preview/",
                "privacy": "public",
                "group_id": 45776887808,
                "height": 720,
                "width": 1280,
                "scaled_url": "https://www.yammer.com/api/v1/uploaded_files/1752185880576/version/1775134613504/scaled/{{width}}x{{height}}",
                "image": {
                    "url": "https://www.yammer.com/api/v1/uploaded_files/1752185880576/preview/",
                    "size": 82874,
                    "thumbnail_url": "https://www.yammer.com/api/v1/uploaded_files/1752185880576/version/1775134613504/thumbnail",
                },
                "latest_version_id": 1775134613504,
                "status": "not_ams",
                "real_type": "uploaded_file",
            },
        ],
        "additional": "Prevention of Sexual Harassment ( POSH) Training Conducted for off roll employee's at Chinchwad Plant.",
        "liked_by": 11,
    },
    {
        "created_at": "2023/07/11 06:39:18 +0000",
        "web_url": "https://www.yammer.com/adorians.com/messages/2350262455738368",
        "message": "Welcome on board!!!",
        "image": [
            {
                "id": 1749865332736,
                "network_id": 5043320,
                "url": "https://www.yammer.com/api/v1/uploaded_files/1749865332736",
                "web_url": "https://www.yammer.com/adorians.com/uploaded_files/1749865332736",
                "type": "image",
                "name": "Joining Announcement Khushwant Midha.jpg",
                "original_name": "Joining Announcement Khushwant Midha.jpg",
                "full_name": "Joining Announcement Khushwant Midha",
                "description": "",
                "content_type": "image/jpeg",
                "content_class": "Image",
                "created_at": "2023/07/11 06:39:02 +0000",
                "owner_id": 2610098839552,
                "official": False,
                "storage_type": "SHAREPOINT",
                "target_type": "GROUP",
                "storage_state": False,
                "sharepoint_id": "01XSUWBKCSD7EVYPIURRGL6N27XM2VNJFY",
                "sharepoint_web_url": "https://adorians.sharepoint.com/sites/allcompany/Shared%20Documents/Apps/Viva%20Engage/Joining%20Announcement%20Khushwant%20Midha.jpg",
                "small_icon_url": "https://s0-azure.assets-yammer.com/assets/images/file_icons/types/picture_orange_39x50_icon.png",
                "large_icon_url": "https://s0-azure.assets-yammer.com/assets/images/file_icons/types/picture_orange_79x102_icon.png",
                "download_url": "https://www.yammer.com/api/v1/uploaded_files/1749865332736/download",
                "thumbnail_url": "https://www.yammer.com/api/v1/uploaded_files/1749865332736/version/1772803104768/thumbnail",
                "preview_url": "https://www.yammer.com/api/v1/uploaded_files/1749865332736/preview/",
                "large_preview_url": "https://www.yammer.com/api/v1/uploaded_files/1749865332736/version/1772803104768/large_preview/",
                "size": 152578,
                "owner_type": "user",
                "last_uploaded_at": "2023/07/11 06:39:02 +0000",
                "last_uploaded_by_id": 2610098839552,
                "last_uploaded_by_type": "user",
                "uuid": False,
                "transcoded": False,
                "streaming_url": False,
                "path": "5043320/1749865332736/Joining Announcement Khushwant Midha.jpg",
                "y_id": 1749865332736,
                "overlay_url": "https://www.yammer.com/api/v1/uploaded_files/1749865332736/version/1772803104768/preview/",
                "privacy": "public",
                "group_id": 45776887808,
                "height": 1152,
                "width": 1152,
                "scaled_url": "https://www.yammer.com/api/v1/uploaded_files/1749865332736/version/1772803104768/scaled/{{width}}x{{height}}",
                "image": {
                    "url": "https://www.yammer.com/api/v1/uploaded_files/1749865332736/preview/",
                    "size": 152578,
                    "thumbnail_url": "https://www.yammer.com/api/v1/uploaded_files/1749865332736/version/1772803104768/thumbnail",
                },
                "latest_version_id": 1772803104768,
                "status": "not_ams",
                "real_type": "uploaded_file",
            }
        ],
        "additional": "Welcome on board!!!",
        "liked_by": 2,
    },
    {
        "created_at": "2023/07/11 06:38:44 +0000",
        "web_url": "https://www.yammer.com/adorians.com/messages/2350261884198912",
        "message": "Welcome on board!!!",
        "image": [
            {
                "id": 1749864947712,
                "network_id": 5043320,
                "url": "https://www.yammer.com/api/v1/uploaded_files/1749864947712",
                "web_url": "https://www.yammer.com/adorians.com/uploaded_files/1749864947712",
                "type": "image",
                "name": "Joining Announcement - Gaurav Patil.jpg",
                "original_name": "Joining Announcement - Gaurav Patil.jpg",
                "full_name": "Joining Announcement - Gaurav Patil",
                "description": "",
                "content_type": "image/jpeg",
                "content_class": "Image",
                "created_at": "2023/07/11 06:38:33 +0000",
                "owner_id": 2610098839552,
                "official": False,
                "storage_type": "SHAREPOINT",
                "target_type": "GROUP",
                "storage_state": False,
                "sharepoint_id": "01XSUWBKDKTHEN4HK4IBEJKZV4UOZYUD7G",
                "sharepoint_web_url": "https://adorians.sharepoint.com/sites/allcompany/Shared%20Documents/Apps/Viva%20Engage/Joining%20Announcement%20-%20Gaurav%20Patil.jpg",
                "small_icon_url": "https://s0-azure.assets-yammer.com/assets/images/file_icons/types/picture_orange_39x50_icon.png",
                "large_icon_url": "https://s0-azure.assets-yammer.com/assets/images/file_icons/types/picture_orange_79x102_icon.png",
                "download_url": "https://www.yammer.com/api/v1/uploaded_files/1749864947712/download",
                "thumbnail_url": "https://www.yammer.com/api/v1/uploaded_files/1749864947712/version/1772802719744/thumbnail",
                "preview_url": "https://www.yammer.com/api/v1/uploaded_files/1749864947712/preview/",
                "large_preview_url": "https://www.yammer.com/api/v1/uploaded_files/1749864947712/version/1772802719744/large_preview/",
                "size": 140497,
                "owner_type": "user",
                "last_uploaded_at": "2023/07/11 06:38:33 +0000",
                "last_uploaded_by_id": 2610098839552,
                "last_uploaded_by_type": "user",
                "uuid": False,
                "transcoded": False,
                "streaming_url": False,
                "path": "5043320/1749864947712/Joining Announcement - Gaurav Patil.jpg",
                "y_id": 1749864947712,
                "overlay_url": "https://www.yammer.com/api/v1/uploaded_files/1749864947712/version/1772802719744/preview/",
                "privacy": "public",
                "group_id": 45776887808,
                "height": 1152,
                "width": 1152,
                "scaled_url": "https://www.yammer.com/api/v1/uploaded_files/1749864947712/version/1772802719744/scaled/{{width}}x{{height}}",
                "image": {
                    "url": "https://www.yammer.com/api/v1/uploaded_files/1749864947712/preview/",
                    "size": 140497,
                    "thumbnail_url": "https://www.yammer.com/api/v1/uploaded_files/1749864947712/version/1772802719744/thumbnail",
                },
                "latest_version_id": 1772802719744,
                "status": "not_ams",
                "real_type": "uploaded_file",
            }
        ],
        "additional": "Welcome on board!!!",
        "liked_by": 4,
    },
    {
        "created_at": "2023/07/11 06:38:10 +0000",
        "web_url": "https://www.yammer.com/adorians.com/messages/2350261312708608",
        "message": "Welcome on board!!!",
        "image": [
            {
                "id": 1749863735296,
                "network_id": 5043320,
                "url": "https://www.yammer.com/api/v1/uploaded_files/1749863735296",
                "web_url": "https://www.yammer.com/adorians.com/uploaded_files/1749863735296",
                "type": "image",
                "name": "Joining Announcement - Nitin sharma.jpg",
                "original_name": "Joining Announcement - Nitin sharma.jpg",
                "full_name": "Joining Announcement - Nitin sharma",
                "description": "",
                "content_type": "image/jpeg",
                "content_class": "Image",
                "created_at": "2023/07/11 06:37:25 +0000",
                "owner_id": 2610098839552,
                "official": False,
                "storage_type": "SHAREPOINT",
                "target_type": "GROUP",
                "storage_state": False,
                "sharepoint_id": "01XSUWBKECXUIDQSZI5BEKPB3JRTFKOFKS",
                "sharepoint_web_url": "https://adorians.sharepoint.com/sites/allcompany/Shared%20Documents/Apps/Viva%20Engage/Joining%20Announcement%20-%20Nitin%20sharma.jpg",
                "small_icon_url": "https://s0-azure.assets-yammer.com/assets/images/file_icons/types/picture_orange_39x50_icon.png",
                "large_icon_url": "https://s0-azure.assets-yammer.com/assets/images/file_icons/types/picture_orange_79x102_icon.png",
                "download_url": "https://www.yammer.com/api/v1/uploaded_files/1749863735296/download",
                "thumbnail_url": "https://www.yammer.com/api/v1/uploaded_files/1749863735296/version/1772801499136/thumbnail",
                "preview_url": "https://www.yammer.com/api/v1/uploaded_files/1749863735296/preview/",
                "large_preview_url": "https://www.yammer.com/api/v1/uploaded_files/1749863735296/version/1772801499136/large_preview/",
                "size": 146791,
                "owner_type": "user",
                "last_uploaded_at": "2023/07/11 06:37:25 +0000",
                "last_uploaded_by_id": 2610098839552,
                "last_uploaded_by_type": "user",
                "uuid": False,
                "transcoded": False,
                "streaming_url": False,
                "path": "5043320/1749863735296/Joining Announcement - Nitin sharma.jpg",
                "y_id": 1749863735296,
                "overlay_url": "https://www.yammer.com/api/v1/uploaded_files/1749863735296/version/1772801499136/preview/",
                "privacy": "public",
                "group_id": 45776887808,
                "height": 1152,
                "width": 1152,
                "scaled_url": "https://www.yammer.com/api/v1/uploaded_files/1749863735296/version/1772801499136/scaled/{{width}}x{{height}}",
                "image": {
                    "url": "https://www.yammer.com/api/v1/uploaded_files/1749863735296/preview/",
                    "size": 146791,
                    "thumbnail_url": "https://www.yammer.com/api/v1/uploaded_files/1749863735296/version/1772801499136/thumbnail",
                },
                "latest_version_id": 1772801499136,
                "status": "not_ams",
                "real_type": "uploaded_file",
            }
        ],
        "additional": "Welcome on board!!!",
        "liked_by": 3,
    },
    {
        "created_at": "2023/07/11 04:19:30 +0000",
        "web_url": "https://www.yammer.com/adorians.com/messages/2350121724035072",
        "message": "Welcome on board!!!",
        "image": [
            {
                "id": 1749766873088,
                "network_id": 5043320,
                "url": "https://www.yammer.com/api/v1/uploaded_files/1749766873088",
                "web_url": "https://www.yammer.com/adorians.com/uploaded_files/1749766873088",
                "type": "image",
                "name": "Joining Announcement.jpg",
                "original_name": "Joining Announcement.jpg",
                "full_name": "Joining Announcement",
                "description": "",
                "content_type": "image/jpeg",
                "content_class": "Image",
                "created_at": "2023/07/11 04:18:04 +0000",
                "owner_id": 738066022400,
                "official": False,
                "storage_type": "SHAREPOINT",
                "target_type": "GROUP",
                "storage_state": False,
                "sharepoint_id": "01XSUWBKEP3FQQ6WA4SZFKPQWGX5WAR6GF",
                "sharepoint_web_url": "https://adorians.sharepoint.com/sites/allcompany/Shared%20Documents/Apps/Viva%20Engage/Joining%20Announcement.jpg",
                "small_icon_url": "https://s0-azure.assets-yammer.com/assets/images/file_icons/types/picture_orange_39x50_icon.png",
                "large_icon_url": "https://s0-azure.assets-yammer.com/assets/images/file_icons/types/picture_orange_79x102_icon.png",
                "download_url": "https://www.yammer.com/api/v1/uploaded_files/1749766873088/download",
                "thumbnail_url": "https://www.yammer.com/api/v1/uploaded_files/1749766873088/version/1772704129024/thumbnail",
                "preview_url": "https://www.yammer.com/api/v1/uploaded_files/1749766873088/preview/",
                "large_preview_url": "https://www.yammer.com/api/v1/uploaded_files/1749766873088/version/1772704129024/large_preview/",
                "size": 146167,
                "owner_type": "user",
                "last_uploaded_at": "2023/07/11 04:18:04 +0000",
                "last_uploaded_by_id": 738066022400,
                "last_uploaded_by_type": "user",
                "uuid": False,
                "transcoded": False,
                "streaming_url": False,
                "path": "5043320/1749766873088/Joining Announcement.jpg",
                "y_id": 1749766873088,
                "overlay_url": "https://www.yammer.com/api/v1/uploaded_files/1749766873088/version/1772704129024/preview/",
                "privacy": "public",
                "group_id": 45776887808,
                "height": 1152,
                "width": 1152,
                "scaled_url": "https://www.yammer.com/api/v1/uploaded_files/1749766873088/version/1772704129024/scaled/{{width}}x{{height}}",
                "image": {
                    "url": "https://www.yammer.com/api/v1/uploaded_files/1749766873088/preview/",
                    "size": 146167,
                    "thumbnail_url": "https://www.yammer.com/api/v1/uploaded_files/1749766873088/version/1772704129024/thumbnail",
                },
                "latest_version_id": 1772704129024,
                "status": "not_ams",
                "real_type": "uploaded_file",
            }
        ],
        "additional": "Welcome on board!!!",
        "liked_by": 2,
    },
]


@api_view(["GET"])
def get_api(request):
    if False:
        access_token = "5043320-RQeyfQ9dC5tQQ2omUJGw"
        arr = []
        url = "https://www.yammer.com/api/v1/messages.json"
        params = {"limit": 5}
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(url, params=params, headers=headers)
        for item in response.json()["messages"]:
            arr.append(
                {
                    "created_at": item["created_at"],
                    "web_url": item["web_url"],
                    "message": item["body"]["plain"],
                    "image": item["attachments"],
                    "additional": item["content_excerpt"],
                    "liked_by": item["liked_by"]["count"],
                }
            )
    # return Response(arr)
    return Response(yammer_data)

    # if response.status_code == 200:
    #     feeds = response.json()["messages"]

    #     for feed in feeds:
    #         print(feed["body"]["plain"])
    # else:
    #     print(f"Error: {response.status_code}")
