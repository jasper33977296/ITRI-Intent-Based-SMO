from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from main.utils.logger import log_trigger
from main.apps.metadata_mgt.services.ConversationController import ConversationController
import json

class ConversationManager():
    """
    提供對 Conversation (DB table: conversation) 進行 
    Create / Read / Update / Delete 的方法，
    但不直接執行邏輯，改呼叫 ConversationController。
    """

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def create_conversation_metadata(request):
        """
        Input (POST JSON):
            user_uid (必填)
            conversation_name (必填)
            agent_uid (必填)
        Output (JsonResponse)
        """
        try:
            payload = json.loads(request.body)
            required_fields = ["user_uid", "conversation_name", "agent_uid"]
            missing_fields = [f for f in required_fields if f not in payload]
            if missing_fields:
                return JsonResponse({
                    "status_code": 400,
                    "message": f"缺少必填欄位: {', '.join(missing_fields)}"
                }, status=400)
            response = ConversationController.create_conversation(
                f_user_uid=payload.get("user_uid"),
                conversation_name=payload.get("conversation_name"),
                f_agent_uid=payload.get("agent_uid")
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
                "message": f"系統發生錯誤，請稍後再試: {str(e)}"
            }, status=500)

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def get_conversation_metadata_list(request):
        """
        Input (POST JSON):
            user_uid (必填)
            agent_uid (選填)
        Output (JsonResponse)
        """
        try:
            payload = json.loads(request.body)
            required_fields = ["user_uid"]
            missing_fields = [f for f in required_fields if f not in payload]
            if missing_fields:
                return JsonResponse({
                    "status_code": 400,
                    "message": f"缺少必填欄位: {', '.join(missing_fields)}"
                }, status=400)
            response = ConversationController.get_user_conversation_metadata_list(
                user_uid=payload["user_uid"],
                agent_uid=payload.get("agent_uid")
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
                "message": f"系統發生錯誤，請稍後再試: {str(e)}"
            }, status=500)

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def get_conversation_metadata(request):
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
            response = ConversationController.get_conversation(payload["conversation_uid"])

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
    def update_conversation_name(request):
        """
        Input (POST JSON):
            conversation_uid (必填)
            conversation_name (必填)

        Output (JsonResponse)
        """
        try:
            payload = json.loads(request.body)

            # 必填欄位檢查
            required_fields = ["conversation_uid", "conversation_name"]
            missing_fields = [f for f in required_fields if f not in payload]
            if missing_fields:
                return JsonResponse({
                    "status_code": 400,
                    "message": f"缺少必填欄位: {', '.join(missing_fields)}"
                }, status=400)

            # 呼叫 Controller 更新
            response = ConversationController.update_conversation_name(
                conversation_uid=payload["conversation_uid"],
                conversation_name=payload["conversation_name"]
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
                "message": f"系統發生錯誤，請稍後再試: {str(e)}"
            }, status=500)

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def delete_conversation_metadata(request):
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

            # 呼叫 Controller 刪除
            response = ConversationController.delete_conversation(payload["conversation_uid"])

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
    def verify_conversation_exist(request):
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
            response = ConversationController.get_conversation(conversation_uid=payload["conversation_uid"])

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
