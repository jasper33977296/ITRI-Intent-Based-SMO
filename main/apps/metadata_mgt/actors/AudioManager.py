from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json
from main.utils.logger import log_trigger
from main.apps.metadata_mgt.services.AudioController import AudioController

class AudioManager:

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def create_audio_metadata(request):
        try:
            payload = json.loads(request.body)

            required_fields = ["conversation_uid"]
            missing_fields = [f for f in required_fields if f not in payload]
            if missing_fields:
                return JsonResponse({
                    "status_code": 400,
                    "message": f"缺少必填欄位: {', '.join(missing_fields)}"
                }, status=400)

            response = AudioController.create_audio(payload["conversation_uid"])
            return JsonResponse(response, status=response["status_code"])

        except json.JSONDecodeError:
            return JsonResponse({
                "status_code": 400,
                "message": "無效的 JSON 格式"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "message": f"系統發生錯誤，請稍後再試: {str(e)}"
            }, status=500)

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def get_audio_metadata(request):
        try:
            payload = json.loads(request.body)

            required_fields = ["audio_uid"]
            missing_fields = [f for f in required_fields if f not in payload]
            if missing_fields:
                return JsonResponse({
                    "status_code": 400,
                    "message": f"缺少必填欄位: {', '.join(missing_fields)}"
                }, status=400)

            response = AudioController.get_audio_metadata_by_uid(payload["audio_uid"])
            return JsonResponse(response, status=response["status_code"])

        except json.JSONDecodeError:
            return JsonResponse({
                "status_code": 400,
                "message": "無效的 JSON 格式"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "message": f"系統發生錯誤，請稍後再試: {str(e)}"
            }, status=500)

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def get_audio_metadata_list(request):
        try:
            payload = json.loads(request.body)

            required_fields = ["conversation_uid"]
            missing_fields = [f for f in required_fields if f not in payload]
            if missing_fields:
                return JsonResponse({
                    "status_code": 400,
                    "message": f"缺少必填欄位: {', '.join(missing_fields)}"
                }, status=400)

            response = AudioController.get_audio_list_by_conversation(payload["conversation_uid"])
            return JsonResponse(response, status=response["status_code"])

        except json.JSONDecodeError:
            return JsonResponse({
                "status_code": 400,
                "message": "無效的 JSON 格式"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "message": f"系統發生錯誤，請稍後再試: {str(e)}"
            }, status=500)

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def delete_audio_metadata(request):
        try:
            payload = json.loads(request.body)

            required_fields = ["audio_uid"]
            missing_fields = [f for f in required_fields if f not in payload]
            if missing_fields:
                return JsonResponse({
                    "status_code": 400,
                    "message": f"缺少必填欄位: {', '.join(missing_fields)}"
                }, status=400)

            response = AudioController.delete_audio_by_uid(payload["audio_uid"])
            return JsonResponse(response, status=response["status_code"])

        except json.JSONDecodeError:
            return JsonResponse({
                "status_code": 400,
                "message": "無效的 JSON 格式"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "message": f"系統發生錯誤，請稍後再試: {str(e)}"
            }, status=500)
