from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from main.utils.logger import log_trigger, log_writer
from main.apps.metadata_mgt.services.ConversationController import ConversationController
import json

class ConversationManager():
    """
    提供對 Conversation (DB table: conversation) 進行 
    Create / Read / Update / Delete 的方法，
    但不直接執行邏輯，改呼叫 ConversationController。
    """

    @csrf_exempt
    @log_trigger("INFO")
    @require_http_methods(["POST"])
    def create_conversation_metadata(request):
        """
        Input (POST JSON):
            f_user_uid (必填)
            conversation_name (選填)

        Output (JsonResponse):
            - conversation_path 不需前端傳入，會在後端自動組合
        """
        try:
            payload = json.loads(request.body)

            # 必填欄位檢查
            required_fields = ["user_uid","conversation_name"]
            missing_fields = [f for f in required_fields if f not in payload]
            if missing_fields:
                return JsonResponse({
                    "status_code": 400,
                    "status": False,
                    "message": f"缺少必填欄位: {', '.join(missing_fields)}"
                }, status=400)

            # 呼叫 Controller 建立
            response = ConversationController.create_conversation(
                f_user_uid=payload.get("user_uid"),
                conversation_name=payload.get("conversation_name"),
            )

            return JsonResponse(response, status=response["status_code"])

        except json.JSONDecodeError:
            return JsonResponse({
                "status_code": 400,
                "status": False,
                "message": "無效的 JSON 格式"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "status": False,
                "message": f"系統發生錯誤，請稍後再試: {str(e)}"
            }, status=500)

    @csrf_exempt
    @log_trigger("INFO")
    @require_http_methods(["POST"])
    def get_user_conversation_list(request):
        """
        Input (POST JSON):
            user_uid (必填)

        Output (JsonResponse)
        """
        try:
            payload = json.loads(request.body)
            if "user_uid" not in payload:
                return JsonResponse({
                    "status_code": 400,
                    "status": False,
                    "message": "缺少 user_uid"
                }, status=400)

            # 呼叫 Controller 查詢
            response = ConversationController.get_user_conversation_metadata_list(payload["user_uid"])

            return JsonResponse(response, status=response["status_code"])
        except json.JSONDecodeError:
            return JsonResponse({
                "status_code": 400,
                "status": False,
                "message": "無效的 JSON 格式"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "status": False,
                "message": f"系統發生錯誤，請稍後再試: {str(e)}"
            }, status=500)

    @csrf_exempt
    @log_trigger("INFO")
    @require_http_methods(["POST"])
    def get_conversation(request):
        """
        Input (POST JSON):
            conversation_uid (必填)

        Output (JsonResponse)
        """
        try:
            payload = json.loads(request.body)
            if "conversation_uid" not in payload:
                return JsonResponse({
                    "status_code": 400,
                    "status": False,
                    "message": "缺少 conversation_uid"
                }, status=400)

            response = ConversationController.get_conversation(payload["conversation_uid"])

            return JsonResponse(response, status=response["status_code"])
        except json.JSONDecodeError:
            return JsonResponse({
                "status_code": 400,
                "status": False,
                "message": "無效的 JSON 格式"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "status": False,
                "message": f"系統發生錯誤，請稍後再試: {str(e)}"
            }, status=500)

    @csrf_exempt
    @log_trigger("INFO")
    @require_http_methods(["POST"])
    def update_conversation_name(request):
        """
        Input (POST JSON):
            {
                "conversation_uid": <string>,
                "conversation_name": <string>
            }

        Output (JsonResponse):
            {
                "status": <bool>,
                "message": <string>
            }
        """
        try:
            payload = json.loads(request.body)

            # 檢查必填欄位
            if "conversation_uid" not in payload or "conversation_name" not in payload:
                return JsonResponse({
                    "status": False,
                    "message": "缺少必填欄位: conversation_uid, conversation_name"
                }, status=400)

            # 呼叫 Controller
            response = ConversationController.update_conversation_name(
                conversation_uid=payload["conversation_uid"],
                conversation_name=payload["conversation_name"]
            )

            # 從 Controller 回傳的資料只取 status、message 即可
            return JsonResponse({
                "status": response["status"],
                "message": response["message"]
            }, status=response["status_code"])

        except json.JSONDecodeError:
            return JsonResponse({
                "status": False,
                "message": "無效的 JSON 格式"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"系統發生錯誤，請稍後再試: {str(e)}"
            }, status=500)

    @csrf_exempt
    @log_trigger("INFO")
    @require_http_methods(["POST"])
    def delete_conversation(request):
        """
        Input (POST JSON):
            conversation_uid (必填)

        Output (JsonResponse)
        """
        try:
            payload = json.loads(request.body)
            if "conversation_uid" not in payload:
                return JsonResponse({
                    "status_code": 400,
                    "status": False,
                    "message": "缺少 conversation_uid"
                }, status=400)

            response = ConversationController.delete_conversation(payload["conversation_uid"])

            return JsonResponse(response, status=response["status_code"])
        except json.JSONDecodeError:
            return JsonResponse({
                "status_code": 400,
                "status": False,
                "message": "無效的 JSON 格式"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "status": False,
                "message": f"系統發生錯誤，請稍後再試: {str(e)}"
            }, status=500)