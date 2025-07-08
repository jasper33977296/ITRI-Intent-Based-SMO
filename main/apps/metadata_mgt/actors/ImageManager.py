from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json
from main.utils.logger import log_trigger
from main.apps.metadata_mgt.services.ImageController import ImageController

class ImageManager:

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def create_image_metadata(request):
        try:
            payload = json.loads(request.body)
            if "conversation_uid" not in payload:
                return JsonResponse({
                    "status_code": 400,
                    "message": "缺少欄位: conversation_uid"
                }, status=400)

            response = ImageController.create_image(
                conversation_uid=payload["conversation_uid"]
            )
            return JsonResponse(response, status=response["status_code"])

        except json.JSONDecodeError:
            return JsonResponse({
                "status_code": 400,
                "message": "無效的 JSON 格式"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "message": f"系統錯誤: {str(e)}"
            }, status=500)

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def get_image_metadata(request):
        try:
            payload = json.loads(request.body)
            if "image_uid" not in payload:
                return JsonResponse({
                    "status_code": 400,
                    "message": "缺少欄位: image_uid"
                }, status=400)

            response = ImageController.get_image_metadata_by_uid(payload["image_uid"])
            return JsonResponse(response, status=response["status_code"])

        except json.JSONDecodeError:
            return JsonResponse({
                "status_code": 400,
                "message": "無效的 JSON 格式"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "message": f"系統錯誤: {str(e)}"
            }, status=500)

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def get_image_metadata_list(request):
        try:
            payload = json.loads(request.body)
            if "conversation_uid" not in payload:
                return JsonResponse({
                    "status_code": 400,
                    "message": "缺少欄位: conversation_uid"
                }, status=400)

            response = ImageController.get_image_list_by_conversation(payload["conversation_uid"])
            return JsonResponse(response, status=response["status_code"])

        except json.JSONDecodeError:
            return JsonResponse({
                "status_code": 400,
                "message": "無效的 JSON 格式"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "message": f"系統錯誤: {str(e)}"
            }, status=500)

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def delete_image_metadata(request):
        try:
            payload = json.loads(request.body)
            if "image_uid" not in payload:
                return JsonResponse({
                    "status_code": 400,
                    "message": "缺少欄位: image_uid"
                }, status=400)

            response = ImageController.delete_image_by_uid(payload["image_uid"])
            return JsonResponse(response, status=response["status_code"])

        except json.JSONDecodeError:
            return JsonResponse({
                "status_code": 400,
                "message": "無效的 JSON 格式"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "message": f"系統錯誤: {str(e)}"
            }, status=500)
