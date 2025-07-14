from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json
from main.utils.logger import log_trigger

from main.apps.metadata_mgt.services.TextController import TextController

class TextManager:
    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def create_text_metadata(request):
        """
        Input (POST JSON):
            conversation_uid (必填)

        Output (JsonResponse)
        """
        try:
            payload = json.loads(request.body)

            # 必填欄位檢查
            required_fields = ["conversation_uid"]
            missing_fields = [f for f in required_fields if f not in payload]
            if missing_fields:
                return JsonResponse({
                    "status_code": 400,
                    "message": f"缺少必填欄位: {', '.join(missing_fields)}"
                }, status=400)

            # 呼叫 Controller 建立
            response = TextController.create_text(payload["conversation_uid"])

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
    def get_text_metadata(request):
        """
        Input (POST JSON):
            text_uid (必填)

        Output (JsonResponse)
        """
        try:
            payload = json.loads(request.body)

            # 必填欄位檢查
            required_fields = ["text_uid"]
            missing_fields = [f for f in required_fields if f not in payload]
            if missing_fields:
                return JsonResponse({
                    "status_code": 400,
                    "message": f"缺少必填欄位: {', '.join(missing_fields)}"
                }, status=400)

            # 呼叫 Controller 查詢
            response = TextController.get_text_metadata_by_uid(payload["text_uid"])

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

    @log_trigger()
    def get_text_metadata_list(request):
        """
        Input (POST JSON):
            conversation_uid (必填)

        Output (JsonResponse)
        """
        try:
            payload = json.loads(request.body)

            # 必填欄位檢查
            required_fields = ["conversation_uid"]
            missing_fields = [f for f in required_fields if f not in payload]
            if missing_fields:
                return JsonResponse({
                    "status_code": 400,
                    "message": f"缺少必填欄位: {', '.join(missing_fields)}"
                }, status=400)

            # 呼叫 Controller 查詢
            response = TextController.get_text_list_by_conversation(payload["conversation_uid"])

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
        
    @log_trigger()
    def delete_text_metadata(request):
        """
        Input (POST JSON):
            text_uid (必填)

        Output (JsonResponse)
        """
        try:
            payload = json.loads(request.body)

            # 必填欄位檢查
            required_fields = ["text_uid"]
            missing_fields = [f for f in required_fields if f not in payload]
            if missing_fields:
                return JsonResponse({
                    "status_code": 400,
                    "message": f"缺少必填欄位: {', '.join(missing_fields)}"
                }, status=400)
            
            # 呼叫 Controller 刪除
            response = TextController.delete_text_by_uid(payload["text_uid"])

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